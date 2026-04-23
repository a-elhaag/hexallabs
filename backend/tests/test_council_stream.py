"""Tests for Council mode streaming.

Covers:
  - Phase 1 fan-out: hex_start + token + hex_done emitted for each model
  - confidence events emitted with stage="initial"
  - Phase 2 peer_review events emitted
  - Phase 3 synth_start/synth_done emitted
  - primal=True emits primal event
  - mode=council with <2 models → 422
  - unknown whitelabel → 400
  - DB writes: council_0 MessageRows + PeerReview rows
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


def _make_apex_client(synthesis_deltas: list[str], primal_text: str = "") -> FakeClient:
    """Apex client: yields synthesis tokens, then optionally primal text.

    For the primal pass, synthesize() calls apex_client.stream() a second time.
    We use a stateful client that returns different deltas on each call.
    """
    return _StatefulApexClient(synthesis_deltas=synthesis_deltas, primal_text=primal_text)


class _StatefulApexClient:
    """Fake Apex that yields synth tokens on first call, primal on second."""

    whitelabel = "Apex"

    def __init__(self, synthesis_deltas: list[str], primal_text: str = "") -> None:
        self._synthesis_deltas = synthesis_deltas
        self._primal_text = primal_text
        self._call_count = 0

    async def stream(
        self,
        messages: list[Message],
        cache_key: str | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[StreamChunk]:
        self._call_count += 1
        if self._call_count == 1:
            for d in self._synthesis_deltas:
                yield StreamChunk(delta=d)
            yield StreamChunk(delta="", total_tokens=20, cached_tokens=0)
        else:
            # Primal Protocol second pass
            if self._primal_text:
                yield StreamChunk(delta=self._primal_text)
            yield StreamChunk(delta="", total_tokens=10, cached_tokens=0)


def _setup_council_app(
    monkeypatch: pytest.MonkeyPatch,
    council_clients: dict[str, FakeClient],
    apex_client: object,
    fake_session: FakeSession | None = None,
) -> TestClient:
    """Wire app with fake clients and return a TestClient."""
    user = AuthUser(id=uuid.uuid4(), email="user@example.com")
    session = fake_session or FakeSession()

    def _get_client(wl: str) -> object:
        if wl == "Apex":
            return apex_client
        if wl in council_clients:
            return council_clients[wl]
        raise KeyError(f"Unknown white-label {wl!r}")

    async def _fake_session():  # type: ignore[no-untyped-def]
        yield session

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_session] = _fake_session
    monkeypatch.setattr(query_module, "get_client", _get_client)
    return TestClient(app)


# ---------------------------------------------------------------------------
# Phase 1 fan-out tests
# ---------------------------------------------------------------------------


def test_council_hex_start_emitted_for_each_model(monkeypatch: pytest.MonkeyPatch) -> None:
    """hex_start event emitted for each model in the council."""
    clients = {
        "Swift": FakeClient(["swift answer [[CONF:8]]"], whitelabel="Swift"),
        "Prism": FakeClient(["prism answer [[CONF:7]]"], whitelabel="Prism"),
    }
    apex = _make_apex_client(["synthesis result"])

    tc = _setup_council_app(monkeypatch, clients, apex)
    try:
        with tc:
            r = tc.post(
                "/api/query",
                json={"mode": "council", "query": "test question", "models": ["Swift", "Prism"]},
            )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    events = parse_sse(r.text)
    names = [e for e, _ in events]

    hex_starts = [(e, d) for e, d in events if e == "hex_start"]
    hex_labels = {d["hex"] for _, d in hex_starts}
    assert hex_labels == {"Swift", "Prism"}


def test_council_token_events_emitted_per_model(monkeypatch: pytest.MonkeyPatch) -> None:
    """token events are emitted with correct hex fields for each model."""
    clients = {
        "Swift": FakeClient(["hello ", "world [[CONF:9]]"], whitelabel="Swift"),
        "Prism": FakeClient(["prism ", "answer [[CONF:6]]"], whitelabel="Prism"),
    }
    apex = _make_apex_client(["final synthesis"])

    tc = _setup_council_app(monkeypatch, clients, apex)
    try:
        with tc:
            r = tc.post(
                "/api/query",
                json={"mode": "council", "query": "question", "models": ["Swift", "Prism"]},
            )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    events = parse_sse(r.text)

    token_hexes = {d["hex"] for e, d in events if e == "token"}
    assert "Swift" in token_hexes
    assert "Prism" in token_hexes


def test_council_hex_done_emitted_per_model(monkeypatch: pytest.MonkeyPatch) -> None:
    """hex_done event emitted for each model with correct token counts."""
    clients = {
        "Swift": FakeClient(["swift [[CONF:8]]"], whitelabel="Swift", total=50, cached=5),
        "Depth": FakeClient(["depth [[CONF:7]]"], whitelabel="Depth", total=60, cached=10),
    }
    apex = _make_apex_client(["synthesis"])

    tc = _setup_council_app(monkeypatch, clients, apex)
    try:
        with tc:
            r = tc.post(
                "/api/query",
                json={"mode": "council", "query": "question", "models": ["Swift", "Depth"]},
            )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    events = parse_sse(r.text)

    hex_dones = {d["hex"]: d for e, d in events if e == "hex_done"}
    assert "Swift" in hex_dones
    assert "Depth" in hex_dones
    assert hex_dones["Swift"]["tokens"] == 50
    assert hex_dones["Depth"]["tokens"] == 60


def test_council_initial_confidence_events(monkeypatch: pytest.MonkeyPatch) -> None:
    """confidence events emitted with stage='initial' after Phase 1."""
    clients = {
        "Swift": FakeClient(["answer [[CONF:8]]"], whitelabel="Swift"),
        "Prism": FakeClient(["answer [[CONF:6]]"], whitelabel="Prism"),
    }
    apex = _make_apex_client(["synthesis"])

    tc = _setup_council_app(monkeypatch, clients, apex)
    try:
        with tc:
            r = tc.post(
                "/api/query",
                json={"mode": "council", "query": "question", "models": ["Swift", "Prism"]},
            )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    events = parse_sse(r.text)

    initial_confs = [(e, d) for e, d in events if e == "confidence" and d.get("stage") == "initial"]
    conf_hexes = {d["hex"] for _, d in initial_confs}
    assert conf_hexes == {"Swift", "Prism"}

    # Scores should match the [[CONF:N]] sentinels
    swift_conf = next(d["score"] for _, d in initial_confs if d["hex"] == "Swift")
    prism_conf = next(d["score"] for _, d in initial_confs if d["hex"] == "Prism")
    assert swift_conf == 8
    assert prism_conf == 6


def test_council_confidence_default_when_no_sentinel(monkeypatch: pytest.MonkeyPatch) -> None:
    """When model emits no [[CONF:N]], default confidence (5) is used."""
    clients = {
        "Swift": FakeClient(["answer without sentinel"], whitelabel="Swift"),
        "Prism": FakeClient(["another answer"], whitelabel="Prism"),
    }
    apex = _make_apex_client(["synthesis"])

    tc = _setup_council_app(monkeypatch, clients, apex)
    try:
        with tc:
            r = tc.post(
                "/api/query",
                json={"mode": "council", "query": "question", "models": ["Swift", "Prism"]},
            )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    events = parse_sse(r.text)

    initial_confs = {d["hex"]: d["score"] for e, d in events if e == "confidence" and d.get("stage") == "initial"}
    assert initial_confs["Swift"] == 5
    assert initial_confs["Prism"] == 5


# ---------------------------------------------------------------------------
# Phase 2 peer review tests
# ---------------------------------------------------------------------------


def test_council_peer_review_events_emitted(monkeypatch: pytest.MonkeyPatch) -> None:
    """peer_review events emitted after Phase 1 completes."""
    # Peer review clients return a critique (second stream call from each client)
    clients = {
        "Swift": _MultiCallClient(
            call_responses=[
                ["swift answer [[CONF:8]]"],     # Phase 1
                ["good point by Prism [[CONF:8]]"],  # Phase 2 review
            ],
            whitelabel="Swift",
        ),
        "Prism": _MultiCallClient(
            call_responses=[
                ["prism answer [[CONF:7]]"],     # Phase 1
                ["swift has good coverage [[CONF:7]]"],  # Phase 2 review
            ],
            whitelabel="Prism",
        ),
    }
    apex = _make_apex_client(["synthesis"])

    tc = _setup_council_app(monkeypatch, clients, apex)
    try:
        with tc:
            r = tc.post(
                "/api/query",
                json={"mode": "council", "query": "question", "models": ["Swift", "Prism"]},
            )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    events = parse_sse(r.text)

    peer_review_events = [(e, d) for e, d in events if e == "peer_review"]
    # 2 models × 1 target each = 2 peer_review events minimum
    assert len(peer_review_events) >= 2

    # Events use white-label names (hexal-whitelabel-names)
    from_values = {d["from"] for _, d in peer_review_events}
    to_values = {d["to"] for _, d in peer_review_events}
    assert from_values <= {"Swift", "Prism"}
    assert to_values <= {"Swift", "Prism"}


def test_council_peer_review_confidence_updated(monkeypatch: pytest.MonkeyPatch) -> None:
    """If peer review includes [[CONF:N]], post_review confidence event is emitted."""
    clients = {
        "Swift": _MultiCallClient(
            call_responses=[
                ["swift answer [[CONF:8]]"],
                ["after review, updating [[CONF:9]]"],  # confidence updated
            ],
            whitelabel="Swift",
        ),
        "Prism": _MultiCallClient(
            call_responses=[
                ["prism answer [[CONF:7]]"],
                ["no change needed"],  # no [[CONF:N]] — unchanged
            ],
            whitelabel="Prism",
        ),
    }
    apex = _make_apex_client(["synthesis"])

    tc = _setup_council_app(monkeypatch, clients, apex)
    try:
        with tc:
            r = tc.post(
                "/api/query",
                json={"mode": "council", "query": "question", "models": ["Swift", "Prism"]},
            )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    events = parse_sse(r.text)

    post_review = [(e, d) for e, d in events if e == "confidence" and d.get("stage") == "post_review"]
    # Swift updated confidence → should have a post_review event
    swift_post = [d for _, d in post_review if d["hex"] == "Swift"]
    assert len(swift_post) >= 1
    assert swift_post[0]["score"] == 9

    # Prism did not update → no post_review confidence event for Prism
    prism_post = [d for _, d in post_review if d["hex"] == "Prism"]
    assert len(prism_post) == 0


# ---------------------------------------------------------------------------
# Phase 3 synthesis tests
# ---------------------------------------------------------------------------


def test_council_synth_start_and_done_emitted(monkeypatch: pytest.MonkeyPatch) -> None:
    """synth_start and synth_done emitted during Apex synthesis."""
    clients = {
        "Swift": FakeClient(["answer [[CONF:8]]"], whitelabel="Swift"),
        "Prism": FakeClient(["answer [[CONF:7]]"], whitelabel="Prism"),
    }
    apex = _make_apex_client(["synthesis token1 ", "token2"])

    tc = _setup_council_app(monkeypatch, clients, apex)
    try:
        with tc:
            r = tc.post(
                "/api/query",
                json={"mode": "council", "query": "question", "models": ["Swift", "Prism"]},
            )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    events = parse_sse(r.text)
    names = [e for e, _ in events]

    assert "synth_start" in names
    assert "synth_done" in names
    assert "synth_token" in names

    # Order: synth_start before synth_done
    assert names.index("synth_start") < names.index("synth_done")


def test_council_done_event_at_end(monkeypatch: pytest.MonkeyPatch) -> None:
    """done event is the last event in the stream."""
    clients = {
        "Swift": FakeClient(["answer [[CONF:8]]"], whitelabel="Swift"),
        "Prism": FakeClient(["answer [[CONF:7]]"], whitelabel="Prism"),
    }
    apex = _make_apex_client(["synthesis"])

    tc = _setup_council_app(monkeypatch, clients, apex)
    try:
        with tc:
            r = tc.post(
                "/api/query",
                json={"mode": "council", "query": "question", "models": ["Swift", "Prism"]},
            )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    events = parse_sse(r.text)
    assert events[-1][0] == "done"


def test_council_primal_event_emitted(monkeypatch: pytest.MonkeyPatch) -> None:
    """primal event emitted when primal_protocol=True."""
    clients = {
        "Swift": FakeClient(["swift answer [[CONF:8]]"], whitelabel="Swift"),
        "Prism": FakeClient(["prism answer [[CONF:7]]"], whitelabel="Prism"),
    }
    apex = _make_apex_client(["synthesis"], primal_text="ME SMART. ANSWER GOOD.")

    tc = _setup_council_app(monkeypatch, clients, apex)
    try:
        with tc:
            r = tc.post(
                "/api/query",
                json={
                    "mode": "council",
                    "query": "question",
                    "models": ["Swift", "Prism"],
                    "primal_protocol": True,
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    events = parse_sse(r.text)
    names = [e for e, _ in events]

    assert "primal" in names
    primal_data = next(d for e, d in events if e == "primal")
    assert "ME SMART" in primal_data["text"]


def test_council_primal_not_emitted_when_off(monkeypatch: pytest.MonkeyPatch) -> None:
    """primal event NOT emitted when primal_protocol=False (default)."""
    clients = {
        "Swift": FakeClient(["answer [[CONF:8]]"], whitelabel="Swift"),
        "Prism": FakeClient(["answer [[CONF:7]]"], whitelabel="Prism"),
    }
    apex = _make_apex_client(["synthesis"], primal_text="CAVEMAN TEXT")

    tc = _setup_council_app(monkeypatch, clients, apex)
    try:
        with tc:
            r = tc.post(
                "/api/query",
                json={"mode": "council", "query": "question", "models": ["Swift", "Prism"]},
            )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    events = parse_sse(r.text)
    names = [e for e, _ in events]
    assert "primal" not in names


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------


def test_council_requires_at_least_2_models(monkeypatch: pytest.MonkeyPatch) -> None:
    """council mode with <2 models → 422 Unprocessable Entity."""
    user = AuthUser(id=uuid.uuid4(), email="user@example.com")

    async def _fake_session():  # type: ignore[no-untyped-def]
        yield FakeSession()

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_session] = _fake_session
    monkeypatch.setattr(query_module, "get_client", lambda _wl: FakeClient([]))

    try:
        with TestClient(app) as tc:
            r0 = tc.post(
                "/api/query",
                json={"mode": "council", "query": "test", "models": []},
            )
            r1 = tc.post(
                "/api/query",
                json={"mode": "council", "query": "test", "models": ["Swift"]},
            )
    finally:
        app.dependency_overrides.clear()

    assert r0.status_code == 422
    assert r1.status_code == 422


def test_council_unknown_whitelabel_returns_400(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unknown whitelabel in models → 400."""
    user = AuthUser(id=uuid.uuid4(), email="user@example.com")

    async def _fake_session():  # type: ignore[no-untyped-def]
        yield FakeSession()

    def _raise(wl: str) -> object:
        raise KeyError(f"Unknown {wl!r}")

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_session] = _fake_session
    monkeypatch.setattr(query_module, "get_client", _raise)

    try:
        with TestClient(app) as tc:
            r = tc.post(
                "/api/query",
                json={"mode": "council", "query": "test", "models": ["Unknown1", "Unknown2"]},
            )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 400


# ---------------------------------------------------------------------------
# DB persistence tests
# ---------------------------------------------------------------------------


def test_council_db_writes_council_0_messages(monkeypatch: pytest.MonkeyPatch) -> None:
    """Two council_0 MessageRows are persisted after Phase 1."""
    from app.db.models import Message as MessageRow

    fake_session = FakeSession()
    clients = {
        "Swift": FakeClient(["swift [[CONF:8]]"], whitelabel="Swift"),
        "Prism": FakeClient(["prism [[CONF:7]]"], whitelabel="Prism"),
    }
    apex = _make_apex_client(["synthesis"])

    tc = _setup_council_app(monkeypatch, clients, apex, fake_session=fake_session)
    try:
        with tc:
            r = tc.post(
                "/api/query",
                json={"mode": "council", "query": "question", "models": ["Swift", "Prism"]},
            )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    messages = [o for o in fake_session.added if isinstance(o, MessageRow)]
    council_0 = [m for m in messages if m.stage == "council_0"]
    assert len(council_0) == 2

    models_persisted = {m.model for m in council_0}
    assert models_persisted == {"Swift", "Prism"}


def test_council_db_writes_peer_review_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    """PeerReview rows persisted: reviewer × target combinations."""
    from app.db.models import PeerReview as PeerReviewRow

    fake_session = FakeSession()
    clients = {
        "Swift": _MultiCallClient(
            call_responses=[
                ["swift [[CONF:8]]"],
                ["reviewed peers"],
            ],
            whitelabel="Swift",
        ),
        "Prism": _MultiCallClient(
            call_responses=[
                ["prism [[CONF:7]]"],
                ["reviewed peers"],
            ],
            whitelabel="Prism",
        ),
    }
    apex = _make_apex_client(["synthesis"])

    tc = _setup_council_app(monkeypatch, clients, apex, fake_session=fake_session)
    try:
        with tc:
            r = tc.post(
                "/api/query",
                json={"mode": "council", "query": "question", "models": ["Swift", "Prism"]},
            )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    peer_reviews = [o for o in fake_session.added if isinstance(o, PeerReviewRow)]
    # 2 models × 1 target each = 2 PeerReview rows
    assert len(peer_reviews) == 2


def test_council_event_order(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify high-level event ordering: session → hex_starts → ... → synth → done."""
    clients = {
        "Swift": FakeClient(["s answer [[CONF:8]]"], whitelabel="Swift"),
        "Prism": FakeClient(["p answer [[CONF:7]]"], whitelabel="Prism"),
    }
    apex = _make_apex_client(["synthesis"])

    tc = _setup_council_app(monkeypatch, clients, apex)
    try:
        with tc:
            r = tc.post(
                "/api/query",
                json={"mode": "council", "query": "question", "models": ["Swift", "Prism"]},
            )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    events = parse_sse(r.text)
    names = [e for e, _ in events]

    assert names[0] == "session"
    assert names[-1] == "done"
    assert "hex_start" in names
    assert "hex_done" in names
    assert "synth_start" in names
    assert "synth_done" in names

    # synth_start comes after all hex_done events
    last_hex_done_idx = max(i for i, n in enumerate(names) if n == "hex_done")
    synth_start_idx = names.index("synth_start")
    assert synth_start_idx > last_hex_done_idx


def test_council_three_models(monkeypatch: pytest.MonkeyPatch) -> None:
    """Council works with 3 models: 3 hex_start, 3 hex_done, 6 peer_review events."""
    clients = {
        "Swift": FakeClient(["swift [[CONF:8]]"], whitelabel="Swift"),
        "Prism": FakeClient(["prism [[CONF:7]]"], whitelabel="Prism"),
        "Depth": FakeClient(["depth [[CONF:9]]"], whitelabel="Depth"),
    }
    apex = _make_apex_client(["synthesis"])

    tc = _setup_council_app(monkeypatch, clients, apex)
    try:
        with tc:
            r = tc.post(
                "/api/query",
                json={
                    "mode": "council",
                    "query": "question",
                    "models": ["Swift", "Prism", "Depth"],
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    events = parse_sse(r.text)
    names = [e for e, _ in events]

    assert names.count("hex_start") == 3
    assert names.count("hex_done") == 3
    # 3 models × 2 targets each = 6 peer_review events
    assert names.count("peer_review") == 6


# ---------------------------------------------------------------------------
# Multi-call fake client (Phase 1 + Phase 2)
# ---------------------------------------------------------------------------


class _MultiCallClient:
    """Fake LLM client that returns different responses per call (Phase 1, Phase 2)."""

    def __init__(self, call_responses: list[list[str]], whitelabel: str) -> None:
        self.whitelabel = whitelabel
        self._responses = call_responses
        self._call_count = 0

    async def stream(
        self,
        messages: list[Message],
        cache_key: str | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[StreamChunk]:
        idx = min(self._call_count, len(self._responses) - 1)
        self._call_count += 1
        for d in self._responses[idx]:
            yield StreamChunk(delta=d)
        yield StreamChunk(delta="", total_tokens=42, cached_tokens=7)
