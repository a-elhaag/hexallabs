"""Tests for Workflow mode executor.

Covers:
  - Single-node workflow (one model) emits session → hex_start → token → hex_done → done
  - Two-node sequential workflow: node_1 output feeds node_2 as input
  - Cycle detection emits error + done, no crash
  - Empty workflow_nodes returns 422 from API
  - Unknown model in node emits error event but does not crash pipeline
  - passthrough node passes input unchanged (no SSE events for node)
  - prompt_template node applies template without model call
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api import query as query_module
from app.auth.middleware import get_current_user
from app.auth.models import AuthUser
from app.db.session import get_session
from app.llm.base import Message, StreamChunk
from app.main import app

from .conftest import FakeClient, FakeSession, parse_sse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _setup_workflow_app(
    monkeypatch: pytest.MonkeyPatch,
    model_clients: dict[str, FakeClient] | None = None,
    fake_session: FakeSession | None = None,
) -> TestClient:
    """Wire app with fake clients; return a TestClient."""
    user = AuthUser(id=uuid.uuid4(), email="user@example.com")
    session = fake_session or FakeSession()
    clients = model_clients or {}

    def _get_client(wl: str) -> object:
        if wl in clients:
            return clients[wl]
        raise KeyError(f"Unknown white-label {wl!r}")

    async def _fake_session():  # type: ignore[no-untyped-def]
        yield session

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_session] = _fake_session
    monkeypatch.setattr(query_module, "get_client", _get_client)
    # Also patch get_client inside the executor module
    monkeypatch.setattr("app.workflow.executor.get_client", _get_client)
    return TestClient(app)


# ---------------------------------------------------------------------------
# Test: single-node workflow
# ---------------------------------------------------------------------------


def test_workflow_single_model_node_event_sequence(monkeypatch: pytest.MonkeyPatch) -> None:
    """Single model node emits: session → hex_start → token(s) → hex_done → done."""
    fake_client = FakeClient(["hello ", "world"], whitelabel="Swift", total=20, cached=3)
    nodes = [
        {"id": "n0", "type": "model", "model": "Swift", "inputs": [], "config": {}},
    ]

    tc = _setup_workflow_app(monkeypatch, {"Swift": fake_client})
    try:
        with tc:
            r = tc.post(
                "/api/query",
                json={"mode": "workflow", "query": "test question", "workflow_nodes": nodes},
            )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    events = parse_sse(r.text)
    names = [e for e, _ in events]

    # First event is session
    assert names[0] == "session"
    session_data = events[0][1]
    assert session_data["mode"] == "workflow"
    assert "session_id" in session_data

    # hex_start for Swift
    assert "hex_start" in names
    hex_start_data = next(d for e, d in events if e == "hex_start")
    assert hex_start_data["hex"] == "Swift"

    # token events with correct deltas
    token_events = [(e, d) for e, d in events if e == "token"]
    assert len(token_events) == 2
    deltas = [d["delta"] for _, d in token_events]
    assert deltas == ["hello ", "world"]

    # hex_done with token counts
    assert "hex_done" in names
    hex_done_data = next(d for e, d in events if e == "hex_done")
    assert hex_done_data["hex"] == "Swift"
    assert hex_done_data["tokens"] == 20
    assert hex_done_data["cached_tokens"] == 3

    # done is last
    assert names[-1] == "done"

    # Order: session < hex_start < token < hex_done < done
    assert names.index("session") < names.index("hex_start")
    assert names.index("hex_start") < names.index("token")
    last_token_idx = max(i for i, n in enumerate(names) if n == "token")
    assert last_token_idx < names.index("hex_done")
    assert names.index("hex_done") < names.index("done")


def test_workflow_single_model_db_writes(monkeypatch: pytest.MonkeyPatch) -> None:
    """Model node output is persisted as a MessageRow with stage='workflow'."""
    from app.db.models import Message as MessageRow

    fake_session = FakeSession()
    fake_client = FakeClient(["answer text"], whitelabel="Swift")
    nodes = [
        {"id": "n0", "type": "model", "model": "Swift", "inputs": [], "config": {}},
    ]

    tc = _setup_workflow_app(monkeypatch, {"Swift": fake_client}, fake_session=fake_session)
    try:
        with tc:
            r = tc.post(
                "/api/query",
                json={"mode": "workflow", "query": "question", "workflow_nodes": nodes},
            )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    messages = [o for o in fake_session.added if isinstance(o, MessageRow)]
    workflow_msgs = [m for m in messages if m.stage == "workflow"]
    assert len(workflow_msgs) == 1
    assert workflow_msgs[0].model == "Swift"
    assert workflow_msgs[0].content == "answer text"


# ---------------------------------------------------------------------------
# Test: two-node sequential workflow — output of node_0 feeds node_1
# ---------------------------------------------------------------------------


class _InputCapturingClient:
    """Fake client that records the messages it receives, then returns fixed deltas."""

    def __init__(self, deltas: list[str], whitelabel: str = "Prism") -> None:
        self.whitelabel = whitelabel
        self._deltas = deltas
        self.received_messages: list[list[Message]] = []

    async def stream(
        self,
        messages: list[Message],
        cache_key: str | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[StreamChunk]:
        self.received_messages.append(list(messages))
        for d in self._deltas:
            yield StreamChunk(delta=d)
        yield StreamChunk(delta="", total_tokens=10, cached_tokens=0)


def test_workflow_two_node_sequential_output_fed_as_input(monkeypatch: pytest.MonkeyPatch) -> None:
    """node_1 output is passed as the input to node_2."""
    node0_client = FakeClient(["first node output"], whitelabel="Swift")
    node1_client = _InputCapturingClient(["second node output"], whitelabel="Prism")

    nodes = [
        {"id": "n0", "type": "model", "model": "Swift", "inputs": [], "config": {}},
        {"id": "n1", "type": "model", "model": "Prism", "inputs": ["n0"], "config": {}},
    ]

    tc = _setup_workflow_app(monkeypatch, {"Swift": node0_client, "Prism": node1_client})
    try:
        with tc:
            r = tc.post(
                "/api/query",
                json={"mode": "workflow", "query": "original query", "workflow_nodes": nodes},
            )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    events = parse_sse(r.text)
    names = [e for e, _ in events]

    # Both models should emit hex_start
    hex_starts = [d["hex"] for e, d in events if e == "hex_start"]
    assert "Swift" in hex_starts
    assert "Prism" in hex_starts

    # node_1 (Prism) should have received "first node output" as its user message
    assert len(node1_client.received_messages) == 1
    prism_msg_content = node1_client.received_messages[0][0].content
    assert prism_msg_content == "first node output"

    # done is last
    assert names[-1] == "done"


def test_workflow_two_node_token_events_from_both(monkeypatch: pytest.MonkeyPatch) -> None:
    """token events appear from both nodes in sequence."""
    nodes = [
        {"id": "n0", "type": "model", "model": "Swift", "inputs": [], "config": {}},
        {"id": "n1", "type": "model", "model": "Prism", "inputs": ["n0"], "config": {}},
    ]
    clients = {
        "Swift": FakeClient(["swift ", "out"], whitelabel="Swift"),
        "Prism": FakeClient(["prism ", "out"], whitelabel="Prism"),
    }

    tc = _setup_workflow_app(monkeypatch, clients)
    try:
        with tc:
            r = tc.post(
                "/api/query",
                json={"mode": "workflow", "query": "q", "workflow_nodes": nodes},
            )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    events = parse_sse(r.text)

    token_hexes = [d["hex"] for e, d in events if e == "token"]
    assert "Swift" in token_hexes
    assert "Prism" in token_hexes

    # Swift tokens should appear before Prism tokens (sequential execution)
    swift_indices = [i for i, (e, d) in enumerate(events) if e == "token" and d["hex"] == "Swift"]
    prism_indices = [i for i, (e, d) in enumerate(events) if e == "token" and d["hex"] == "Prism"]
    assert max(swift_indices) < min(prism_indices)


# ---------------------------------------------------------------------------
# Test: cycle detection
# ---------------------------------------------------------------------------


def test_workflow_cycle_detection_emits_error_and_done(monkeypatch: pytest.MonkeyPatch) -> None:
    """A cyclic workflow emits error + done events and does not crash."""
    nodes = [
        {"id": "n0", "type": "model", "model": "Swift", "inputs": ["n1"], "config": {}},
        {"id": "n1", "type": "model", "model": "Prism", "inputs": ["n0"], "config": {}},
    ]

    tc = _setup_workflow_app(monkeypatch, {
        "Swift": FakeClient(["x"], whitelabel="Swift"),
        "Prism": FakeClient(["y"], whitelabel="Prism"),
    })
    try:
        with tc:
            r = tc.post(
                "/api/query",
                json={"mode": "workflow", "query": "q", "workflow_nodes": nodes},
            )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    events = parse_sse(r.text)
    names = [e for e, _ in events]

    assert "error" in names
    error_data = next(d for e, d in events if e == "error")
    assert error_data["code"] == "CycleDetected"

    assert "done" in names
    assert names[-1] == "done"

    # No model tokens should have been emitted
    assert "token" not in names
    assert "hex_start" not in names


# ---------------------------------------------------------------------------
# Test: empty workflow_nodes → 422
# ---------------------------------------------------------------------------


def test_workflow_empty_nodes_returns_422(monkeypatch: pytest.MonkeyPatch) -> None:
    """workflow mode with empty workflow_nodes returns 422."""
    user = AuthUser(id=uuid.uuid4(), email="user@example.com")

    async def _fake_session():  # type: ignore[no-untyped-def]
        yield FakeSession()

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_session] = _fake_session

    try:
        with TestClient(app) as tc:
            r = tc.post(
                "/api/query",
                json={"mode": "workflow", "query": "question", "workflow_nodes": []},
            )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Test: unknown model in node emits error but does not crash pipeline
# ---------------------------------------------------------------------------


def test_workflow_unknown_model_emits_error_continues(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unknown model in a node emits error event; downstream nodes still run."""
    nodes = [
        {"id": "n0", "type": "model", "model": "UnknownModel", "inputs": [], "config": {}},
        {"id": "n1", "type": "model", "model": "Swift", "inputs": ["n0"], "config": {}},
    ]
    clients = {
        "Swift": FakeClient(["fallback output"], whitelabel="Swift"),
        # "UnknownModel" is intentionally absent → KeyError
    }

    tc = _setup_workflow_app(monkeypatch, clients)
    try:
        with tc:
            r = tc.post(
                "/api/query",
                json={"mode": "workflow", "query": "q", "workflow_nodes": nodes},
            )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    events = parse_sse(r.text)
    names = [e for e, _ in events]

    # Error event for the unknown model node
    assert "error" in names
    error_data = next(d for e, d in events if e == "error")
    assert error_data["code"] == "UnknownModel"

    # Pipeline continues: Swift node runs
    assert "hex_start" in names
    swift_hex_start = next(
        (d for e, d in events if e == "hex_start" and d["hex"] == "Swift"), None
    )
    assert swift_hex_start is not None

    # done is last
    assert names[-1] == "done"


def test_workflow_unknown_model_only_node_emits_error_done(monkeypatch: pytest.MonkeyPatch) -> None:
    """Single unknown-model node: emits session → error → done."""
    nodes = [
        {"id": "n0", "type": "model", "model": "Ghost", "inputs": [], "config": {}},
    ]

    tc = _setup_workflow_app(monkeypatch, {})  # no clients registered
    try:
        with tc:
            r = tc.post(
                "/api/query",
                json={"mode": "workflow", "query": "q", "workflow_nodes": nodes},
            )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    events = parse_sse(r.text)
    names = [e for e, _ in events]

    assert names[0] == "session"
    assert "error" in names
    assert names[-1] == "done"
    assert "token" not in names


# ---------------------------------------------------------------------------
# Test: passthrough node
# ---------------------------------------------------------------------------


def test_workflow_passthrough_node_no_sse_but_feeds_downstream(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """passthrough node passes input through; no hex_start/token/hex_done emitted for it."""
    node1_client = _InputCapturingClient(["model out"], whitelabel="Swift")
    nodes = [
        {"id": "p0", "type": "passthrough", "inputs": [], "config": {}},
        {"id": "n1", "type": "model", "model": "Swift", "inputs": ["p0"], "config": {}},
    ]

    tc = _setup_workflow_app(monkeypatch, {"Swift": node1_client})
    try:
        with tc:
            r = tc.post(
                "/api/query",
                json={"mode": "workflow", "query": "original input", "workflow_nodes": nodes},
            )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    events = parse_sse(r.text)

    # Swift model receives the original query (passed through passthrough)
    assert len(node1_client.received_messages) == 1
    assert node1_client.received_messages[0][0].content == "original input"

    # Only one hex_start (from Swift model)
    hex_starts = [d["hex"] for e, d in events if e == "hex_start"]
    assert hex_starts == ["Swift"]


# ---------------------------------------------------------------------------
# Test: prompt_template node
# ---------------------------------------------------------------------------


def test_workflow_prompt_template_applies_template(monkeypatch: pytest.MonkeyPatch) -> None:
    """prompt_template node applies config.template with {input} placeholder."""
    node1_client = _InputCapturingClient(["model out"], whitelabel="Swift")
    nodes = [
        {
            "id": "t0",
            "type": "prompt_template",
            "inputs": [],
            "config": {"template": "Please summarize the following:\n\n{input}"},
        },
        {"id": "n1", "type": "model", "model": "Swift", "inputs": ["t0"], "config": {}},
    ]

    tc = _setup_workflow_app(monkeypatch, {"Swift": node1_client})
    try:
        with tc:
            r = tc.post(
                "/api/query",
                json={"mode": "workflow", "query": "raw query", "workflow_nodes": nodes},
            )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    events = parse_sse(r.text)

    # Swift receives the template-formatted input
    assert len(node1_client.received_messages) == 1
    content = node1_client.received_messages[0][0].content
    assert content == "Please summarize the following:\n\nraw query"

    # No hex_start for prompt_template node
    hex_starts = [d["hex"] for e, d in events if e == "hex_start"]
    assert hex_starts == ["Swift"]

    assert [e for e, _ in events][-1] == "done"


# ---------------------------------------------------------------------------
# Test: unknown node type emits error and continues
# ---------------------------------------------------------------------------


def test_workflow_unknown_node_type_emits_error_continues(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unknown node type emits error; pipeline continues with downstream nodes."""
    node1_client = _InputCapturingClient(["output"], whitelabel="Swift")
    nodes = [
        {"id": "u0", "type": "mystery_type", "inputs": [], "config": {}},
        {"id": "n1", "type": "model", "model": "Swift", "inputs": ["u0"], "config": {}},
    ]

    tc = _setup_workflow_app(monkeypatch, {"Swift": node1_client})
    try:
        with tc:
            r = tc.post(
                "/api/query",
                json={"mode": "workflow", "query": "q", "workflow_nodes": nodes},
            )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    events = parse_sse(r.text)
    names = [e for e, _ in events]

    assert "error" in names
    error_data = next(d for e, d in events if e == "error")
    assert error_data["code"] == "UnknownNodeType"

    # Swift still runs
    assert "hex_start" in names
    assert names[-1] == "done"
