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
