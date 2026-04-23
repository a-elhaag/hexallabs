from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.auth.middleware import get_current_user
from app.auth.models import AuthUser
from app.db.session import get_session
from app.main import app
from tests.conftest import FakeClient, FakeSession, parse_sse


@pytest.fixture
def _base_overrides():
    user = AuthUser(id=uuid.uuid4(), email="user@example.com")
    fake_session = FakeSession()

    async def _session_gen():
        yield fake_session

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_session] = _session_gen
    yield user, fake_session
    app.dependency_overrides.clear()


def _fake_scout_result():
    from app.tools.web_search import SearchResult
    return SearchResult(
        summary="Web context here.",
        urls=["https://example.com"],
        raw=[],
        result_count=1,
    )


def _make_request(scout: str = "force") -> dict:
    return {
        "mode": "council",
        "query": "test query",
        "models": ["Swift", "Prism"],
        "scout": scout,
    }


def test_council_scout_force_emits_tool_call_and_result_before_hex_start(
    monkeypatch: pytest.MonkeyPatch,
    _base_overrides: tuple,
) -> None:
    """scout=force: tool_call + tool_result emitted before any hex_start."""
    import app.council.stream as council_module
    import app.api.query as query_module

    fake_result = _fake_scout_result()
    monkeypatch.setattr(query_module, "get_client", lambda _wl: FakeClient(["answer"]))
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")

    with patch("app.council.stream.scout_force", new=AsyncMock(return_value=("ctx", fake_result))):
        with patch("app.council.stream.get_client", return_value=FakeClient(["synth"])):
            with TestClient(app) as tc:
                r = tc.post("/api/query", json=_make_request("force"))

    assert r.status_code == 200
    events = parse_sse(r.text)
    names = [e[0] for e in events]
    assert "tool_call" in names
    assert "tool_result" in names
    first_hex_start = next(i for i, e in enumerate(events) if e[0] == "hex_start")
    tool_call_idx = next(i for i, e in enumerate(events) if e[0] == "tool_call")
    tool_result_idx = next(i for i, e in enumerate(events) if e[0] == "tool_result")
    assert tool_call_idx < first_hex_start
    assert tool_result_idx < first_hex_start


def test_council_scout_auto_also_does_pre_injection(
    monkeypatch: pytest.MonkeyPatch,
    _base_overrides: tuple,
) -> None:
    """scout=auto: same pre-injection as force in council context."""
    import app.api.query as query_module

    fake_result = _fake_scout_result()
    monkeypatch.setattr(query_module, "get_client", lambda _wl: FakeClient(["answer"]))
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")

    with patch("app.council.stream.scout_force", new=AsyncMock(return_value=("ctx", fake_result))):
        with patch("app.council.stream.get_client", return_value=FakeClient(["synth"])):
            with TestClient(app) as tc:
                r = tc.post("/api/query", json=_make_request("auto"))

    assert r.status_code == 200
    events = parse_sse(r.text)
    names = [e[0] for e in events]
    assert "tool_call" in names
    assert "tool_result" in names


def test_council_scout_off_no_tool_events(
    monkeypatch: pytest.MonkeyPatch,
    _base_overrides: tuple,
) -> None:
    """scout=off: no tool_call or tool_result events emitted."""
    import app.api.query as query_module

    monkeypatch.setattr(query_module, "get_client", lambda _wl: FakeClient(["answer"]))

    with patch("app.council.stream.get_client", return_value=FakeClient(["synth"])):
        with TestClient(app) as tc:
            r = tc.post("/api/query", json=_make_request("off"))

    assert r.status_code == 200
    events = parse_sse(r.text)
    names = [e[0] for e in events]
    assert "tool_call" not in names
    assert "tool_result" not in names


def test_council_scout_missing_key_returns_error_and_done(
    monkeypatch: pytest.MonkeyPatch,
    _base_overrides: tuple,
) -> None:
    """scout=force with missing TAVILY_API_KEY → error + done, no hex_start."""
    import app.api.query as query_module

    monkeypatch.setattr(query_module, "get_client", lambda _wl: FakeClient(["answer"]))

    with patch("app.council.stream.scout_force", new=AsyncMock(side_effect=ValueError("TAVILY_API_KEY not set"))):
        with TestClient(app) as tc:
            r = tc.post("/api/query", json=_make_request("force"))

    assert r.status_code == 200
    events = parse_sse(r.text)
    names = [e[0] for e in events]
    assert "error" in names
    assert "done" in names
    assert "hex_start" not in names
