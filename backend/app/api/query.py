from __future__ import annotations

import json
import time
import uuid
from collections.abc import AsyncIterator
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AuthUser, get_current_user
from app.db import get_session
from app.db.models import Message as MessageRow
from app.db.models import Query as QueryRow
from app.db.models import Session as SessionRow
from app.llm.base import Message, ToolCall
from app.llm.factory import get_client
from app.relay.stream import _relay_stream
from app.sse import SseEvent, _TokenCarry, _ToolCallCarry, _client_tokens, _with_heartbeat, format_event
from app.tools.registry import anthropic_schema, openai_schema
from app.tools.web_search import WEB_SEARCH_SPEC, SearchResult, execute_web_search, format_search_context

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
                db, client, query_row, req.query, whitelabel, req.scout
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
                db, client_a, client_b, apex_client, query_row, req.query, wl_a, wl_b
            ):
                yield chunk

        return StreamingResponse(
            _relay(),
            media_type="text/event-stream",
            headers=_SSE_HEADERS,
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"mode {req.mode!r} not yet implemented",
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


def _build_tools_for_client(client: object) -> list[dict[str, Any]]:
    """Render the web_search tool in the correct schema for this client's provider."""
    from app.llm.anthropic_client import AnthropicClient
    from app.llm.azure_client import AzureFoundryClient

    if isinstance(client, AnthropicClient):
        return [anthropic_schema(WEB_SEARCH_SPEC, cache=True)]
    if isinstance(client, AzureFoundryClient):
        return [openai_schema(WEB_SEARCH_SPEC)]
    # Fallback: try Anthropic shape
    return [anthropic_schema(WEB_SEARCH_SPEC, cache=True)]


async def _dispatch_tool(
    tc: ToolCall,
    *,
    tavily_api_key: str,
    scout_max_results: int,
) -> SearchResult:
    if tc.name == "web_search":
        query_str = tc.input.get("query", "")
        max_results = int(tc.input.get("max_results", scout_max_results))
        return await execute_web_search(
            query_str, max_results, api_key=tavily_api_key
        )
    raise ValueError(f"unknown tool: {tc.name!r}")


async def _oracle_stream(
    db: AsyncSession,
    client: object,
    query_row: QueryRow,
    prompt: str,
    whitelabel: str,
    scout: ScoutMode,
) -> AsyncIterator[bytes]:
    from app.config import get_settings
    from app.llm.base import Message as LLMMessage

    settings = get_settings()
    start_ns = time.monotonic_ns()
    session_id = str(query_row.session_id)

    yield format_event(SseEvent("session", {"session_id": session_id, "mode": "oracle"}))
    yield format_event(SseEvent("hex_start", {"hex": whitelabel}))

    messages: list[LLMMessage] = []
    tools_arg: list[dict[str, Any]] | None = None

    # Force mode: pre-execute search, inject as system context.
    if scout == "force":
        if not settings.tavily_api_key:
            yield format_event(SseEvent(
                "error",
                {"hex": whitelabel, "code": "MissingConfig", "message": "TAVILY_API_KEY not set"},
            ))
            yield format_event(SseEvent("done", {"session_id": session_id, "duration_ms": 0}))
            return

        try:
            pre_result = await execute_web_search(
                prompt,
                settings.scout_max_results,
                api_key=settings.tavily_api_key,
            )
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

        context_text = format_search_context(pre_result)
        messages.append(LLMMessage(role="system", content=context_text, cache=True))

    messages.append(LLMMessage(role="user", content=prompt))

    if scout in ("auto", "force"):
        if settings.tavily_api_key:
            tools_arg = _build_tools_for_client(client)

    # Agentic loop — run up to scout_max_turns to handle tool calls.
    collected: list[str] = []
    total_tokens: int | None = None
    cached_tokens: int | None = None

    try:
        for _turn in range(settings.scout_max_turns):
            pending_tool_calls: list[ToolCall] = []
            turn_text: list[str] = []

            async for sse_chunk in _with_heartbeat(
                _client_tokens(client, messages, whitelabel, turn_text, tools=tools_arg)
            ):
                if isinstance(sse_chunk, _TokenCarry):
                    total_tokens = sse_chunk.total_tokens
                    cached_tokens = sse_chunk.cached_tokens
                    continue
                if isinstance(sse_chunk, _ToolCallCarry):
                    tc = sse_chunk.tool_call
                    pending_tool_calls.append(tc)
                    yield format_event(SseEvent("tool_call", {
                        "hex": whitelabel,
                        "id": tc.id,
                        "name": tc.name,
                        "input": tc.input,
                    }))
                    continue
                # Raw bytes (token SSE event)
                yield sse_chunk

            collected.extend(turn_text)

            if not pending_tool_calls:
                break

            # Append assistant turn with tool_calls, then resolve each tool.
            messages.append(LLMMessage(
                role="assistant",
                content="".join(turn_text),
                tool_calls=tuple(pending_tool_calls),
            ))

            for tc in pending_tool_calls:
                if not settings.tavily_api_key:
                    err_msg = "TAVILY_API_KEY not set"
                    yield format_event(SseEvent("tool_result", {
                        "hex": whitelabel,
                        "id": tc.id,
                        "name": tc.name,
                        "summary": "",
                        "urls": [],
                        "result_count": 0,
                        "error": err_msg,
                    }))
                    messages.append(LLMMessage(
                        role="tool",
                        content=json.dumps({"error": err_msg}),
                        tool_use_id=tc.id,
                    ))
                    continue

                try:
                    result = await _dispatch_tool(
                        tc,
                        tavily_api_key=settings.tavily_api_key,
                        scout_max_results=settings.scout_max_results,
                    )
                    yield format_event(SseEvent("tool_result", {
                        "hex": whitelabel,
                        "id": tc.id,
                        "name": tc.name,
                        "summary": result.summary,
                        "urls": result.urls,
                        "result_count": result.result_count,
                    }))
                    messages.append(LLMMessage(
                        role="tool",
                        content=json.dumps({
                            "summary": result.summary,
                            "urls": result.urls,
                            "results": result.raw,
                        }),
                        tool_use_id=tc.id,
                    ))
                except Exception as e:
                    err_msg = str(e)[:500]
                    yield format_event(SseEvent("tool_result", {
                        "hex": whitelabel,
                        "id": tc.id,
                        "name": tc.name,
                        "summary": "",
                        "urls": [],
                        "result_count": 0,
                        "error": err_msg,
                    }))
                    messages.append(LLMMessage(
                        role="tool",
                        content=json.dumps({"error": err_msg}),
                        tool_use_id=tc.id,
                    ))

    except Exception as e:
        query_row.status = "error"
        query_row.error = str(e)[:500]
        yield format_event(SseEvent(
            "error",
            {"hex": whitelabel, "code": type(e).__name__, "message": str(e)[:500]},
        ))
        yield format_event(SseEvent("done", {"session_id": session_id, "duration_ms": 0}))
        return

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

    duration_ms = (time.monotonic_ns() - start_ns) // 1_000_000
    yield format_event(SseEvent("done", {"session_id": session_id, "duration_ms": duration_ms}))
