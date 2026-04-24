from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class ToolCall:
    id: str
    name: str
    input: dict[str, Any]


@dataclass(frozen=True, slots=True)
class Message:
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    cache: bool = False
    tool_calls: tuple[ToolCall, ...] = field(default_factory=tuple)
    tool_use_id: str | None = None  # for role="tool" messages


@dataclass(frozen=True, slots=True)
class StreamChunk:
    delta: str = ""
    cached_tokens: int | None = None
    total_tokens: int | None = None
    tool_call: ToolCall | None = None
    stop_reason: str | None = None  # "tool_use" | "end_turn"


@runtime_checkable
class LLMClient(Protocol):
    whitelabel: str

    def stream(
        self,
        messages: list[Message],
        cache_key: str | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[StreamChunk]: ...
