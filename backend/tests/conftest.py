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
