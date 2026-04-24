# FastAPI Skeleton + LLM Client Factory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up FastAPI backend with provider-aware LLM client factory (Anthropic Console for Apex/Pulse, Azure AI Foundry for Swift/Prism/Depth/Atlas/Horizon), including health check and a debug invoke endpoint. No DB, no SSE, no Council logic yet — those are later plans.

**Architecture:** Single FastAPI app under `backend/`. `app/llm/` holds provider abstraction: `LLMClient` Protocol, `AnthropicClient`, `AzureFoundryClient`, and a `get_client(whitelabel)` factory that reads `MODEL_<NAME>` + `MODEL_<NAME>_PROVIDER` env vars. Caller code never imports Anthropic or OpenAI SDKs directly — only the factory.

**Tech Stack:** Python 3.13, uv, FastAPI, uvicorn, pydantic-settings, anthropic SDK, openai SDK (pointed at Azure), azure-identity (DefaultAzureCredential), ruff, mypy (strict), pytest, pytest-asyncio, httpx.AsyncClient.

---

## File Structure

```
backend/
  pyproject.toml                # uv project, py 3.13, all deps
  .python-version               # 3.13
  uv.lock                       # generated
  .env.example                  # template, committed
  app/
    __init__.py
    main.py                     # FastAPI app, /health, debug router mount
    config.py                   # Settings (pydantic-settings)
    llm/
      __init__.py
      base.py                   # LLMClient Protocol + Message type
      anthropic_client.py       # Claude via anthropic SDK, streaming
      azure_client.py           # Azure Foundry via openai SDK + Entra, streaming
      factory.py                # get_client(whitelabel) -> LLMClient
    api/
      __init__.py
      debug.py                  # POST /api/debug/invoke (non-SSE plain stream)
  tests/
    __init__.py
    conftest.py                 # httpx AsyncClient fixture, mock creds
    test_health.py
    test_config.py
    test_anthropic_client.py    # mocked Anthropic SDK
    test_azure_client.py        # mocked OpenAI SDK
    test_factory.py
    test_debug_invoke.py        # mocked factory
  README.md                     # run instructions
```

Single responsibility per file. Clients mirror each other. Factory is thin (~20 lines).

---

## Task 1: Initialize uv project

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/.python-version`
- Create: `backend/.gitignore`

- [ ] **Step 1: Verify uv installed**

Run: `uv --version`
Expected: `uv 0.5.x` or newer. If missing: `curl -LsSf https://astral.sh/uv/install.sh | sh`

- [ ] **Step 2: Create project**

Run:
```bash
cd backend
uv init --python 3.13 --no-readme --no-workspace .
```

Expected: creates `pyproject.toml`, `.python-version`, `main.py` (will delete/replace), `hello.py` (will delete).

- [ ] **Step 3: Remove scaffolding**

Run:
```bash
rm backend/main.py backend/hello.py 2>/dev/null || true
```

- [ ] **Step 4: Replace `backend/pyproject.toml`**

```toml
[project]
name = "hexal-backend"
version = "0.1.0"
description = "Hexal-LM FastAPI backend"
requires-python = ">=3.13"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "pydantic-settings>=2.6.0",
    "anthropic>=0.39.0",
    "openai>=1.54.0",
    "azure-identity>=1.19.0",
    "httpx>=0.27.0",
]

[dependency-groups]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "ruff>=0.7.0",
    "mypy>=1.13.0",
]

[tool.ruff]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM", "ASYNC"]

[tool.mypy]
python_version = "3.13"
strict = true
packages = ["app"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 5: Create `backend/.gitignore`**

```
.venv/
__pycache__/
*.pyc
.pytest_cache/
.mypy_cache/
.ruff_cache/
.env
!.env.example
```

- [ ] **Step 6: Install deps**

Run: `cd backend && uv sync`
Expected: creates `.venv/`, `uv.lock`. No errors.

- [ ] **Step 7: Commit**

```bash
git add backend/pyproject.toml backend/.python-version backend/.gitignore backend/uv.lock
git commit -m "chore(backend): init uv project, python 3.13, core deps"
```

---

## Task 2: Settings + .env.example

**Files:**
- Create: `backend/app/__init__.py`
- Create: `backend/app/config.py`
- Create: `backend/.env.example`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/test_config.py`

- [ ] **Step 1: Create `backend/.env.example`**

```
# Anthropic Console (Apex, Pulse)
ANTHROPIC_API_KEY=sk-ant-...

# Azure AI Foundry (Swift, Prism, Depth, Atlas, Horizon)
AZURE_FOUNDRY_ENDPOINT=https://your-resource.services.ai.azure.com
AZURE_FOUNDRY_API_VERSION=2024-10-21
AZURE_CLIENT_ID=
AZURE_TENANT_ID=
AZURE_CLIENT_SECRET=

# White-label -> real deployment/model
MODEL_APEX=claude-opus-4-7
MODEL_APEX_PROVIDER=anthropic

MODEL_PULSE=claude-sonnet-4-6
MODEL_PULSE_PROVIDER=anthropic

MODEL_SWIFT=gpt-4o-mini
MODEL_SWIFT_PROVIDER=azure

MODEL_PRISM=o3-mini
MODEL_PRISM_PROVIDER=azure

MODEL_DEPTH=gpt-5
MODEL_DEPTH_PROVIDER=azure

MODEL_ATLAS=DeepSeek-V3.1
MODEL_ATLAS_PROVIDER=azure

MODEL_HORIZON=gpt-4.1
MODEL_HORIZON_PROVIDER=azure
```

- [ ] **Step 2: Write failing test `backend/tests/test_config.py`**

```python
from app.config import Settings

def test_settings_loads_whitelabel_map(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("AZURE_FOUNDRY_ENDPOINT", "https://x.services.ai.azure.com")
    monkeypatch.setenv("MODEL_APEX", "claude-opus-4-7")
    monkeypatch.setenv("MODEL_APEX_PROVIDER", "anthropic")
    monkeypatch.setenv("MODEL_SWIFT", "gpt-4o-mini")
    monkeypatch.setenv("MODEL_SWIFT_PROVIDER", "azure")
    s = Settings()
    assert s.models["Apex"] == "claude-opus-4-7"
    assert s.providers["Apex"] == "anthropic"
    assert s.models["Swift"] == "gpt-4o-mini"
    assert s.providers["Swift"] == "azure"

def test_settings_rejects_unknown_provider(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("AZURE_FOUNDRY_ENDPOINT", "https://x.services.ai.azure.com")
    monkeypatch.setenv("MODEL_APEX", "x")
    monkeypatch.setenv("MODEL_APEX_PROVIDER", "bedrock")
    import pytest
    with pytest.raises(ValueError):
        Settings()
```

Create `backend/app/__init__.py` and `backend/tests/__init__.py` as empty files.

- [ ] **Step 3: Run test, verify fail**

Run: `cd backend && uv run pytest tests/test_config.py -v`
Expected: FAIL (ModuleNotFoundError: app.config).

- [ ] **Step 4: Implement `backend/app/config.py`**

```python
from __future__ import annotations

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

WHITELABELS = ("Apex", "Pulse", "Swift", "Prism", "Depth", "Atlas", "Horizon")
VALID_PROVIDERS = {"anthropic", "azure"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
        case_sensitive=False,
    )

    anthropic_api_key: str = Field(alias="ANTHROPIC_API_KEY")
    azure_foundry_endpoint: str = Field(alias="AZURE_FOUNDRY_ENDPOINT")
    azure_foundry_api_version: str = Field(
        default="2024-10-21", alias="AZURE_FOUNDRY_API_VERSION"
    )

    models: dict[str, str] = Field(default_factory=dict)
    providers: dict[str, str] = Field(default_factory=dict)

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        import os

        for name in WHITELABELS:
            deploy = os.getenv(f"MODEL_{name.upper()}")
            prov = os.getenv(f"MODEL_{name.upper()}_PROVIDER")
            if deploy and prov:
                if prov not in VALID_PROVIDERS:
                    raise ValueError(
                        f"MODEL_{name.upper()}_PROVIDER={prov!r} invalid. "
                        f"Allowed: {sorted(VALID_PROVIDERS)}"
                    )
                self.models[name] = deploy
                self.providers[name] = prov

    @field_validator("azure_foundry_endpoint")
    @classmethod
    def _strip_trailing_slash(cls, v: str) -> str:
        return v.rstrip("/")


def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
```

- [ ] **Step 5: Run test, verify pass**

Run: `cd backend && uv run pytest tests/test_config.py -v`
Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add backend/app/__init__.py backend/app/config.py backend/tests/__init__.py backend/tests/test_config.py backend/.env.example
git commit -m "feat(backend): settings + whitelabel->provider env map"
```

---

## Task 3: FastAPI app + /health

**Files:**
- Create: `backend/app/main.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_health.py`

- [ ] **Step 1: Write failing test `backend/tests/test_health.py`**

```python
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_returns_ok():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
```

- [ ] **Step 2: Create `backend/tests/conftest.py`**

```python
import os

import pytest


@pytest.fixture(autouse=True)
def _default_env(monkeypatch: pytest.MonkeyPatch) -> None:
    defaults = {
        "ANTHROPIC_API_KEY": "sk-test",
        "AZURE_FOUNDRY_ENDPOINT": "https://test.services.ai.azure.com",
        "MODEL_APEX": "claude-opus-4-7",
        "MODEL_APEX_PROVIDER": "anthropic",
        "MODEL_SWIFT": "gpt-4o-mini",
        "MODEL_SWIFT_PROVIDER": "azure",
    }
    for k, v in defaults.items():
        if not os.getenv(k):
            monkeypatch.setenv(k, v)
```

- [ ] **Step 3: Run test, verify fail**

Run: `cd backend && uv run pytest tests/test_health.py -v`
Expected: FAIL (ModuleNotFoundError: app.main).

- [ ] **Step 4: Implement `backend/app/main.py`**

```python
from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(title="Hexal-LM Backend", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 5: Run test, verify pass**

Run: `cd backend && uv run pytest tests/test_health.py -v`
Expected: 1 passed.

- [ ] **Step 6: Sanity — boot server**

Run: `cd backend && uv run uvicorn app.main:app --reload --port 8000 &`
Then: `curl http://localhost:8000/health`
Expected: `{"status":"ok"}`
Kill: `kill %1`

- [ ] **Step 7: Commit**

```bash
git add backend/app/main.py backend/tests/conftest.py backend/tests/test_health.py
git commit -m "feat(backend): FastAPI app + /health endpoint"
```

---

## Task 4: LLMClient Protocol + base types

**Files:**
- Create: `backend/app/llm/__init__.py`
- Create: `backend/app/llm/base.py`

- [ ] **Step 1: Create `backend/app/llm/__init__.py`** (empty)

- [ ] **Step 2: Implement `backend/app/llm/base.py`**

```python
from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Literal, Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class Message:
    role: Literal["system", "user", "assistant"]
    content: str
    cache: bool = False  # whether to mark cacheable (Anthropic cache_control)


@dataclass(frozen=True, slots=True)
class StreamChunk:
    delta: str
    cached_tokens: int | None = None  # final-chunk metadata; None per-token
    total_tokens: int | None = None


@runtime_checkable
class LLMClient(Protocol):
    whitelabel: str

    async def stream(self, messages: list[Message]) -> AsyncIterator[StreamChunk]:
        ...
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/llm/__init__.py backend/app/llm/base.py
git commit -m "feat(backend): LLMClient protocol + Message/StreamChunk types"
```

---

## Task 5: AnthropicClient (Apex, Pulse)

**Files:**
- Create: `backend/app/llm/anthropic_client.py`
- Create: `backend/tests/test_anthropic_client.py`

- [ ] **Step 1: Write failing test `backend/tests/test_anthropic_client.py`**

```python
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.llm.anthropic_client import AnthropicClient
from app.llm.base import Message


class _FakeStream:
    def __init__(self, deltas: list[str]) -> None:
        self._deltas = deltas

    async def __aenter__(self) -> "_FakeStream":
        return self

    async def __aexit__(self, *args: object) -> None:  # noqa: D401
        return None

    async def __aiter__(self) -> AsyncIterator[MagicMock]:
        for d in self._deltas:
            ev = MagicMock()
            ev.type = "content_block_delta"
            ev.delta.type = "text_delta"
            ev.delta.text = d
            yield ev
        final = MagicMock()
        final.type = "message_stop"
        yield final

    def get_final_message(self) -> MagicMock:  # not used by client; placeholder
        return MagicMock()


@pytest.mark.asyncio
async def test_anthropic_client_streams_deltas() -> None:
    deltas = ["Hello", " ", "world"]
    fake = _FakeStream(deltas)

    mock_messages = MagicMock()
    mock_messages.stream = MagicMock(return_value=fake)
    mock_sdk = MagicMock()
    mock_sdk.messages = mock_messages

    client = AnthropicClient(
        whitelabel="Apex",
        api_key="sk-test",
        model="claude-opus-4-7",
        sdk=mock_sdk,
    )

    out = []
    async for chunk in client.stream([Message(role="user", content="hi")]):
        out.append(chunk.delta)

    assert "".join(out) == "Hello world"


@pytest.mark.asyncio
async def test_anthropic_client_marks_cache_control() -> None:
    captured: dict[str, object] = {}

    def _capture_stream(**kwargs: object):  # noqa: ANN401
        captured.update(kwargs)
        return _FakeStream([])

    mock_sdk = MagicMock()
    mock_sdk.messages.stream = _capture_stream

    client = AnthropicClient(
        whitelabel="Apex",
        api_key="sk-test",
        model="claude-opus-4-7",
        sdk=mock_sdk,
    )

    msgs = [
        Message(role="system", content="RUBRIC", cache=True),
        Message(role="user", content="query"),
    ]
    async for _ in client.stream(msgs):
        pass

    system = captured["system"]
    assert isinstance(system, list)
    assert system[0]["cache_control"] == {"type": "ephemeral"}
    assert system[0]["text"] == "RUBRIC"
    user_messages = captured["messages"]
    assert user_messages == [{"role": "user", "content": "query"}]
```

- [ ] **Step 2: Run test, verify fail**

Run: `cd backend && uv run pytest tests/test_anthropic_client.py -v`
Expected: FAIL (ModuleNotFoundError).

- [ ] **Step 3: Implement `backend/app/llm/anthropic_client.py`**

```python
from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from anthropic import AsyncAnthropic

from app.llm.base import LLMClient, Message, StreamChunk


class AnthropicClient(LLMClient):
    def __init__(
        self,
        whitelabel: str,
        api_key: str,
        model: str,
        sdk: Any | None = None,
        max_tokens: int = 4096,
    ) -> None:
        self.whitelabel = whitelabel
        self._model = model
        self._max_tokens = max_tokens
        self._sdk = sdk if sdk is not None else AsyncAnthropic(api_key=api_key)

    async def stream(self, messages: list[Message]) -> AsyncIterator[StreamChunk]:
        system_blocks: list[dict[str, Any]] = []
        user_messages: list[dict[str, Any]] = []
        for m in messages:
            if m.role == "system":
                block: dict[str, Any] = {"type": "text", "text": m.content}
                if m.cache:
                    block["cache_control"] = {"type": "ephemeral"}
                system_blocks.append(block)
            else:
                user_messages.append({"role": m.role, "content": m.content})

        kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": self._max_tokens,
            "messages": user_messages,
        }
        if system_blocks:
            kwargs["system"] = system_blocks

        stream_ctx = self._sdk.messages.stream(**kwargs)
        async with stream_ctx as stream:
            async for event in stream:
                etype = getattr(event, "type", None)
                if etype == "content_block_delta":
                    delta = getattr(event.delta, "text", None)
                    if delta:
                        yield StreamChunk(delta=delta)
```

- [ ] **Step 4: Run test, verify pass**

Run: `cd backend && uv run pytest tests/test_anthropic_client.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/llm/anthropic_client.py backend/tests/test_anthropic_client.py
git commit -m "feat(backend): AnthropicClient with cache_control support"
```

---

## Task 6: AzureFoundryClient (Swift/Prism/Depth/Atlas/Horizon)

**Files:**
- Create: `backend/app/llm/azure_client.py`
- Create: `backend/tests/test_azure_client.py`

- [ ] **Step 1: Write failing test `backend/tests/test_azure_client.py`**

```python
from collections.abc import AsyncIterator
from unittest.mock import MagicMock

import pytest

from app.llm.azure_client import AzureFoundryClient
from app.llm.base import Message


class _AsyncIter:
    def __init__(self, items: list[MagicMock]) -> None:
        self._items = items

    def __aiter__(self) -> AsyncIterator[MagicMock]:
        async def gen() -> AsyncIterator[MagicMock]:
            for i in self._items:
                yield i

        return gen()


def _chunk(text: str | None) -> MagicMock:
    c = MagicMock()
    choice = MagicMock()
    choice.delta.content = text
    c.choices = [choice]
    return c


@pytest.mark.asyncio
async def test_azure_client_streams_deltas() -> None:
    chunks = [_chunk("Hello"), _chunk(" "), _chunk("world"), _chunk(None)]

    mock_sdk = MagicMock()

    async def _create(**kwargs: object):  # noqa: ANN401
        return _AsyncIter(chunks)

    mock_sdk.chat.completions.create = _create

    client = AzureFoundryClient(
        whitelabel="Swift",
        endpoint="https://test.services.ai.azure.com",
        api_version="2024-10-21",
        deployment="gpt-4o-mini",
        sdk=mock_sdk,
    )

    out = []
    async for chunk in client.stream([Message(role="user", content="hi")]):
        out.append(chunk.delta)

    assert "".join(out) == "Hello world"


@pytest.mark.asyncio
async def test_azure_client_passes_prompt_cache_key() -> None:
    captured: dict[str, object] = {}

    async def _create(**kwargs: object):  # noqa: ANN401
        captured.update(kwargs)
        return _AsyncIter([])

    mock_sdk = MagicMock()
    mock_sdk.chat.completions.create = _create

    client = AzureFoundryClient(
        whitelabel="Swift",
        endpoint="https://test.services.ai.azure.com",
        api_version="2024-10-21",
        deployment="gpt-4o-mini",
        sdk=mock_sdk,
    )

    async for _ in client.stream(
        [Message(role="system", content="RUBRIC"), Message(role="user", content="q")],
        cache_key="session-123",
    ):
        pass

    assert captured["model"] == "gpt-4o-mini"
    assert captured["stream"] is True
    assert captured["extra_body"] == {"prompt_cache_key": "session-123"}
    assert captured["messages"] == [
        {"role": "system", "content": "RUBRIC"},
        {"role": "user", "content": "q"},
    ]
```

- [ ] **Step 2: Run test, verify fail**

Run: `cd backend && uv run pytest tests/test_azure_client.py -v`
Expected: FAIL (ModuleNotFoundError).

- [ ] **Step 3: Implement `backend/app/llm/azure_client.py`**

```python
from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AsyncAzureOpenAI

from app.llm.base import LLMClient, Message, StreamChunk


class AzureFoundryClient(LLMClient):
    def __init__(
        self,
        whitelabel: str,
        endpoint: str,
        api_version: str,
        deployment: str,
        sdk: Any | None = None,
    ) -> None:
        self.whitelabel = whitelabel
        self._deployment = deployment
        if sdk is not None:
            self._sdk = sdk
        else:
            token_provider = get_bearer_token_provider(
                DefaultAzureCredential(), "https://ai.azure.com/.default"
            )
            self._sdk = AsyncAzureOpenAI(
                azure_endpoint=endpoint,
                api_version=api_version,
                azure_ad_token_provider=token_provider,
            )

    async def stream(
        self, messages: list[Message], cache_key: str | None = None
    ) -> AsyncIterator[StreamChunk]:
        payload: list[dict[str, str]] = [{"role": m.role, "content": m.content} for m in messages]
        kwargs: dict[str, Any] = {
            "model": self._deployment,
            "messages": payload,
            "stream": True,
        }
        if cache_key:
            kwargs["extra_body"] = {"prompt_cache_key": cache_key}

        stream = await self._sdk.chat.completions.create(**kwargs)
        async for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta.content
            if delta:
                yield StreamChunk(delta=delta)
```

- [ ] **Step 4: Run test, verify pass**

Run: `cd backend && uv run pytest tests/test_azure_client.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/llm/azure_client.py backend/tests/test_azure_client.py
git commit -m "feat(backend): AzureFoundryClient via OpenAI SDK + Entra ID"
```

---

## Task 7: Factory

**Files:**
- Create: `backend/app/llm/factory.py`
- Create: `backend/tests/test_factory.py`

- [ ] **Step 1: Write failing test `backend/tests/test_factory.py`**

```python
import pytest

from app.config import Settings
from app.llm.anthropic_client import AnthropicClient
from app.llm.azure_client import AzureFoundryClient
from app.llm.factory import get_client


def _settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


def test_factory_returns_anthropic_for_apex() -> None:
    client = get_client("Apex", settings=_settings())
    assert isinstance(client, AnthropicClient)
    assert client.whitelabel == "Apex"


def test_factory_returns_azure_for_swift() -> None:
    client = get_client("Swift", settings=_settings())
    assert isinstance(client, AzureFoundryClient)
    assert client.whitelabel == "Swift"


def test_factory_unknown_whitelabel_raises() -> None:
    with pytest.raises(KeyError):
        get_client("Bogus", settings=_settings())
```

- [ ] **Step 2: Run test, verify fail**

Run: `cd backend && uv run pytest tests/test_factory.py -v`
Expected: FAIL (ModuleNotFoundError).

- [ ] **Step 3: Implement `backend/app/llm/factory.py`**

```python
from __future__ import annotations

from functools import lru_cache

from app.config import Settings, get_settings
from app.llm.anthropic_client import AnthropicClient
from app.llm.azure_client import AzureFoundryClient
from app.llm.base import LLMClient


def get_client(whitelabel: str, settings: Settings | None = None) -> LLMClient:
    s = settings or _cached_settings()
    if whitelabel not in s.models:
        raise KeyError(f"Unknown white-label {whitelabel!r}. Known: {sorted(s.models)}")
    provider = s.providers[whitelabel]
    model = s.models[whitelabel]

    if provider == "anthropic":
        return AnthropicClient(
            whitelabel=whitelabel,
            api_key=s.anthropic_api_key,
            model=model,
        )
    if provider == "azure":
        return AzureFoundryClient(
            whitelabel=whitelabel,
            endpoint=s.azure_foundry_endpoint,
            api_version=s.azure_foundry_api_version,
            deployment=model,
        )
    raise ValueError(f"Unsupported provider {provider!r} for {whitelabel}")


@lru_cache(maxsize=1)
def _cached_settings() -> Settings:
    return get_settings()
```

- [ ] **Step 4: Run test, verify pass**

Run: `cd backend && uv run pytest tests/test_factory.py -v`
Expected: 3 passed.

Note: AzureFoundryClient construction triggers `DefaultAzureCredential` lookup but does not call Azure until `.stream()` runs. Test should pass without real creds.

- [ ] **Step 5: Commit**

```bash
git add backend/app/llm/factory.py backend/tests/test_factory.py
git commit -m "feat(backend): LLM factory routes whitelabel -> provider client"
```

---

## Task 8: Debug invoke endpoint

**Files:**
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/debug.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_debug_invoke.py`

- [ ] **Step 1: Write failing test `backend/tests/test_debug_invoke.py`**

```python
from collections.abc import AsyncIterator
from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.llm.base import Message, StreamChunk
from app.main import app


class _FakeClient:
    whitelabel = "Apex"

    async def stream(self, messages: list[Message]) -> AsyncIterator[StreamChunk]:
        yield StreamChunk(delta="Hello")
        yield StreamChunk(delta=" world")


@pytest.mark.asyncio
async def test_debug_invoke_streams_plain_text(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api import debug

    monkeypatch.setattr(debug, "get_client", lambda wl: _FakeClient())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        async with client.stream(
            "POST",
            "/api/debug/invoke",
            json={"model": "Apex", "query": "hi"},
        ) as resp:
            assert resp.status_code == 200
            body = b""
            async for b_chunk in resp.aiter_bytes():
                body += b_chunk

    assert body == b"Hello world"
```

- [ ] **Step 2: Run test, verify fail**

Run: `cd backend && uv run pytest tests/test_debug_invoke.py -v`
Expected: FAIL.

- [ ] **Step 3: Create `backend/app/api/__init__.py`** (empty)

- [ ] **Step 4: Implement `backend/app/api/debug.py`**

```python
from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.llm.base import Message
from app.llm.factory import get_client

router = APIRouter(prefix="/api/debug", tags=["debug"])


class InvokeRequest(BaseModel):
    model: str
    query: str
    system: str | None = None


@router.post("/invoke")
async def invoke(req: InvokeRequest) -> StreamingResponse:
    client = get_client(req.model)
    messages: list[Message] = []
    if req.system:
        messages.append(Message(role="system", content=req.system, cache=True))
    messages.append(Message(role="user", content=req.query))

    async def _gen() -> AsyncIterator[bytes]:
        async for chunk in client.stream(messages):
            yield chunk.delta.encode("utf-8")

    return StreamingResponse(_gen(), media_type="text/plain")
```

- [ ] **Step 5: Modify `backend/app/main.py`** — mount router

Replace file contents with:

```python
from __future__ import annotations

from fastapi import FastAPI

from app.api.debug import router as debug_router

app = FastAPI(title="Hexal-LM Backend", version="0.1.0")
app.include_router(debug_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 6: Run test, verify pass**

Run: `cd backend && uv run pytest tests/test_debug_invoke.py -v`
Expected: 1 passed.

- [ ] **Step 7: Commit**

```bash
git add backend/app/api backend/app/main.py backend/tests/test_debug_invoke.py
git commit -m "feat(backend): POST /api/debug/invoke streams via factory"
```

---

## Task 9: Full test suite + lint + types

**Files:** none new

- [ ] **Step 1: Run full pytest**

Run: `cd backend && uv run pytest -v`
Expected: all tests pass (2 config + 1 health + 2 anthropic + 2 azure + 3 factory + 1 debug = 11 passed).

- [ ] **Step 2: Run ruff**

Run: `cd backend && uv run ruff check . && uv run ruff format --check .`
Expected: no errors. If format fails: `uv run ruff format .` then re-check.

- [ ] **Step 3: Run mypy**

Run: `cd backend && uv run mypy`
Expected: `Success: no issues found`.

If failures on `azure-identity` or `openai` missing stubs: add to `pyproject.toml`:

```toml
[[tool.mypy.overrides]]
module = ["azure.identity.*"]
ignore_missing_imports = true
```

- [ ] **Step 4: Commit any fixups**

```bash
git add -u
git commit -m "chore(backend): lint + type clean"
```

---

## Task 10: README

**Files:**
- Create: `backend/README.md`

- [ ] **Step 1: Write `backend/README.md`**

```markdown
# Hexal-LM Backend

FastAPI + uv. Python 3.13.

## Setup

1. Copy env template:
   ```bash
   cp .env.example .env
   ```
   Fill: `ANTHROPIC_API_KEY`, `AZURE_FOUNDRY_ENDPOINT`, Entra creds (`AZURE_CLIENT_ID`/`AZURE_TENANT_ID`/`AZURE_CLIENT_SECRET`), and `MODEL_*` deployment names.

2. Install:
   ```bash
   uv sync
   ```

## Run

```bash
uv run uvicorn app.main:app --reload --port 8000
```

- Health: `GET http://localhost:8000/health`
- Debug invoke (streams plain text):
  ```bash
  curl -N -X POST http://localhost:8000/api/debug/invoke \
    -H "Content-Type: application/json" \
    -d '{"model":"Apex","query":"Say hi in 5 words."}'
  ```

## Test / lint / types

```bash
uv run pytest
uv run ruff check .
uv run mypy
```

## Architecture (this plan)

- `app/config.py` — env loader, whitelabel -> model + provider map
- `app/llm/base.py` — `LLMClient` Protocol
- `app/llm/anthropic_client.py` — Apex, Pulse (direct Anthropic Console)
- `app/llm/azure_client.py` — Swift/Prism/Depth/Atlas/Horizon (Azure Foundry + Entra)
- `app/llm/factory.py` — `get_client(whitelabel)` routes by provider
- `app/api/debug.py` — `/api/debug/invoke` for sanity testing
```

- [ ] **Step 2: Commit**

```bash
git add backend/README.md
git commit -m "docs(backend): README for skeleton"
```

---

## Self-Review Notes

**Spec coverage:** plan covers Build Order item #1 only (FastAPI skeleton). SSE, Council fan-out, peer review, Prompt Forge, Relay, Scout, Workflow, Prompt Lens, Primal, auth = later plans. Intentional.

**Provider split** (per hexal-model-router skill): Apex/Pulse = Anthropic direct; Swift/Prism/Depth/Atlas/Horizon = Azure Foundry. Factory enforces.

**Caching** (per hexal-caching-rules skill): AnthropicClient honors `Message.cache=True` via `cache_control: ephemeral`. AzureFoundryClient accepts optional `cache_key` param forwarded as `prompt_cache_key`. Real usage comes in Council/Apex synth plan.

**White-label** (per hexal-whitelabel-names skill): only white-labels in code. Real model names live in `.env` only.

**SSE** (per hexal-sse-contract skill): not implemented here — debug invoke uses plain `text/plain` stream on purpose to decouple from final SSE schema. SSE plan next.

**No placeholders:** every step has runnable code or exact commands.

---

## Next plans (not this one)

1. `2026-04-XX-oracle-sse.md` — SSE event schema impl + Oracle mode (single model)
2. `2026-04-XX-council-parallel.md` — fan-out N models, per-hex channels
3. `2026-04-XX-confidence-peer-review.md` — self-rate, peer critique, rescore
4. `2026-04-XX-apex-synth.md` — weighted synth w/ cache_control
5. Relay, Scout, Workflow, Prompt Lens, Primal Protocol, Auth
