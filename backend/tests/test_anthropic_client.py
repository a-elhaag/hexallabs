from collections.abc import AsyncIterator
from unittest.mock import MagicMock

import pytest

from app.llm.anthropic_client import AnthropicClient
from app.llm.base import Message


class _FakeStream:
    def __init__(self, deltas: list[str]) -> None:
        self._deltas = deltas

    async def __aenter__(self) -> "_FakeStream":
        return self

    async def __aexit__(self, *args: object) -> None:
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

    def get_final_message(self) -> MagicMock:
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

    def _capture_stream(**kwargs: object):  # type: ignore[no-untyped-def]
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
