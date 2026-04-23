from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api import query as query_module
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


def test_scout_force_emits_tool_call_and_result(
    monkeypatch: pytest.MonkeyPatch,
    _base_overrides: tuple,
) -> None:
    """scout=force: pre-execute search, emits tool_call + tool_result before tokens."""
    from app.tools.web_search import SearchResult

    fake_result = SearchResult(
        summary="Paris is the capital of France.",
        urls=["https://example.com"],
        raw=[],
        result_count=1,
    )

    monkeypatch.setattr(query_module, "get_client", lambda _wl: FakeClient(["Paris"]))
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")

    with patch("app.tools.scout._execute_web_search", new=AsyncMock(return_value=fake_result)):
        with patch("app.config.get_settings") as mock_settings:
            mock_settings.return_value.tavily_api_key = "tvly-test"
            mock_settings.return_value.scout_max_results = 5
            mock_settings.return_value.scout_max_turns = 4
            with TestClient(app) as tc:
                r = tc.post(
                    "/api/query",
                    json={"mode": "oracle", "query": "capital of France", "models": ["Apex"], "scout": "force"},
                )

    assert r.status_code == 200
    events = parse_sse(r.text)
    names = [e for e, _ in events]

    assert "tool_call" in names
    assert "tool_result" in names

    tc_data = next(d for e, d in events if e == "tool_call")
    assert tc_data["name"] == "web_search"
    assert tc_data.get("forced") is True

    tr_data = next(d for e, d in events if e == "tool_result")
    assert tr_data["name"] == "web_search"
    assert tr_data["result_count"] == 1

    tc_idx = names.index("tool_call")
    token_idx = names.index("token")
    assert tc_idx < token_idx


def test_scout_force_missing_tavily_key_emits_error(
    monkeypatch: pytest.MonkeyPatch,
    _base_overrides: tuple,
) -> None:
    """scout=force with no TAVILY_API_KEY → error event then done, no token events."""
    monkeypatch.setattr(query_module, "get_client", lambda _wl: FakeClient(["should not emit"]))

    with patch("app.config.get_settings") as mock_settings:
        mock_settings.return_value.tavily_api_key = None
        mock_settings.return_value.scout_max_results = 5
        mock_settings.return_value.scout_max_turns = 4

        with TestClient(app) as tc:
            r = tc.post(
                "/api/query",
                json={"mode": "oracle", "query": "test", "models": ["Apex"], "scout": "force"},
            )

    assert r.status_code == 200
    events = parse_sse(r.text)
    names = [e for e, _ in events]
    assert "error" in names
    assert "token" not in names
    assert names[-1] == "done"


def test_scout_force_search_exception_emits_error(
    monkeypatch: pytest.MonkeyPatch,
    _base_overrides: tuple,
) -> None:
    """scout=force when search raises → error event, no tokens."""
    monkeypatch.setattr(query_module, "get_client", lambda _wl: FakeClient(["should not emit"]))

    with patch(
        "app.tools.scout._execute_web_search",
        new=AsyncMock(side_effect=RuntimeError("network failure")),
    ):
        with patch("app.config.get_settings") as mock_settings:
            mock_settings.return_value.tavily_api_key = "tvly-test"
            mock_settings.return_value.scout_max_results = 5
            mock_settings.return_value.scout_max_turns = 4

            with TestClient(app) as tc:
                r = tc.post(
                    "/api/query",
                    json={"mode": "oracle", "query": "test", "models": ["Apex"], "scout": "force"},
                )

    assert r.status_code == 200
    events = parse_sse(r.text)
    names = [e for e, _ in events]
    assert "error" in names
    assert "token" not in names
    assert names[-1] == "done"


def test_scout_off_no_tools_passed(
    monkeypatch: pytest.MonkeyPatch,
    _base_overrides: tuple,
) -> None:
    """scout=off (default): no tool_call or tool_result events."""
    monkeypatch.setattr(query_module, "get_client", lambda _wl: FakeClient(["hello"]))

    with TestClient(app) as tc:
        r = tc.post(
            "/api/query",
            json={"mode": "oracle", "query": "hello", "models": ["Apex"]},
        )

    assert r.status_code == 200
    events = parse_sse(r.text)
    names = [e for e, _ in events]
    assert "tool_call" not in names
    assert "tool_result" not in names
