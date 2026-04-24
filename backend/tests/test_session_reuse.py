from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.api import query as query_module
from app.auth.middleware import get_current_user
from app.auth.models import AuthUser
from app.db.models import Session as SessionRow
from app.db.models.user_quota import UserQuota
from app.db.session import get_session
from app.main import app
from tests.conftest import FakeClient, FakeSession


class _FakeSessionWithLookup(FakeSession):
    """FakeSession that returns a pre-configured SessionRow on db.get().

    Returns None for UserQuota lookups so QuotaService.get_or_create creates a
    fresh quota row (which is flushed/added but not verified by these tests).
    """

    def __init__(self, session_row: SessionRow | None = None) -> None:
        super().__init__()
        self._session_row = session_row

    async def get(self, _model: object, _id: uuid.UUID) -> object | None:
        if _model is UserQuota:
            return None
        return self._session_row


def test_new_session_created_when_no_session_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No session_id → a new SessionRow is added to DB."""
    user = AuthUser(id=uuid.uuid4(), email="user@example.com")
    fake_db = FakeSession()

    async def _session_gen():
        yield fake_db

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_session] = _session_gen
    monkeypatch.setattr(query_module, "get_client", lambda _wl: FakeClient(["hi"]))

    with TestClient(app) as tc:
        r = tc.post("/api/query", json={"mode": "oracle", "query": "hi", "models": ["Apex"]})
    app.dependency_overrides.clear()

    assert r.status_code == 200
    sessions = [o for o in fake_db.added if isinstance(o, SessionRow)]
    assert len(sessions) == 1


def test_existing_session_reused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Valid session_id for same user → no new SessionRow added."""
    user_id = uuid.uuid4()
    session_id = uuid.uuid4()
    existing = SessionRow(
        id=session_id,
        user_id=user_id,
        mode="oracle",
        primal_protocol=False,
        scout_enabled="off",
    )
    fake_db = _FakeSessionWithLookup(session_row=existing)

    async def _session_gen():
        yield fake_db

    app.dependency_overrides[get_current_user] = lambda: AuthUser(id=user_id, email="u@u.com")
    app.dependency_overrides[get_session] = _session_gen
    monkeypatch.setattr(query_module, "get_client", lambda _wl: FakeClient(["hi"]))

    with TestClient(app) as tc:
        r = tc.post(
            "/api/query",
            json={"mode": "oracle", "query": "hi", "models": ["Apex"], "session_id": str(session_id)},
        )
    app.dependency_overrides.clear()

    assert r.status_code == 200
    sessions = [o for o in fake_db.added if isinstance(o, SessionRow)]
    assert len(sessions) == 0


def test_session_not_found_returns_404(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """session_id that doesn't exist → 404."""
    fake_db = _FakeSessionWithLookup(session_row=None)

    async def _session_gen():
        yield fake_db

    app.dependency_overrides[get_current_user] = lambda: AuthUser(id=uuid.uuid4(), email="u@u.com")
    app.dependency_overrides[get_session] = _session_gen
    monkeypatch.setattr(query_module, "get_client", lambda _wl: FakeClient(["hi"]))

    with TestClient(app) as tc:
        r = tc.post(
            "/api/query",
            json={
                "mode": "oracle",
                "query": "hi",
                "models": ["Apex"],
                "session_id": str(uuid.uuid4()),
            },
        )
    app.dependency_overrides.clear()

    assert r.status_code == 404


def test_session_wrong_user_returns_404(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """session_id exists but belongs to different user → 404."""
    other_user_id = uuid.uuid4()
    session_id = uuid.uuid4()
    existing = SessionRow(
        id=session_id,
        user_id=other_user_id,
        mode="oracle",
        primal_protocol=False,
        scout_enabled="off",
    )
    fake_db = _FakeSessionWithLookup(session_row=existing)

    async def _session_gen():
        yield fake_db

    requesting_user_id = uuid.uuid4()
    app.dependency_overrides[get_current_user] = lambda: AuthUser(
        id=requesting_user_id, email="u@u.com"
    )
    app.dependency_overrides[get_session] = _session_gen
    monkeypatch.setattr(query_module, "get_client", lambda _wl: FakeClient(["hi"]))

    with TestClient(app) as tc:
        r = tc.post(
            "/api/query",
            json={
                "mode": "oracle",
                "query": "hi",
                "models": ["Apex"],
                "session_id": str(session_id),
            },
        )
    app.dependency_overrides.clear()

    assert r.status_code == 404
