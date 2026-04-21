from __future__ import annotations

import asyncio
import time
import uuid
from collections.abc import AsyncIterator
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AuthUser, get_current_user
from app.db import get_session
from app.db.models import Message as MessageRow
from app.db.models import Query as QueryRow
from app.db.models import Session as SessionRow
from app.llm.base import Message
from app.llm.factory import get_client
from app.sse import HEARTBEAT, SseEvent, format_event

router = APIRouter(prefix="/api", tags=["query"])

_HEARTBEAT_INTERVAL_SECONDS = 15.0


class QueryRequest(BaseModel):
    mode: Literal["council", "oracle", "relay", "workflow"]
    query: str = Field(min_length=1)
    models: list[str] = Field(default_factory=list)
    relay_chain: list[str] = Field(default_factory=list)
    workflow_nodes: list[dict[str, object]] = Field(default_factory=list)
    primal_protocol: bool = False
    scout: bool = False
    session_id: uuid.UUID | None = None


@router.post("/query")
async def query(
    req: QueryRequest,
    user: AuthUser = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_session),  # noqa: B008
) -> StreamingResponse:
    if req.mode != "oracle":
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"mode {req.mode!r} not yet implemented; only 'oracle' is wired",
        )
    if len(req.models) != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="oracle mode requires exactly one model in `models`",
        )

    whitelabel = req.models[0]
    try:
        client = get_client(whitelabel)
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    session_row, query_row = await _open_session_and_query(db, user.id, req, whitelabel)

    async def _stream() -> AsyncIterator[bytes]:
        async for chunk in _oracle_stream(db, client, query_row, req.query, whitelabel):
            yield chunk

    return StreamingResponse(
        _stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


async def _open_session_and_query(
    db: AsyncSession,
    user_id: uuid.UUID,
    req: QueryRequest,
    whitelabel: str,
) -> tuple[SessionRow, QueryRow]:
    if req.session_id is None:
        session_row = SessionRow(
            user_id=user_id,
            mode=req.mode,
            primal_protocol=req.primal_protocol,
            scout_enabled=req.scout,
        )
        db.add(session_row)
        await db.flush()
    else:
        existing = await db.get(SessionRow, req.session_id)
        if existing is None or existing.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="session not found"
            )
        session_row = existing

    query_row = QueryRow(
        session_id=session_row.id,
        user_id=user_id,
        raw_prompt=req.query,
        selected_models=[whitelabel],
        apex_model=None,
        status="streaming",
    )
    db.add(query_row)
    await db.flush()
    return session_row, query_row


async def _oracle_stream(
    db: AsyncSession,
    client: object,  # LLMClient Protocol — object for mypy's sake here
    query_row: QueryRow,
    prompt: str,
    whitelabel: str,
) -> AsyncIterator[bytes]:
    start_ns = time.monotonic_ns()
    session_id = str(query_row.session_id)

    yield format_event(
        SseEvent("session", {"session_id": session_id, "mode": "oracle"})
    )
    yield format_event(SseEvent("hex_start", {"hex": whitelabel}))

    messages = [Message(role="user", content=prompt)]
    collected: list[str] = []
    total_tokens: int | None = None
    cached_tokens: int | None = None

    try:
        async for sse_chunk in _with_heartbeat(
            _client_tokens(client, messages, whitelabel, collected)
        ):
            if isinstance(sse_chunk, _TokenCarry):
                total_tokens = sse_chunk.total_tokens
                cached_tokens = sse_chunk.cached_tokens
                continue
            yield sse_chunk
    except Exception as e:
        query_row.status = "error"
        query_row.error = str(e)[:500]
        yield format_event(
            SseEvent(
                "error",
                {"hex": whitelabel, "code": type(e).__name__, "message": str(e)[:500]},
            )
        )
        yield format_event(SseEvent("done", {"session_id": session_id, "duration_ms": 0}))
        return

    full_text = "".join(collected)

    db.add(
        MessageRow(
            query_id=query_row.id,
            role="model",
            model=whitelabel,
            content=full_text,
            tokens_in=None,
            tokens_out=total_tokens,
            stage="initial",
        )
    )
    query_row.status = "done"
    from sqlalchemy import func

    query_row.completed_at = func.now()

    # Oracle confidence is flat 10 — we don't self-rate a single model.
    yield format_event(
        SseEvent("confidence", {"hex": whitelabel, "score": 10, "stage": "initial"})
    )
    yield format_event(
        SseEvent(
            "hex_done",
            {
                "hex": whitelabel,
                "tokens": total_tokens or 0,
                "cached_tokens": cached_tokens or 0,
            },
        )
    )

    duration_ms = (time.monotonic_ns() - start_ns) // 1_000_000
    yield format_event(
        SseEvent("done", {"session_id": session_id, "duration_ms": duration_ms})
    )


# --- helpers -----------------------------------------------------------------


class _TokenCarry:
    """Sentinel passed from the token iterator to the main loop with final counts.

    Not emitted to the wire. Consumed by the Oracle handler after the stream ends.
    """

    __slots__ = ("cached_tokens", "total_tokens")

    def __init__(self, total_tokens: int | None, cached_tokens: int | None) -> None:
        self.total_tokens = total_tokens
        self.cached_tokens = cached_tokens


async def _client_tokens(
    client: object,
    messages: list[Message],
    whitelabel: str,
    collected: list[str],
) -> AsyncIterator[bytes | _TokenCarry]:
    total: int | None = None
    cached: int | None = None
    async for chunk in client.stream(messages):  # type: ignore[attr-defined]
        if chunk.delta:
            collected.append(chunk.delta)
            yield format_event(
                SseEvent("token", {"hex": whitelabel, "delta": chunk.delta})
            )
        if chunk.total_tokens is not None:
            total = chunk.total_tokens
        if chunk.cached_tokens is not None:
            cached = chunk.cached_tokens
    yield _TokenCarry(total_tokens=total, cached_tokens=cached)


async def _with_heartbeat(
    src: AsyncIterator[bytes | _TokenCarry],
) -> AsyncIterator[bytes | _TokenCarry]:
    """Yield from `src`, injecting a keep-alive comment every 15s of silence."""
    iterator = src.__aiter__()
    while True:
        get_next = asyncio.ensure_future(iterator.__anext__())
        try:
            while True:
                try:
                    item = await asyncio.wait_for(
                        asyncio.shield(get_next), timeout=_HEARTBEAT_INTERVAL_SECONDS
                    )
                except TimeoutError:
                    yield HEARTBEAT
                    continue
                yield item
                break
        except StopAsyncIteration:
            return
