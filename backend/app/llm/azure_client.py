from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AsyncAzureOpenAI

from app.llm.base import LLMClient, Message, StreamChunk, ToolCall


class AzureFoundryClient(LLMClient):
    def __init__(
        self,
        whitelabel: str,
        endpoint: str,
        api_version: str,
        deployment: str,
        api_key: str | None = None,
        sdk: Any | None = None,
    ) -> None:
        self.whitelabel = whitelabel
        self._deployment = deployment
        if sdk is not None:
            self._sdk = sdk
        elif api_key:
            self._sdk = AsyncAzureOpenAI(
                azure_endpoint=endpoint,
                api_version=api_version,
                api_key=api_key,
            )
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
        self,
        messages: list[Message],
        cache_key: str | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[StreamChunk]:
        payload: list[dict[str, Any]] = []
        for m in messages:
            if m.role == "assistant":
                msg: dict[str, Any] = {"role": "assistant"}
                if m.content:
                    msg["content"] = m.content
                if m.tool_calls:
                    msg["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json.dumps(tc.input),
                            },
                        }
                        for tc in m.tool_calls
                    ]
                payload.append(msg)
            elif m.role == "tool":
                payload.append({
                    "role": "tool",
                    "tool_call_id": m.tool_use_id,
                    "content": m.content,
                })
            else:
                payload.append({"role": m.role, "content": m.content})

        kwargs: dict[str, Any] = {
            "model": self._deployment,
            "messages": payload,
            "stream": True,
        }
        if cache_key:
            kwargs["extra_body"] = {"prompt_cache_key": cache_key}
        if tools:
            kwargs["tools"] = tools

        # Accumulate tool_calls across streaming chunks — OpenAI sends them
        # in fragments keyed by index, joined on finish_reason=="tool_calls".
        pending: dict[int, dict[str, Any]] = {}
        stop_reason: str | None = None

        stream = await self._sdk.chat.completions.create(**kwargs)
        async for chunk in stream:
            if not chunk.choices:
                continue
            choice = chunk.choices[0]
            delta = choice.delta

            if delta.content:
                yield StreamChunk(delta=delta.content)

            if delta.tool_calls:
                for tc_delta in delta.tool_calls:
                    idx = tc_delta.index
                    if idx not in pending:
                        pending[idx] = {
                            "id": tc_delta.id or "",
                            "name": (tc_delta.function and tc_delta.function.name) or "",
                            "args_chunks": [],
                        }
                    elif tc_delta.id:
                        pending[idx]["id"] = tc_delta.id
                    if tc_delta.function and tc_delta.function.name:
                        pending[idx]["name"] = tc_delta.function.name
                    if tc_delta.function and tc_delta.function.arguments:
                        pending[idx]["args_chunks"].append(tc_delta.function.arguments)

            if choice.finish_reason:
                stop_reason = choice.finish_reason

        if pending:
            for tc_data in pending.values():
                raw_args = "".join(tc_data["args_chunks"])
                try:
                    parsed = json.loads(raw_args) if raw_args else {}
                except json.JSONDecodeError:
                    parsed = {"_raw": raw_args}
                yield StreamChunk(
                    tool_call=ToolCall(
                        id=tc_data["id"],
                        name=tc_data["name"],
                        input=parsed,
                    )
                )

        if stop_reason:
            yield StreamChunk(stop_reason=stop_reason)
