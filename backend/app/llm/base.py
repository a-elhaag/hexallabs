from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Literal, Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class Message:
    role: Literal["system", "user", "assistant"]
    content: str
    cache: bool = False


@dataclass(frozen=True, slots=True)
class StreamChunk:
    delta: str
    cached_tokens: int | None = None
    total_tokens: int | None = None


@runtime_checkable
class LLMClient(Protocol):
    whitelabel: str

    async def stream(self, messages: list[Message]) -> AsyncIterator[StreamChunk]:
        ...
