from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.api import query as query_module
from app.auth.middleware import get_current_user
from app.auth.models import AuthUser
from app.db.session import get_session
from app.main import app
from tests.conftest import FakeClient, FakeSession


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    user = AuthUser(id=uuid.uuid4(), email="user@example.com")

    async def _fake_session():
        yield FakeSession()

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_session] = _fake_session
    monkeypatch.setattr(query_module, "get_client", lambda _wl: FakeClient(["ok"]))
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_missing_mode_returns_422(client: TestClient) -> None:
    r = client.post("/api/query", json={"query": "hi", "models": ["Apex"]})
    assert r.status_code == 422


def test_empty_query_returns_422(client: TestClient) -> None:
    r = client.post("/api/query", json={"mode": "oracle", "query": "", "models": ["Apex"]})
    assert r.status_code == 422


def test_invalid_mode_returns_422(client: TestClient) -> None:
    r = client.post("/api/query", json={"mode": "turbo", "query": "hi", "models": ["Apex"]})
    assert r.status_code == 422


def test_scout_bool_true_coerces_to_auto(client: TestClient) -> None:
    """scout=true (bool) coerced to 'auto' by validator — request succeeds."""
    r = client.post(
        "/api/query",
        json={"mode": "oracle", "query": "hi", "models": ["Apex"], "scout": True},
    )
    assert r.status_code == 200


def test_scout_bool_false_coerces_to_off(client: TestClient) -> None:
    """scout=false (bool) coerced to 'off' by validator — request succeeds."""
    r = client.post(
        "/api/query",
        json={"mode": "oracle", "query": "hi", "models": ["Apex"], "scout": False},
    )
    assert r.status_code == 200


def test_council_mode_accepted(client: TestClient) -> None:
    # Council mode is now implemented; valid request should return 200 (streaming)
    r = client.post(
        "/api/query",
        json={"mode": "council", "query": "hi", "models": ["Apex", "Swift"]},
    )
    assert r.status_code == 200


def test_workflow_empty_nodes_returns_422(client: TestClient) -> None:
    """workflow mode with no workflow_nodes returns 422 (was 501 before implementation)."""
    r = client.post(
        "/api/query",
        json={"mode": "workflow", "query": "hi", "workflow_nodes": []},
    )
    assert r.status_code == 422


def test_oracle_zero_models_returns_400(client: TestClient) -> None:
    r = client.post("/api/query", json={"mode": "oracle", "query": "hi", "models": []})
    assert r.status_code == 400


def test_oracle_two_models_returns_400(client: TestClient) -> None:
    r = client.post(
        "/api/query",
        json={"mode": "oracle", "query": "hi", "models": ["Apex", "Swift"]},
    )
    assert r.status_code == 400


def test_relay_one_model_returns_400(client: TestClient) -> None:
    r = client.post(
        "/api/query",
        json={"mode": "relay", "query": "hi", "relay_chain": ["Swift"]},
    )
    assert r.status_code == 400


def test_relay_three_models_returns_400(client: TestClient) -> None:
    r = client.post(
        "/api/query",
        json={"mode": "relay", "query": "hi", "relay_chain": ["A", "B", "C"]},
    )
    assert r.status_code == 400


def test_no_auth_returns_401() -> None:
    """No auth override → real middleware runs → 401."""
    with TestClient(app) as tc:
        r = tc.post("/api/query", json={"mode": "oracle", "query": "hi", "models": ["Apex"]})
    assert r.status_code == 401
