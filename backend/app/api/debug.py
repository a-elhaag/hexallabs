from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.llm.base import Message
from app.llm.factory import get_client

router = APIRouter(prefix="/api/debug", tags=["debug"])


class InvokeRequest(BaseModel):
    model: str
    query: str
    system: str | None = None


@router.post("/invoke")
async def invoke(req: InvokeRequest) -> StreamingResponse:
    client = get_client(req.model)
    messages: list[Message] = []
    if req.system:
        messages.append(Message(role="system", content=req.system, cache=True))
    messages.append(Message(role="user", content=req.query))

    async def _gen() -> AsyncIterator[bytes]:
        async for chunk in client.stream(messages):
            yield chunk.delta.encode("utf-8")

    return StreamingResponse(_gen(), media_type="text/plain")
