"""Tests for Scout integration in Relay mode.

Both force and auto scout modes do pre-injection in relay context:
  - tool_call + tool_result events emitted before hex_start
  - system message prepended to Stage A messages
  - scout=off: no tool events emitted

Scout failure (missing TAVILY_API_KEY) returns error + done immediately.
"""
from __future__ import annotations

import json
import uuid
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api import query as query_module
from app.auth.middleware import get_current_user
from app.auth.models import AuthUser
from app.db.session import get_session
from app.llm.base import Message, StreamChunk
from app.main import app
from tests.conftest import FakeSession, parse_sse


# ---------------------------------------------------------------------------
# Fake relay clients
# ---------------------------------------------------------------------------

class _FakeClient:
    """LLM client that emits configured deltas (no triggers — passthrough path)."""

    def __init__(
        self,
        deltas: list[str],
        whitelabel: str = "Swift",
        total: int = 42,
        cached: int = 7,
    ) -> None:
        self.whitelabel = whitelabel
        self._deltas = deltas
        self._total = total
        self._cached = cached

    async def stream(
        self,
        messages: list[Message],
        cache_key: str | None = None,
        tools: list[dict[str, Any]] | None = None,
    ):
        for d in self._deltas:
            yield StreamChunk(delta=d)
        yield StreamChunk(delta="", total_tokens=self._total, cached_tokens=self._cached)


class _FakeApex:
    """Apex watcher that never fires a handoff (passthrough scenario)."""

    whitelabel = "Apex"

    async def stream(
        self,
        messages: list[Message],
        cache_key: str | None = None,
        tools: list[dict[str, Any]] | None = None,
    ):
        verdict = json.dumps({"handoff": False, "reason": "ok"})
        yield StreamChunk(delta=verdict)
        yield StreamChunk(delta="", total_tokens=10, cached_tokens=0)


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _setup_relay_app(
    monkeypatch: pytest.MonkeyPatch,
    client_a_deltas: list[str] | None = None,
) -> tuple[TestClient, FakeSession]:
    """Wire up fake relay clients and return (TestClient, FakeSession)."""
    if client_a_deltas is None:
        client_a_deltas = ["some answer text"]

    user = AuthUser(id=uuid.uuid4(), email="user@example.com")
    fake_session = FakeSession()
    fake_a = _FakeClient(client_a_deltas, whitelabel="Swift")
    fake_b = _FakeClient(["B answer"], whitelabel="Depth")
    fake_apex = _FakeApex()

    def _fake_get_client(wl: str) -> object:
        if wl == "Swift":
            return fake_a
        if wl == "Depth":
            return fake_b
        if wl == "Apex":
            return fake_apex
        raise KeyError(f"Unknown white-label {wl!r}")

    async def _fake_session_gen():
        yield fake_session

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_session] = _fake_session_gen
    monkeypatch.setattr(query_module, "get_client", _fake_get_client)

    return TestClient(app), fake_session


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_relay_scout_force_emits_tool_call_and_result_before_hex_start(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """scout=force: tool_call + tool_result emitted BEFORE hex_start for Stage A."""
    from app.tools.web_search import SearchResult

    fake_result = SearchResult(
        summary="Paris is the capital of France.",
        urls=["https://example.com"],
        raw=[],
        result_count=1,
    )

    tc, _ = _setup_relay_app(monkeypatch)

    with patch("app.relay.stream.scout_force", new=AsyncMock(return_value=("context text", fake_result))):
        with tc:
            r = tc.post(
                "/api/query",
                json={
                    "mode": "relay",
                    "query": "capital of France",
                    "relay_chain": ["Swift", "Depth"],
                    "scout": "force",
                },
            )

    app.dependency_overrides.clear()

    assert r.status_code == 200
    events = parse_sse(r.text)
    names = [e for e, _ in events]

    # tool_call and tool_result must be present
    assert "tool_call" in names
    assert "tool_result" in names

    # tool_call must appear before first hex_start
    tc_idx = names.index("tool_call")
    hex_start_idx = names.index("hex_start")
    assert tc_idx < hex_start_idx, "tool_call must precede hex_start"

    # tool_result must appear before first hex_start
    tr_idx = names.index("tool_result")
    assert tr_idx < hex_start_idx, "tool_result must precede hex_start"

    # Verify tool_call payload
    tc_data = next(d for e, d in events if e == "tool_call")
    assert tc_data["name"] == "web_search"
    assert tc_data.get("forced") is True
    assert tc_data["hex"] == "Swift"

    # Verify tool_result payload
    tr_data = next(d for e, d in events if e == "tool_result")
    assert tr_data["name"] == "web_search"
    assert tr_data["result_count"] == 1
    assert tr_data["hex"] == "Swift"

    # Stream must complete
    assert names[-1] == "done"


def test_relay_scout_auto_also_does_pre_injection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """scout=auto in relay: same pre-injection as force (no agentic loop)."""
    from app.tools.web_search import SearchResult

    fake_result = SearchResult(
        summary="Auto search result.",
        urls=["https://auto.example.com"],
        raw=[],
        result_count=2,
    )

    tc, _ = _setup_relay_app(monkeypatch)

    with patch("app.relay.stream.scout_force", new=AsyncMock(return_value=("auto context", fake_result))):
        with tc:
            r = tc.post(
                "/api/query",
                json={
                    "mode": "relay",
                    "query": "some query",
                    "relay_chain": ["Swift", "Depth"],
                    "scout": "auto",
                },
            )

    app.dependency_overrides.clear()

    assert r.status_code == 200
    events = parse_sse(r.text)
    names = [e for e, _ in events]

    assert "tool_call" in names
    assert "tool_result" in names

    tc_idx = names.index("tool_call")
    hex_start_idx = names.index("hex_start")
    assert tc_idx < hex_start_idx

    tr_data = next(d for e, d in events if e == "tool_result")
    assert tr_data["result_count"] == 2

    assert names[-1] == "done"


def test_relay_scout_off_no_tool_events(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """scout=off (default): no tool_call or tool_result events emitted."""
    tc, _ = _setup_relay_app(monkeypatch)

    with tc:
        r = tc.post(
            "/api/query",
            json={
                "mode": "relay",
                "query": "hello world",
                "relay_chain": ["Swift", "Depth"],
                # scout defaults to "off"
            },
        )

    app.dependency_overrides.clear()

    assert r.status_code == 200
    events = parse_sse(r.text)
    names = [e for e, _ in events]

    assert "tool_call" not in names
    assert "tool_result" not in names
    assert names[-1] == "done"


def test_relay_scout_force_missing_tavily_key_emits_error_and_done(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """scout=force with no TAVILY_API_KEY: error + done, no hex_start, no tokens."""
    tc, _ = _setup_relay_app(monkeypatch)

    # scout_force raises ValueError when TAVILY_API_KEY is not set
    with patch(
        "app.relay.stream.scout_force",
        new=AsyncMock(side_effect=ValueError("TAVILY_API_KEY not set")),
    ):
        with tc:
            r = tc.post(
                "/api/query",
                json={
                    "mode": "relay",
                    "query": "test query",
                    "relay_chain": ["Swift", "Depth"],
                    "scout": "force",
                },
            )

    app.dependency_overrides.clear()

    assert r.status_code == 200
    events = parse_sse(r.text)
    names = [e for e, _ in events]

    assert "error" in names
    assert "hex_start" not in names
    assert "token" not in names
    assert names[-1] == "done"

    error_data = next(d for e, d in events if e == "error")
    assert error_data["code"] == "MissingConfig"
    assert "TAVILY_API_KEY" in error_data["message"]


def test_relay_scout_force_scout_force_called_with_prompt_and_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """scout=force: scout_force is called with the prompt string."""
    from app.tools.web_search import SearchResult

    fake_result = SearchResult(
        summary="Result.",
        urls=["https://example.com"],
        raw=[],
        result_count=1,
    )

    tc, _ = _setup_relay_app(monkeypatch)
    mock_scout = AsyncMock(return_value=("context", fake_result))

    with patch("app.relay.stream.scout_force", new=mock_scout):
        with tc:
            r = tc.post(
                "/api/query",
                json={
                    "mode": "relay",
                    "query": "exact query text",
                    "relay_chain": ["Swift", "Depth"],
                    "scout": "force",
                },
            )

    app.dependency_overrides.clear()

    assert r.status_code == 200
    mock_scout.assert_awaited_once()
    call_args = mock_scout.call_args
    assert call_args[0][0] == "exact query text"
