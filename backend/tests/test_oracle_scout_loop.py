from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api import query as query_module
from app.auth.middleware import get_current_user
from app.auth.models import AuthUser
from app.db.session import get_session
from app.llm.base import Message, StreamChunk, ToolCall
from app.main import app
from app.tools.web_search import SearchResult


# ── helpers ──────────────────────────────────────────────────────────────────

class _FakeSession:
    def __init__(self) -> None:
        self.added: list[object] = []

    def add(self, obj: object) -> None:
        if not getattr(obj, "id", None):
            obj.id = uuid.uuid4()  # type: ignore[attr-defined]
        self.added.append(obj)

    async def flush(self) -> None:
        return None

    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None

    async def close(self) -> None:
        return None

    async def get(self, _model: object, _id: uuid.UUID) -> object | None:
        return None


def _parse_sse(body: str) -> list[tuple[str, dict[str, object]]]:
    events: list[tuple[str, dict[str, object]]] = []
    for block in body.split("\n\n"):
        block = block.strip("\n")
        if not block or block.startswith(":"):
            continue
        event: str | None = None
        data: str | None = None
        for line in block.split("\n"):
            if line.startswith("event: "):
                event = line[len("event: "):]
            elif line.startswith("data: "):
                data = line[len("data: "):]
        if event and data is not None:
            events.append((event, json.loads(data)))
    return events


def _setup_app(monkeypatch: pytest.MonkeyPatch, fake_client: object) -> TestClient:
    user = AuthUser(id=uuid.uuid4(), email="user@example.com")

    async def _fake_session():  # type: ignore[no-untyped-def]
        yield _FakeSession()

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_session] = _fake_session
    monkeypatch.setattr(query_module, "get_client", lambda _wl: fake_client)
    return TestClient(app)


# ── scout="off" → no tools passed, no tool events ────────────────────────────

class _PlainClient:
    whitelabel = "Apex"
    called_with_tools: list[Any] = []

    async def stream(
        self,
        messages: list[Message],
        cache_key: str | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[StreamChunk]:
        _PlainClient.called_with_tools.append(tools)
        yield StreamChunk(delta="hello")
        yield StreamChunk(stop_reason="end_turn")


def test_scout_off_no_tool_events(monkeypatch: pytest.MonkeyPatch) -> None:
    _PlainClient.called_with_tools = []
    client = _setup_app(monkeypatch, _PlainClient())
    try:
        r = client.post(
            "/api/query",
            json={"mode": "oracle", "query": "hi", "models": ["Apex"], "scout": "off"},
        )
        assert r.status_code == 200
        events = _parse_sse(r.text)
        names = [e for e, _ in events]
        assert "tool_call" not in names
        assert "tool_result" not in names
        assert _PlainClient.called_with_tools[-1] is None
    finally:
        app.dependency_overrides.clear()


# ── scout="auto" + model does NOT call tool → no tool events ─────────────────

def test_scout_auto_no_tool_call_from_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "fake-key")

    class _NoToolClient:
        whitelabel = "Apex"

        async def stream(
            self,
            messages: list[Message],
            cache_key: str | None = None,
            tools: list[dict[str, Any]] | None = None,
        ) -> AsyncIterator[StreamChunk]:
            yield StreamChunk(delta="direct answer")
            yield StreamChunk(stop_reason="end_turn")

    client = _setup_app(monkeypatch, _NoToolClient())
    try:
        r = client.post(
            "/api/query",
            json={"mode": "oracle", "query": "2+2", "models": ["Apex"], "scout": "auto"},
        )
        assert r.status_code == 200
        events = _parse_sse(r.text)
        names = [e for e, _ in events]
        assert "tool_call" not in names
        assert "tool_result" not in names
        deltas = [p["delta"] for ev, p in events if ev == "token"]
        assert "".join(deltas) == "direct answer"  # type: ignore[arg-type]
    finally:
        app.dependency_overrides.clear()


# ── scout="auto" + model calls web_search → tool loop executes ───────────────

def test_scout_auto_tool_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "fake-key")

    _call_count = {"n": 0}

    class _ToolCallingClient:
        whitelabel = "Apex"

        async def stream(
            self,
            messages: list[Message],
            cache_key: str | None = None,
            tools: list[dict[str, Any]] | None = None,
        ) -> AsyncIterator[StreamChunk]:
            _call_count["n"] += 1
            if _call_count["n"] == 1:
                # First turn: emit a tool call
                yield StreamChunk(
                    tool_call=ToolCall(
                        id="tc_001", name="web_search", input={"query": "latest news"}
                    )
                )
                yield StreamChunk(stop_reason="tool_use")
            else:
                # Second turn: emit text after seeing tool result
                yield StreamChunk(delta="Here is what I found: ...")
                yield StreamChunk(stop_reason="end_turn")

    fake_result = SearchResult(
        summary="News summary",
        urls=["https://example.com"],
        result_count=1,
        raw=[{"title": "News", "url": "https://example.com", "content": "..."}],
    )

    async def _fake_dispatch(tc: ToolCall, *, tavily_api_key: str, scout_max_results: int) -> SearchResult:
        return fake_result

    monkeypatch.setattr(query_module, "_dispatch_tool", _fake_dispatch)

    client = _setup_app(monkeypatch, _ToolCallingClient())
    try:
        r = client.post(
            "/api/query",
            json={"mode": "oracle", "query": "news", "models": ["Apex"], "scout": "auto"},
        )
        assert r.status_code == 200
        events = _parse_sse(r.text)
        names = [e for e, _ in events]

        assert "tool_call" in names
        assert "tool_result" in names

        # Ordering: tool_call before tool_result, tokens after
        tc_idx = names.index("tool_call")
        tr_idx = names.index("tool_result")
        tok_idx = names.index("token")
        done_idx = names.index("done")

        assert tc_idx < tr_idx < tok_idx < done_idx

        # Check tool_call payload
        tc_data = next(p for ev, p in events if ev == "tool_call")
        assert tc_data["name"] == "web_search"
        assert tc_data["id"] == "tc_001"

        # Check tool_result payload
        tr_data = next(p for ev, p in events if ev == "tool_result")
        assert tr_data["summary"] == "News summary"
        assert "https://example.com" in tr_data["urls"]
    finally:
        app.dependency_overrides.clear()


# ── scout="force" → pre-search fires with forced=True before any stream call ──

def test_scout_force_pre_search(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "fake-key")

    _stream_call_count = {"n": 0}

    class _ForcedClient:
        whitelabel = "Apex"

        async def stream(
            self,
            messages: list[Message],
            cache_key: str | None = None,
            tools: list[dict[str, Any]] | None = None,
        ) -> AsyncIterator[StreamChunk]:
            _stream_call_count["n"] += 1
            yield StreamChunk(delta="answer")
            yield StreamChunk(stop_reason="end_turn")

    fake_result = SearchResult(
        summary="Pre-fetched summary",
        urls=["https://pre.com"],
        result_count=1,
        raw=[],
    )

    async def _fake_search(query: str, max_results: int = 5, *, api_key: str) -> SearchResult:
        return fake_result

    monkeypatch.setattr(query_module, "execute_web_search", _fake_search)

    client = _setup_app(monkeypatch, _ForcedClient())
    try:
        r = client.post(
            "/api/query",
            json={"mode": "oracle", "query": "recent events", "models": ["Apex"], "scout": "force"},
        )
        assert r.status_code == 200
        events = _parse_sse(r.text)
        names = [e for e, _ in events]

        assert "tool_call" in names
        assert "tool_result" in names

        # forced tool_call fires before any token
        tc_idx = names.index("tool_call")
        first_token_idx = next((i for i, n in enumerate(names) if n == "token"), len(names))
        assert tc_idx < first_token_idx

        # forced flag is True
        tc_data = next(p for ev, p in events if ev == "tool_call")
        assert tc_data.get("forced") is True

        # stream was called (model ran after pre-search)
        assert _stream_call_count["n"] >= 1
    finally:
        app.dependency_overrides.clear()


# ── bool coercion: True → auto, False → off ──────────────────────────────────

def test_scout_bool_coercion_true(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "fake-key")
    _tools_seen: list[Any] = []

    class _CoercionClient:
        whitelabel = "Apex"

        async def stream(
            self,
            messages: list[Message],
            cache_key: str | None = None,
            tools: list[dict[str, Any]] | None = None,
        ) -> AsyncIterator[StreamChunk]:
            _tools_seen.append(tools)
            yield StreamChunk(delta="x")

    client = _setup_app(monkeypatch, _CoercionClient())
    try:
        r = client.post(
            "/api/query",
            json={"mode": "oracle", "query": "hi", "models": ["Apex"], "scout": True},
        )
        assert r.status_code == 200
        # tools should be non-None (auto mode)
        assert _tools_seen and _tools_seen[0] is not None
    finally:
        app.dependency_overrides.clear()
