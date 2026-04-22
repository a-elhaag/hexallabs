from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from anthropic import AsyncAnthropic

from app.llm.base import LLMClient, Message, StreamChunk, ToolCall


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

    async def stream(
        self,
        messages: list[Message],
        cache_key: str | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[StreamChunk]:
        system_blocks: list[dict[str, Any]] = []
        api_messages: list[dict[str, Any]] = []

        for m in messages:
            if m.role == "system":
                block: dict[str, Any] = {"type": "text", "text": m.content}
                if m.cache:
                    block["cache_control"] = {"type": "ephemeral"}
                system_blocks.append(block)
            elif m.role == "assistant":
                content: list[dict[str, Any]] = []
                if m.content:
                    content.append({"type": "text", "text": m.content})
                for tc in m.tool_calls:
                    content.append({
                        "type": "tool_use",
                        "id": tc.id,
                        "name": tc.name,
                        "input": tc.input,
                    })
                api_messages.append({"role": "assistant", "content": content})
            elif m.role == "tool":
                # Tool result — Anthropic expects role="user" with tool_result content
                api_messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": m.tool_use_id,
                        "content": m.content,
                    }],
                })
            else:
                api_messages.append({"role": m.role, "content": m.content})

        kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": self._max_tokens,
            "messages": api_messages,
        }
        if system_blocks:
            kwargs["system"] = system_blocks
        if tools:
            kwargs["tools"] = tools

        # Buffer tool_use blocks — they arrive as a stream of input_json_delta events
        # between content_block_start (type=tool_use) and content_block_stop.
        pending_tool: dict[str, Any] | None = None
        pending_input_chunks: list[str] = []
        stop_reason: str | None = None

        stream_ctx = self._sdk.messages.stream(**kwargs)
        async with stream_ctx as stream:
            async for event in stream:
                etype = getattr(event, "type", None)

                if etype == "content_block_start":
                    block_obj = getattr(event, "content_block", None)
                    if block_obj and getattr(block_obj, "type", None) == "tool_use":
                        pending_tool = {
                            "id": block_obj.id,
                            "name": block_obj.name,
                        }
                        pending_input_chunks = []

                elif etype == "content_block_delta":
                    ev: Any = event
                    delta_obj = ev.delta
                    delta_type = getattr(delta_obj, "type", None)

                    if delta_type == "text_delta":
                        text = getattr(delta_obj, "text", None)
                        if text:
                            yield StreamChunk(delta=text)
                    elif delta_type == "input_json_delta":
                        partial = getattr(delta_obj, "partial_json", "")
                        if partial:
                            pending_input_chunks.append(partial)

                elif etype == "content_block_stop":
                    if pending_tool is not None:
                        raw_input = "".join(pending_input_chunks)
                        try:
                            parsed_input = json.loads(raw_input) if raw_input else {}
                        except json.JSONDecodeError:
                            parsed_input = {"_raw": raw_input}
                        yield StreamChunk(
                            tool_call=ToolCall(
                                id=pending_tool["id"],
                                name=pending_tool["name"],
                                input=parsed_input,
                            )
                        )
                        pending_tool = None
                        pending_input_chunks = []

                elif etype == "message_delta":
                    ev2: Any = event
                    delta2 = getattr(ev2, "delta", None)
                    if delta2:
                        sr = getattr(delta2, "stop_reason", None)
                        if sr:
                            stop_reason = sr
                        out_tokens = getattr(ev2, "usage", None)
                        if out_tokens:
                            yield StreamChunk(
                                total_tokens=getattr(out_tokens, "output_tokens", None)
                            )

                elif etype == "message_start":
                    ev3: Any = event
                    usage = getattr(getattr(ev3, "message", None), "usage", None)
                    if usage:
                        cached = getattr(usage, "cache_read_input_tokens", None)
                        if cached:
                            yield StreamChunk(cached_tokens=cached)

        if stop_reason:
            yield StreamChunk(stop_reason=stop_reason)
