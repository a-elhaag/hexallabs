from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api import prompt_forge as forge_module
from app.auth.middleware import get_current_user
from app.auth.models import AuthUser
from app.llm.base import Message, StreamChunk
from app.main import app


class _FakeForgeClient:
    """Fake LLM client that emits pre-configured delta chunks."""

    whitelabel = "Spark"

    def __init__(self, deltas: list[str]) -> None:
        self._deltas = deltas

    async def stream(
        self,
        messages: list[Message],
        cache_key: str | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[StreamChunk]:
        for d in self._deltas:
            yield StreamChunk(delta=d)
        yield StreamChunk(delta="", total_tokens=10, cached_tokens=8)


class _FakeEmptyClient:
    """Fake LLM client that returns no text (empty response)."""

    whitelabel = "Spark"

    async def stream(
        self,
        messages: list[Message],
        cache_key: str | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[StreamChunk]:
        yield StreamChunk(delta="", total_tokens=0, cached_tokens=0)


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    user = AuthUser(id=uuid.uuid4(), email="forge_user@example.com")
    app.dependency_overrides[get_current_user] = lambda: user
    monkeypatch.setattr(
        forge_module,
        "get_client",
        lambda _wl: _FakeForgeClient(["What are", " the key", " differences?"]),
    )
    yield TestClient(app)
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------


def test_forge_returns_200(client: TestClient) -> None:
    r = client.post("/api/prompt-forge", json={"query": "tell me stuff about python"})
    assert r.status_code == 200


def test_forge_response_schema(client: TestClient) -> None:
    """Response must contain exactly 'original' and 'improved' — no model metadata."""
    r = client.post("/api/prompt-forge", json={"query": "tell me stuff about python"})
    body = r.json()
    assert set(body.keys()) == {"original", "improved"}


def test_forge_original_matches_request(client: TestClient) -> None:
    raw = "tell me stuff about python"
    r = client.post("/api/prompt-forge", json={"query": raw})
    assert r.json()["original"] == raw


def test_forge_improved_is_non_empty(client: TestClient) -> None:
    r = client.post("/api/prompt-forge", json={"query": "tell me stuff about python"})
    improved = r.json()["improved"]
    assert isinstance(improved, str)
    assert len(improved) > 0


def test_forge_improved_assembles_deltas(client: TestClient) -> None:
    """All streamed delta chunks must be concatenated into 'improved'."""
    r = client.post("/api/prompt-forge", json={"query": "any query"})
    assert r.json()["improved"] == "What are the key differences?"


# ---------------------------------------------------------------------------
# Auth tests
# ---------------------------------------------------------------------------


def test_forge_unauthenticated_returns_401() -> None:
    """No dependency override → real get_current_user → missing token → 401."""
    with TestClient(app) as c:
        r = c.post("/api/prompt-forge", json={"query": "some query"})
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------


def test_forge_empty_query_returns_422(client: TestClient) -> None:
    r = client.post("/api/prompt-forge", json={"query": ""})
    assert r.status_code == 422


def test_forge_missing_query_field_returns_422(client: TestClient) -> None:
    r = client.post("/api/prompt-forge", json={})
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Edge-case: model returns empty text → 502
# ---------------------------------------------------------------------------


def test_forge_empty_model_response_returns_502(monkeypatch: pytest.MonkeyPatch) -> None:
    user = AuthUser(id=uuid.uuid4(), email="forge_user@example.com")
    app.dependency_overrides[get_current_user] = lambda: user
    monkeypatch.setattr(forge_module, "get_client", lambda _wl: _FakeEmptyClient())
    try:
        with TestClient(app) as c:
            r = c.post("/api/prompt-forge", json={"query": "some query"})
        assert r.status_code == 502
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Caching contract: system message must have cache=True
# ---------------------------------------------------------------------------


def test_forge_system_message_has_cache_true(monkeypatch: pytest.MonkeyPatch) -> None:
    """The system prompt must be sent with cache=True per hexal-caching-rules."""
    captured: list[list[Message]] = []

    class _CapturingClient:
        whitelabel = "Spark"

        async def stream(
            self,
            messages: list[Message],
            cache_key: str | None = None,
            tools: list[dict[str, Any]] | None = None,
        ) -> AsyncIterator[StreamChunk]:
            captured.append(messages)
            yield StreamChunk(delta="Improved query.")
            yield StreamChunk(delta="", total_tokens=5, cached_tokens=5)

    user = AuthUser(id=uuid.uuid4(), email="forge_user@example.com")
    app.dependency_overrides[get_current_user] = lambda: user
    monkeypatch.setattr(forge_module, "get_client", lambda _wl: _CapturingClient())
    try:
        with TestClient(app) as c:
            r = c.post("/api/prompt-forge", json={"query": "test"})
        assert r.status_code == 200
        assert len(captured) == 1
        msgs = captured[0]
        system_msgs = [m for m in msgs if m.role == "system"]
        assert len(system_msgs) == 1, "Expected exactly one system message"
        assert system_msgs[0].cache is True, "System message must have cache=True"
    finally:
        app.dependency_overrides.clear()


def test_forge_user_message_has_cache_false(monkeypatch: pytest.MonkeyPatch) -> None:
    """The user query must NOT be cached — it's dynamic per request."""
    captured: list[list[Message]] = []

    class _CapturingClient:
        whitelabel = "Spark"

        async def stream(
            self,
            messages: list[Message],
            cache_key: str | None = None,
            tools: list[dict[str, Any]] | None = None,
        ) -> AsyncIterator[StreamChunk]:
            captured.append(messages)
            yield StreamChunk(delta="Improved query.")
            yield StreamChunk(delta="", total_tokens=5, cached_tokens=5)

    user = AuthUser(id=uuid.uuid4(), email="forge_user@example.com")
    app.dependency_overrides[get_current_user] = lambda: user
    monkeypatch.setattr(forge_module, "get_client", lambda _wl: _CapturingClient())
    try:
        with TestClient(app) as c:
            r = c.post("/api/prompt-forge", json={"query": "test"})
        assert r.status_code == 200
        msgs = captured[0]
        user_msgs = [m for m in msgs if m.role == "user"]
        assert len(user_msgs) == 1, "Expected exactly one user message"
        assert user_msgs[0].cache is False, "User message must NOT have cache=True"
    finally:
        app.dependency_overrides.clear()
