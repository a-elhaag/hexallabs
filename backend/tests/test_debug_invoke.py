from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from app.llm.base import Message, StreamChunk
from app.main import app


class _FakeClient:
    whitelabel = "Apex"

    async def stream(self, messages: list[Message]) -> AsyncIterator[StreamChunk]:
        yield StreamChunk(delta="Hello")
        yield StreamChunk(delta=" world")


@pytest.mark.asyncio
async def test_debug_invoke_streams_plain_text(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api import debug

    monkeypatch.setattr(debug, "get_client", lambda wl: _FakeClient())

    transport = ASGITransport(app=app)
    async with (
        AsyncClient(transport=transport, base_url="http://test") as client,
        client.stream(
            "POST",
            "/api/debug/invoke",
            json={"model": "Apex", "query": "hi"},
        ) as resp,
    ):
        assert resp.status_code == 200
        body = b""
        async for b_chunk in resp.aiter_bytes():
            body += b_chunk

    assert body == b"Hello world"
