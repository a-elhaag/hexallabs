from __future__ import annotations

import time
import uuid
from collections.abc import AsyncIterator
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AuthUser, get_current_user
from app.billing.quota import QuotaService
from app.council.stream import _council_stream
from app.db import get_session
from app.db.models import Message as MessageRow
from app.db.models import Query as QueryRow
from app.db.models import Session as SessionRow
from app.db.models.user_quota import UserQuota
from app.llm.base import LLMClient
from app.llm.factory import get_client
from app.relay.stream import _relay_stream
from app.sse import SseEvent, _with_heartbeat, format_event
from app.synthesis.apex import _PRIMAL_SYSTEM
from app.tools.scout import scout_auto_tool_messages, scout_force
from app.workflow.executor import _workflow_stream

router = APIRouter(prefix="/api", tags=["query"])

_SSE_HEADERS = {
    "Cache-Control": "no-cache, no-transform",
    "X-Accel-Buffering": "no",
    "Connection": "keep-alive",
}

ScoutMode = Literal["off", "auto", "force"]


class QueryRequest(BaseModel):
    mode: Literal["council", "oracle", "relay", "workflow"]
    query: str = Field(min_length=1)
    models: list[str] = Field(default_factory=list)
    relay_chain: list[str] = Field(default_factory=list)
    workflow_nodes: list[dict[str, object]] = Field(default_factory=list)
    primal_protocol: bool = False
    scout: ScoutMode = "off"
    session_id: uuid.UUID | None = None

    @field_validator("scout", mode="before")
    @classmethod
    def _coerce_scout_bool(cls, v: object) -> str:
        if isinstance(v, bool):
            return "auto" if v else "off"
        return str(v)


@router.post("/query")
async def query(
    req: QueryRequest,
    user: AuthUser = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_session),  # noqa: B008
) -> StreamingResponse:
    # Quota check — must happen after auth, before streaming
    quota = await QuotaService.get_or_create(db, user.id)
    QuotaService.check(quota)

    if req.mode == "oracle":
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
            async for chunk in _oracle_stream(
                db, client, query_row, req.query, whitelabel, req.scout,
                primal=req.primal_protocol,
                quota=quota,
            ):
                yield chunk

        return StreamingResponse(
            _stream(),
            media_type="text/event-stream",
            headers=_SSE_HEADERS,
        )

    elif req.mode == "relay":
        if len(req.relay_chain) != 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="relay mode requires exactly two models in relay_chain",
            )

        wl_a, wl_b = req.relay_chain
        try:
            client_a = get_client(wl_a)
            client_b = get_client(wl_b)
            apex_client = get_client("Apex")
        except KeyError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

        session_row, query_row = await _open_session_and_query(db, user.id, req, wl_a)
        query_row.selected_models = [wl_a, wl_b]

        async def _relay() -> AsyncIterator[bytes]:
            async for chunk in _relay_stream(
                db, client_a, client_b, apex_client, query_row, req.query, wl_a, wl_b,
                scout=req.scout,
                quota=quota,
            ):
                yield chunk

        return StreamingResponse(
            _relay(),
            media_type="text/event-stream",
            headers=_SSE_HEADERS,
        )

    elif req.mode == "council":
        if len(req.models) < 2:
            raise HTTPException(
                status_code=422,
                detail="council mode requires at least 2 models",
            )

        try:
            clients = [get_client(wl) for wl in req.models]
            apex_client = get_client("Apex")
        except KeyError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

        session_row, query_row = await _open_session_and_query(
            db, user.id, req, req.models[0]
        )
        query_row.selected_models = list(req.models)
        query_row.apex_model = "Apex"

        async def _council() -> AsyncIterator[bytes]:
            async for chunk in _council_stream(
                db,
                clients,
                apex_client,
                query_row,
                req.query,
                list(req.models),
                primal=req.primal_protocol,
                scout=req.scout,
                quota=quota,
            ):
                yield chunk

        return StreamingResponse(
            _with_heartbeat(_council()),
            media_type="text/event-stream",
            headers=_SSE_HEADERS,
        )

    else:
        # req.mode == "workflow"
        if not req.workflow_nodes:
            raise HTTPException(
                status_code=422,
                detail="workflow mode requires workflow_nodes",
            )
        session_row, query_row = await _open_session_and_query(db, user.id, req, "workflow")

        async def _workflow() -> AsyncIterator[bytes]:
            async for chunk in _workflow_stream(
                db, query_row, req.query, req.workflow_nodes,
                scout=req.scout,
                quota=quota,
            ):
                yield chunk

        return StreamingResponse(
            _with_heartbeat(_workflow()),
            media_type="text/event-stream",
            headers=_SSE_HEADERS,
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
    client: object,
    query_row: QueryRow,
    prompt: str,
    whitelabel: str,
    scout: ScoutMode,
    *,
    primal: bool = False,
    quota: UserQuota | None = None,
) -> AsyncIterator[bytes]:
    from app.config import get_settings
    from app.llm.base import Message as LLMMessage

    settings = get_settings()
    start_ns = time.monotonic_ns()
    session_id = str(query_row.session_id)

    yield format_event(SseEvent("session", {"session_id": session_id, "mode": "oracle"}))
    yield format_event(SseEvent("hex_start", {"hex": whitelabel}))

    messages: list[LLMMessage] = []

    # Force mode: pre-execute search, inject as system context.
    if scout == "force":
        try:
            context_text, pre_result = await scout_force(prompt, settings)
        except ValueError:
            yield format_event(SseEvent(
                "error",
                {"hex": whitelabel, "code": "MissingConfig", "message": "TAVILY_API_KEY not set"},
            ))
            yield format_event(SseEvent("done", {"session_id": session_id, "duration_ms": 0}))
            return
        except Exception as e:
            yield format_event(SseEvent(
                "error",
                {"hex": whitelabel, "code": type(e).__name__, "message": str(e)[:500]},
            ))
            yield format_event(SseEvent("done", {"session_id": session_id, "duration_ms": 0}))
            return

        force_id = f"force_{uuid.uuid4().hex[:8]}"
        yield format_event(SseEvent("tool_call", {
            "hex": whitelabel,
            "id": force_id,
            "name": "web_search",
            "input": {"query": prompt},
            "forced": True,
        }))
        yield format_event(SseEvent("tool_result", {
            "hex": whitelabel,
            "id": force_id,
            "name": "web_search",
            "summary": pre_result.summary,
            "urls": pre_result.urls,
            "result_count": pre_result.result_count,
        }))

        messages.append(LLMMessage(role="system", content=context_text, cache=True))

    messages.append(LLMMessage(role="user", content=prompt))

    # Agentic loop — run up to scout_max_turns to handle tool calls.
    collected: list[str] = []
    token_counts: dict[str, int | None] = {"total": None, "cached": None}

    try:
        async for sse_bytes in scout_auto_tool_messages(
            client,
            messages,
            settings,
            whitelabel,
            with_tools=scout in ("auto", "force"),
            collected=collected,
            token_counts=token_counts,
        ):
            yield sse_bytes

    except Exception as e:
        query_row.status = "error"
        query_row.error = str(e)[:500]
        yield format_event(SseEvent(
            "error",
            {"hex": whitelabel, "code": type(e).__name__, "message": str(e)[:500]},
        ))
        yield format_event(SseEvent("done", {"session_id": session_id, "duration_ms": 0}))
        return

    total_tokens = token_counts["total"]
    cached_tokens = token_counts["cached"]
    full_text = "".join(collected)

    db.add(MessageRow(
        query_id=query_row.id,
        role="model",
        model=whitelabel,
        content=full_text,
        tokens_in=None,
        tokens_out=total_tokens,
        stage="initial",
    ))
    query_row.status = "done"
    from sqlalchemy import func
    query_row.completed_at = func.now()

    yield format_event(SseEvent("confidence", {"hex": whitelabel, "score": 10, "stage": "initial"}))
    yield format_event(SseEvent("hex_done", {
        "hex": whitelabel,
        "tokens": total_tokens or 0,
        "cached_tokens": cached_tokens or 0,
    }))

    if primal:
        try:
            apex_client = get_client("Apex")
            primal_text = await _run_primal_pass(apex_client, full_text)
            yield format_event(SseEvent("primal", {"text": primal_text}))
        except Exception as e:
            # Don't fail the whole stream for primal failure
            yield format_event(SseEvent(
                "error",
                {"hex": "Apex", "code": type(e).__name__, "message": str(e)[:500]},
            ))

    if quota is not None and total_tokens:
        await QuotaService.deduct(db, quota, total_tokens, whitelabel)

    duration_ms = (time.monotonic_ns() - start_ns) // 1_000_000
    yield format_event(SseEvent("done", {"session_id": session_id, "duration_ms": duration_ms}))


async def _run_primal_pass(apex_client: LLMClient, text: str) -> str:
    """Call Apex with caveman rewrite prompt, collect full text."""
    from app.llm.base import Message as LLMMessage

    messages: list[LLMMessage] = [
        LLMMessage(role="system", content=_PRIMAL_SYSTEM, cache=True),
        LLMMessage(role="user", content=text),
    ]
    parts: list[str] = []
    async for chunk in apex_client.stream(messages):
        if chunk.delta:
            parts.append(chunk.delta)
    return "".join(parts)
