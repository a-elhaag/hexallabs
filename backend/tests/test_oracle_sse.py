from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator

import pytest
from fastapi.testclient import TestClient

from app.api import query as query_module
from app.auth.middleware import get_current_user
from app.auth.models import AuthUser
from app.db.session import get_session
from app.llm.base import Message, StreamChunk
from app.main import app


class _FakeClient:
    whitelabel = "Apex"

    def __init__(self, deltas: list[str], total: int = 42, cached: int = 7) -> None:
        self._deltas = deltas
        self._total = total
        self._cached = cached

    async def stream(
        self, messages: list[Message], cache_key: str | None = None
    ) -> AsyncIterator[StreamChunk]:
        for d in self._deltas:
            yield StreamChunk(delta=d)
        yield StreamChunk(delta="", total_tokens=self._total, cached_tokens=self._cached)


class _FakeSession:
    """Minimal AsyncSession stand-in. Captures adds, no-op on flush/commit/rollback."""

    def __init__(self) -> None:
        self.added: list[object] = []

    def add(self, obj: object) -> None:
        # Emulate server_default id + timestamp population for rows we need to read back.
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
                event = line[len("event: ") :]
            elif line.startswith("data: "):
                data = line[len("data: ") :]
        if event and data is not None:
            events.append((event, json.loads(data)))
    return events


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    user = AuthUser(id=uuid.uuid4(), email="user@example.com")

    async def _fake_session():  # type: ignore[no-untyped-def]
        yield _FakeSession()

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_session] = _fake_session
    monkeypatch.setattr(
        query_module, "get_client", lambda _wl: _FakeClient(["Hello", " world"])
    )
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_oracle_emits_contract_event_order(client: TestClient) -> None:
    r = client.post("/api/query", json={"mode": "oracle", "query": "hi", "models": ["Apex"]})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")

    events = _parse_sse(r.text)
    names = [e for e, _ in events]
    # session first, done last, no peer_review / synth_* in oracle
    assert names[0] == "session"
    assert names[-1] == "done"
    assert "hex_start" in names
    assert "hex_done" in names
    assert "confidence" in names
    assert "peer_review" not in names
    assert "synth_start" not in names
    assert "synth_token" not in names
    assert "synth_done" not in names


def test_oracle_tokens_preserve_order(client: TestClient) -> None:
    r = client.post("/api/query", json={"mode": "oracle", "query": "hi", "models": ["Apex"]})
    events = _parse_sse(r.text)
    deltas = [payload["delta"] for ev, payload in events if ev == "token"]
    assert "".join(deltas) == "Hello world"


def test_oracle_requires_exactly_one_model(client: TestClient) -> None:
    r = client.post("/api/query", json={"mode": "oracle", "query": "hi", "models": []})
    assert r.status_code == 400


def test_non_oracle_mode_not_implemented(client: TestClient) -> None:
    r = client.post(
        "/api/query", json={"mode": "council", "query": "hi", "models": ["Apex", "Swift"]}
    )
    assert r.status_code == 501


def test_unknown_model_returns_400(monkeypatch: pytest.MonkeyPatch) -> None:
    user = AuthUser(id=uuid.uuid4(), email="user@example.com")

    async def _fake_session():  # type: ignore[no-untyped-def]
        yield _FakeSession()

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_session] = _fake_session

    def _raise(_wl: str) -> object:
        raise KeyError("Unknown white-label 'Nope'")

    monkeypatch.setattr(query_module, "get_client", _raise)
    try:
        with TestClient(app) as c:
            r = c.post("/api/query", json={"mode": "oracle", "query": "hi", "models": ["Nope"]})
        assert r.status_code == 400
    finally:
        app.dependency_overrides.clear()


def test_missing_auth_returns_401() -> None:
    # No dependency_overrides for auth → real get_current_user runs → 401.
    with TestClient(app) as c:
        r = c.post("/api/query", json={"mode": "oracle", "query": "hi", "models": ["Apex"]})
    assert r.status_code == 401
