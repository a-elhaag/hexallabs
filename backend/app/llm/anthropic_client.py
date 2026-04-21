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
