from __future__ import annotations

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

    async def _create(**kwargs: object) -> _AsyncIter:
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

    async def _create(**kwargs: object) -> _AsyncIter:
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
