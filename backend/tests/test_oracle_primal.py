"""Tests for Primal Protocol in Oracle mode.

Verifies that primal=True on an oracle request emits a `primal` event
(with a non-empty `text` field) between `hex_done` and `done`, and that
primal=False does NOT emit the event.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.api import query as query_module
from app.auth.middleware import get_current_user
from app.auth.models import AuthUser
from app.db.session import get_session
from app.main import app
from tests.conftest import FakeClient, FakeSession, parse_sse


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def _base_overrides():
    """Set up auth + DB dependency overrides; cleans up after each test."""
    user = AuthUser(id=uuid.uuid4(), email="user@example.com")
    fake_session = FakeSession()

    async def _session_gen():
        yield fake_session

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_session] = _session_gen
    yield user, fake_session
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_get_client(oracle_client: object, apex_client: object):
    """Return a get_client stub that returns different clients by whitelabel."""

    def _get_client(whitelabel: str) -> object:
        if whitelabel == "Apex":
            return apex_client
        return oracle_client

    return _get_client


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_primal_true_emits_primal_event(
    monkeypatch: pytest.MonkeyPatch,
    _base_overrides: tuple,
) -> None:
    """primal_protocol=True: stream contains a `primal` event."""
    oracle_client = FakeClient(["Hello", " world"], whitelabel="Swift")
    apex_client = FakeClient(["Hello", " world", " caveman"], whitelabel="Apex")

    monkeypatch.setattr(
        query_module, "get_client", _make_get_client(oracle_client, apex_client)
    )

    with TestClient(app) as tc:
        r = tc.post(
            "/api/query",
            json={
                "mode": "oracle",
                "query": "explain gravity",
                "models": ["Swift"],
                "primal_protocol": True,
            },
        )

    assert r.status_code == 200
    events = parse_sse(r.text)
    names = [e for e, _ in events]
    assert "primal" in names, f"Expected 'primal' in {names}"


def test_primal_false_does_not_emit_primal_event(
    monkeypatch: pytest.MonkeyPatch,
    _base_overrides: tuple,
) -> None:
    """primal_protocol=False (default): no `primal` event emitted."""
    oracle_client = FakeClient(["Hello", " world"], whitelabel="Swift")

    monkeypatch.setattr(
        query_module, "get_client", lambda _wl: oracle_client
    )

    with TestClient(app) as tc:
        r = tc.post(
            "/api/query",
            json={
                "mode": "oracle",
                "query": "explain gravity",
                "models": ["Swift"],
                "primal_protocol": False,
            },
        )

    assert r.status_code == 200
    events = parse_sse(r.text)
    names = [e for e, _ in events]
    assert "primal" not in names, f"Unexpected 'primal' in {names}"


def test_primal_event_has_nonempty_text(
    monkeypatch: pytest.MonkeyPatch,
    _base_overrides: tuple,
) -> None:
    """The `primal` event payload has a non-empty `text` field."""
    oracle_client = FakeClient(["Big", " answer"], whitelabel="Swift")
    apex_client = FakeClient(["Big", " answer", " cave"], whitelabel="Apex")

    monkeypatch.setattr(
        query_module, "get_client", _make_get_client(oracle_client, apex_client)
    )

    with TestClient(app) as tc:
        r = tc.post(
            "/api/query",
            json={
                "mode": "oracle",
                "query": "explain quantum",
                "models": ["Swift"],
                "primal_protocol": True,
            },
        )

    assert r.status_code == 200
    events = parse_sse(r.text)
    primal_events = [(e, d) for e, d in events if e == "primal"]
    assert len(primal_events) == 1, f"Expected exactly 1 primal event, got {primal_events}"
    _, payload = primal_events[0]
    assert isinstance(payload.get("text"), str), "primal payload must have 'text' str"
    assert len(payload["text"]) > 0, "primal text must be non-empty"


def test_primal_ordering_hex_done_before_primal_before_done(
    monkeypatch: pytest.MonkeyPatch,
    _base_overrides: tuple,
) -> None:
    """Event order: hex_done → primal → done (when primal=True)."""
    oracle_client = FakeClient(["Answer"], whitelabel="Swift")
    apex_client = FakeClient(["Cave", " answer"], whitelabel="Apex")

    monkeypatch.setattr(
        query_module, "get_client", _make_get_client(oracle_client, apex_client)
    )

    with TestClient(app) as tc:
        r = tc.post(
            "/api/query",
            json={
                "mode": "oracle",
                "query": "what is fire",
                "models": ["Swift"],
                "primal_protocol": True,
            },
        )

    assert r.status_code == 200
    events = parse_sse(r.text)
    names = [e for e, _ in events]

    assert "hex_done" in names
    assert "primal" in names
    assert "done" in names

    hex_done_idx = names.index("hex_done")
    primal_idx = names.index("primal")
    done_idx = names.index("done")

    assert hex_done_idx < primal_idx < done_idx, (
        f"Expected hex_done ({hex_done_idx}) < primal ({primal_idx}) < done ({done_idx})"
    )


def test_primal_failure_emits_error_then_done(
    monkeypatch: pytest.MonkeyPatch,
    _base_overrides: tuple,
) -> None:
    """If Apex primal pass raises, an error event is emitted but done still fires."""

    oracle_client = FakeClient(["Answer"], whitelabel="Swift")

    # Apex client that always raises when called
    class _FailingApexClient:
        whitelabel = "Apex"

        async def stream(self, messages, cache_key=None, tools=None):
            raise RuntimeError("apex unavailable")
            # Make it a proper async generator by yielding nothing
            return
            yield  # noqa: unreachable

    monkeypatch.setattr(
        query_module, "get_client", _make_get_client(oracle_client, _FailingApexClient())
    )

    with TestClient(app) as tc:
        r = tc.post(
            "/api/query",
            json={
                "mode": "oracle",
                "query": "what is fire",
                "models": ["Swift"],
                "primal_protocol": True,
            },
        )

    assert r.status_code == 200
    events = parse_sse(r.text)
    names = [e for e, _ in events]

    # error event from primal failure
    assert "error" in names, f"Expected 'error' in {names}"
    # done still emitted at end
    assert names[-1] == "done", f"Expected 'done' to be last, got {names[-1]}"
    # no primal event since it failed
    assert "primal" not in names, f"'primal' should not appear after failure, got {names}"
