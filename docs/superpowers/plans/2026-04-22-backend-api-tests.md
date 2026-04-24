# Backend API Tests Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Write comprehensive integration tests for the entire FastAPI backend using fake LLM clients and fake DB sessions, covering Oracle, Relay, Scout, auth, health, and debug endpoints.

**Architecture:** All tests use `fastapi.testclient.TestClient` with `app.dependency_overrides` to inject fake auth, fake DB session, and monkeypatched `get_client`. No real DB or API calls. Tests are grouped by feature in separate test files.

**Tech Stack:** pytest, fastapi.testclient, monkeypatch, existing `_FakeClient` and `_FakeSession` patterns already in `tests/test_oracle_sse.py` and `tests/test_relay_sse.py`.

---

## File Map

- Modify: `tests/conftest.py` — add shared `_FakeSession`, `_FakeClient`, `_parse_sse` fixtures so tests don't duplicate them
- Modify: `tests/test_oracle_sse.py` — import shared fixtures from conftest instead of local copies (no logic change)
- Modify: `tests/test_relay_sse.py` — import shared fixtures from conftest instead of local copies (no logic change)
- Create: `tests/test_oracle_scout.py` — Oracle+Scout integration: `scout=force`, `scout=auto`, missing TAVILY_API_KEY edge cases
- Create: `tests/test_query_validation.py` — QueryRequest validation: bad mode, empty query, bad scout value
- Create: `tests/test_session_reuse.py` — Existing session_id: found/not-found/wrong-user cases
- Create: `tests/test_health_debug.py` — `/health` 200 and `/api/debug/invoke` endpoint tests (consolidating/extending existing test_health.py and test_debug_invoke.py)

---

### Task 1: Add shared fixtures to conftest.py

**Files:**
- Modify: `tests/conftest.py`

These fixtures are copy-pasted in `test_oracle_sse.py` and `test_relay_sse.py`. Centralise them so all new tests can use them without duplication.

- [ ] **Step 1: Read current conftest.py**

Verify contents match:
```python
import os
import pytest

@pytest.fixture(autouse=True)
def _default_env(monkeypatch: pytest.MonkeyPatch) -> None:
    defaults = {
        "ANTHROPIC_API_KEY": "sk-test",
        "AZURE_FOUNDRY_ENDPOINT": "https://test.services.ai.azure.com",
        "SUPABASE_URL": "https://test.supabase.co",
        "DATABASE_URL": "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres",
        "MODEL_APEX": "claude-opus-4-7",
        "MODEL_APEX_PROVIDER": "anthropic",
        "MODEL_SWIFT": "gpt-4o-mini",
        "MODEL_SWIFT_PROVIDER": "azure",
    }
    for k, v in defaults.items():
        if not os.getenv(k):
            monkeypatch.setenv(k, v)
```

- [ ] **Step 2: Add shared helpers to conftest.py**

Replace `tests/conftest.py` entirely with:

```python
from __future__ import annotations

import json
import os
import uuid
from collections.abc import AsyncIterator
from typing import Any

import pytest

from app.llm.base import Message, StreamChunk


@pytest.fixture(autouse=True)
def _default_env(monkeypatch: pytest.MonkeyPatch) -> None:
    defaults = {
        "ANTHROPIC_API_KEY": "sk-test",
        "AZURE_FOUNDRY_ENDPOINT": "https://test.services.ai.azure.com",
        "SUPABASE_URL": "https://test.supabase.co",
        "DATABASE_URL": "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres",
        "MODEL_APEX": "claude-opus-4-7",
        "MODEL_APEX_PROVIDER": "anthropic",
        "MODEL_SWIFT": "gpt-4o-mini",
        "MODEL_SWIFT_PROVIDER": "azure",
    }
    for k, v in defaults.items():
        if not os.getenv(k):
            monkeypatch.setenv(k, v)


class FakeClient:
    """Fake LLM client that emits configured deltas then a usage chunk."""

    def __init__(
        self,
        deltas: list[str],
        whitelabel: str = "Apex",
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
    ) -> AsyncIterator[StreamChunk]:
        for d in self._deltas:
            yield StreamChunk(delta=d)
        yield StreamChunk(delta="", total_tokens=self._total, cached_tokens=self._cached)


class FakeSession:
    """Minimal AsyncSession stand-in. Captures adds, no-op on flush/commit/rollback."""

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


def parse_sse(body: str) -> list[tuple[str, dict[str, object]]]:
    """Parse SSE body into list of (event_name, payload_dict) tuples."""
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
```

- [ ] **Step 3: Run existing tests to verify nothing broke**

```bash
cd /Users/anas/Projects/hexal-lm/backend && uv run pytest --tb=short -q
```

Expected: all 62 tests pass (conftest only adds helpers, no logic change).

- [ ] **Step 4: Commit**

```bash
git add tests/conftest.py
git commit -m "test: add shared FakeClient, FakeSession, parse_sse to conftest"
```

---

### Task 2: Oracle Scout tests

**Files:**
- Create: `tests/test_oracle_scout.py`

Test the `scout=force` and `scout=auto` paths through the oracle stream. These are not covered by existing `test_oracle_sse.py` or `test_oracle_scout_loop.py`.

- [ ] **Step 1: Write failing tests**

Create `tests/test_oracle_scout.py`:

```python
from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator
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

    with patch("app.api.query.execute_web_search", new=AsyncMock(return_value=fake_result)):
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

    # tool_call appears before first token
    tc_idx = names.index("tool_call")
    token_idx = names.index("token")
    assert tc_idx < token_idx


def test_scout_force_missing_tavily_key_emits_error(
    monkeypatch: pytest.MonkeyPatch,
    _base_overrides: tuple,
) -> None:
    """scout=force with no TAVILY_API_KEY → error event then done, no token events."""
    monkeypatch.setattr(query_module, "get_client", lambda _wl: FakeClient(["should not emit"]))
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    # Also clear it from settings cache
    from app.config import get_settings
    from functools import lru_cache

    with patch("app.api.query.get_settings") as mock_settings:
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
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")

    with patch(
        "app.api.query.execute_web_search",
        new=AsyncMock(side_effect=RuntimeError("network failure")),
    ):
        with patch("app.api.query.get_settings") as mock_settings:
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/anas/Projects/hexal-lm/backend && uv run pytest tests/test_oracle_scout.py -v --tb=short
```

Expected: tests fail (not implemented yet) or some pass if logic already exists.

- [ ] **Step 3: Run full suite to check no regressions**

```bash
uv run pytest --tb=short -q
```

Expected: existing 62 tests pass, new tests may fail.

- [ ] **Step 4: Commit**

```bash
git add tests/test_oracle_scout.py
git commit -m "test: add oracle scout (force/auto/off) integration tests"
```

---

### Task 3: QueryRequest validation tests

**Files:**
- Create: `tests/test_query_validation.py`

Test all validation paths on the `QueryRequest` model and the `/api/query` endpoint. Complements existing oracle/relay tests.

- [ ] **Step 1: Write failing tests**

Create `tests/test_query_validation.py`:

```python
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


def test_council_mode_returns_501(client: TestClient) -> None:
    r = client.post(
        "/api/query",
        json={"mode": "council", "query": "hi", "models": ["Apex", "Swift"]},
    )
    assert r.status_code == 501


def test_workflow_mode_returns_501(client: TestClient) -> None:
    r = client.post(
        "/api/query",
        json={"mode": "workflow", "query": "hi", "workflow_nodes": []},
    )
    assert r.status_code == 501


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
```

- [ ] **Step 2: Run to verify tests exist and most pass**

```bash
cd /Users/anas/Projects/hexal-lm/backend && uv run pytest tests/test_query_validation.py -v --tb=short
```

Expected: all pass (validation paths already implemented).

- [ ] **Step 3: Run full suite**

```bash
uv run pytest --tb=short -q
```

Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add tests/test_query_validation.py
git commit -m "test: add QueryRequest validation integration tests"
```

---

### Task 4: Session reuse tests

**Files:**
- Create: `tests/test_session_reuse.py`

Test the `session_id` param in `_open_session_and_query`: when a valid existing session is provided vs not found vs wrong user.

- [ ] **Step 1: Write failing tests**

Create `tests/test_session_reuse.py`:

```python
from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.api import query as query_module
from app.auth.middleware import get_current_user
from app.auth.models import AuthUser
from app.db.models import Session as SessionRow
from app.db.session import get_session
from app.llm.base import Message, StreamChunk
from app.main import app
from tests.conftest import FakeClient, FakeSession, parse_sse


class _FakeSessionWithLookup(FakeSession):
    """FakeSession that can return a pre-configured SessionRow on db.get()."""

    def __init__(self, session_row: SessionRow | None = None) -> None:
        super().__init__()
        self._session_row = session_row

    async def get(self, _model: object, _id: uuid.UUID) -> object | None:
        return self._session_row


def test_new_session_created_when_no_session_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No session_id → a new SessionRow is added to DB."""
    from app.db.models import Session as SessionRow

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
    from app.db.models import Session as SessionRow

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
    # No new session added — existing was reused
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
    """session_id exists but belongs to a different user → 404."""
    from app.db.models import Session as SessionRow

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
```

- [ ] **Step 2: Run to verify**

```bash
cd /Users/anas/Projects/hexal-lm/backend && uv run pytest tests/test_session_reuse.py -v --tb=short
```

Expected: all pass.

- [ ] **Step 3: Run full suite**

```bash
uv run pytest --tb=short -q
```

Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add tests/test_session_reuse.py
git commit -m "test: add session_id reuse/not-found/wrong-user tests"
```

---

### Task 5: Health and debug endpoint tests

**Files:**
- Modify: `tests/test_health.py` — verify existing tests still pass after we look at them
- Modify: `tests/test_debug_invoke.py` — verify existing tests still pass

These endpoints are already tested. This task verifies full coverage and adds any gaps.

- [ ] **Step 1: Read existing test_health.py**

```bash
cat /Users/anas/Projects/hexal-lm/backend/tests/test_health.py
```

- [ ] **Step 2: Read existing test_debug_invoke.py**

```bash
cat /Users/anas/Projects/hexal-lm/backend/tests/test_debug_invoke.py
```

- [ ] **Step 3: Run those tests**

```bash
cd /Users/anas/Projects/hexal-lm/backend && uv run pytest tests/test_health.py tests/test_debug_invoke.py -v --tb=short
```

Expected: all pass.

- [ ] **Step 4: Add coverage for missing cases in test_health.py**

If `test_health.py` only checks `{"status": "ok"}`, add check for response structure:

```python
def test_health_response_structure() -> None:
    """Health endpoint returns JSON with status key."""
    with TestClient(app) as tc:
        r = tc.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert "status" in body
    assert body["status"] == "ok"
```

Only add this test if it doesn't already exist.

- [ ] **Step 5: Run full suite**

```bash
cd /Users/anas/Projects/hexal-lm/backend && uv run pytest --tb=short -q
```

Expected: all tests pass, 70+ tests.

- [ ] **Step 6: Commit if any changes made**

```bash
git add tests/test_health.py tests/test_debug_invoke.py
git commit -m "test: verify health and debug endpoint coverage"
```

---

### Task 6: Final full suite run and coverage report

**Files:** none (verification only)

- [ ] **Step 1: Run full suite**

```bash
cd /Users/anas/Projects/hexal-lm/backend && uv run pytest --tb=short -v 2>&1 | tail -40
```

Expected: all tests pass with no failures.

- [ ] **Step 2: Run with coverage**

```bash
uv run pytest --tb=short -q --cov=app --cov-report=term-missing 2>&1 | tail -40
```

Note any uncovered lines in `app/api/query.py`, `app/relay/stream.py`, `app/sse/`.

- [ ] **Step 3: Report results**

Report total test count, pass rate, and any coverage gaps worth noting.
