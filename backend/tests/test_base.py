from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

from app.llm.base import LLMClient, Message, StreamChunk


def test_message_fields() -> None:
    msg = Message(role="user", content="hello")
    assert msg.role == "user"
    assert msg.content == "hello"
    assert msg.cache is False


def test_message_cache_flag() -> None:
    msg = Message(role="system", content="sys", cache=True)
    assert msg.cache is True


def test_stream_chunk_fields() -> None:
    chunk = StreamChunk(delta="hi", cached_tokens=10, total_tokens=20)
    assert chunk.delta == "hi"
    assert chunk.cached_tokens == 10
    assert chunk.total_tokens == 20


def test_stream_chunk_optional_fields() -> None:
    chunk = StreamChunk(delta="x")
    assert chunk.cached_tokens is None
    assert chunk.total_tokens is None


def test_message_is_frozen() -> None:
    msg = Message(role="user", content="hi")
    with pytest.raises(AttributeError):
        msg.content = "changed"  # type: ignore[misc]


def test_stream_chunk_is_frozen() -> None:
    chunk = StreamChunk(delta="hi")
    with pytest.raises(AttributeError):
        chunk.delta = "changed"  # type: ignore[misc]


def test_llm_client_protocol_runtime_checkable() -> None:
    class FakeClient:
        whitelabel = "TestModel"

        async def stream(self, messages: list[Message]) -> AsyncIterator[StreamChunk]:
            yield StreamChunk(delta="tok")

    assert isinstance(FakeClient(), LLMClient)


@pytest.mark.asyncio
async def test_llm_client_stream_yields_chunks() -> None:
    class FakeClient:
        whitelabel = "TestModel"

        async def stream(self, messages: list[Message]) -> AsyncIterator[StreamChunk]:
            yield StreamChunk(delta="tok")

    client = FakeClient()
    chunks = [chunk async for chunk in client.stream([])]
    assert len(chunks) == 1
    assert chunks[0].delta == "tok"
