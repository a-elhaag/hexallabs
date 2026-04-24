from __future__ import annotations

import asyncio
import contextlib
import logging
import time
import uuid as _uuid
from collections.abc import AsyncIterator
from typing import Literal

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession

from app.billing.quota import QuotaService
from app.db.models import Message as MessageRow
from app.db.models import Query as QueryRow
from app.db.models import RelayHandoff
from app.db.models.user_quota import UserQuota
from app.llm.base import LLMClient, Message
from app.relay.baton import build_baton
from app.relay.triggers import (
    CONF_RE,
    MARKER_RE,
    TriggerFired,
    apex_watcher,
    scan_confidence,
    scan_marker,
)
from app.sse.events import SseEvent, format_event
from app.sse.stream_utils import _TokenCarry, _client_tokens, _with_heartbeat
from app.tools.scout import scout_force

logger = logging.getLogger(__name__)

_TAIL_WINDOW = 512

ScoutMode = Literal["off", "auto", "force"]


async def _relay_stream(
    db: AsyncSession,
    client_a: LLMClient,
    client_b: LLMClient,
    apex_client: LLMClient,
    query_row: QueryRow,
    prompt: str,
    whitelabel_a: str,
    whitelabel_b: str,
    scout: ScoutMode = "off",
    quota: UserQuota | None = None,
) -> AsyncIterator[bytes]:
    start_ns = time.monotonic_ns()
    session_id = str(query_row.session_id)

    yield format_event(SseEvent("session", {"session_id": session_id, "mode": "relay"}))

    # Scout injection — both force and auto do pre-injection in relay context
    # (agentic tool-use loop is incompatible with trigger-detection streaming)
    prompt_messages: list[Message]
    if scout in ("force", "auto"):
        from app.config import get_settings
        settings = get_settings()
        try:
            context_text, pre_result = await scout_force(prompt, settings)
        except ValueError:
            yield format_event(SseEvent("error", {"hex": whitelabel_a, "code": "MissingConfig", "message": "TAVILY_API_KEY not set"}))
            yield format_event(SseEvent("done", {"session_id": session_id, "duration_ms": 0}))
            return
        force_id = f"force_{_uuid.uuid4().hex[:8]}"
        yield format_event(SseEvent("tool_call", {
            "hex": whitelabel_a,
            "id": force_id,
            "name": "web_search",
            "input": {"query": prompt},
            "forced": True,
        }))
        yield format_event(SseEvent("tool_result", {
            "hex": whitelabel_a,
            "id": force_id,
            "name": "web_search",
            "summary": pre_result.summary,
            "urls": pre_result.urls,
            "result_count": pre_result.result_count,
        }))
        prompt_messages = [
            Message(role="system", content=context_text, cache=True),
            Message(role="user", content=prompt),
        ]
    else:
        prompt_messages = [Message(role="user", content=prompt)]

    yield format_event(SseEvent("hex_start", {"hex": whitelabel_a}))

    # Stage A — stream with trigger detection
    partial_a: list[str] = []
    fire_event = asyncio.Event()
    reason_box: list[str] = []
    triggered: TriggerFired | None = None
    handoff_detected = False
    total_a: int | None = None
    cached_a: int | None = None

    async def drive_a() -> AsyncIterator[bytes | _TokenCarry]:
        nonlocal triggered, handoff_detected
        total: int | None = None
        cached: int | None = None
        async for chunk in client_a.stream(prompt_messages):
            if chunk.total_tokens is not None:
                total = chunk.total_tokens
            if chunk.cached_tokens is not None:
                cached = chunk.cached_tokens
            if chunk.delta:
                partial_a.append(chunk.delta)
                buf = "".join(partial_a)
                buf_tail = buf[-_TAIL_WINDOW:] if len(buf) > _TAIL_WINDOW else buf
                t = scan_marker(buf_tail) or scan_confidence(buf_tail)
                if t:
                    if not reason_box:
                        reason_box.append(t.reason)
                    triggered = t
                    handoff_detected = True
                    fire_event.set()
                    yield _TokenCarry(total_tokens=total, cached_tokens=cached)
                    return
                if fire_event.is_set():
                    # apex_watcher fired
                    handoff_detected = True
                    yield _TokenCarry(total_tokens=total, cached_tokens=cached)
                    return
                yield format_event(SseEvent("token", {"hex": whitelabel_a, "delta": chunk.delta}))
        yield _TokenCarry(total_tokens=total, cached_tokens=cached)

    watcher = asyncio.create_task(
        apex_watcher(apex_client, partial_a, fire_event, reason_box)
    )
    try:
        async for item in _with_heartbeat(drive_a()):
            if isinstance(item, _TokenCarry):
                total_a = item.total_tokens
                cached_a = item.cached_tokens
            else:
                yield item
    except Exception as exc:
        query_row.status = "error"
        query_row.error = str(exc)[:500]
        yield format_event(SseEvent("error", {"hex": whitelabel_a, "code": type(exc).__name__, "message": str(exc)[:500]}))
        yield format_event(SseEvent("done", {"session_id": session_id, "duration_ms": 0}))
        return
    finally:
        fire_event.set()
        watcher.cancel()
        with contextlib.suppress(asyncio.CancelledError, Exception):
            await watcher

    partial_text_a = "".join(partial_a)

    if not handoff_detected:
        # A completed naturally — passthrough, treat as relay_0 only
        db.add(MessageRow(
            query_id=query_row.id,
            role="model",
            model=whitelabel_a,
            content=partial_text_a,
            tokens_out=total_a,
            stage="relay_0",
        ))
        query_row.status = "done"
        query_row.completed_at = func.now()
        yield format_event(SseEvent("confidence", {"hex": whitelabel_a, "score": 10, "stage": "relay_0"}))
        yield format_event(SseEvent("hex_done", {"hex": whitelabel_a, "tokens": total_a or 0, "cached_tokens": cached_a or 0}))
        if quota is not None and total_a:
            await QuotaService.deduct(db, quota, total_a, whitelabel_a)
        duration_ms = (time.monotonic_ns() - start_ns) // 1_000_000
        yield format_event(SseEvent("done", {"session_id": session_id, "duration_ms": duration_ms}))
        return

    # Handoff path — apex may have fired even if triggered is None
    if triggered is None:
        triggered = TriggerFired("apex", reason_box[0] if reason_box else "apex flagged off-track")

    # Persist A's message (need id for RelayHandoff FK)
    stripped_partial = _strip_partial(partial_text_a)
    msg_a = MessageRow(
        query_id=query_row.id,
        role="model",
        model=whitelabel_a,
        content=stripped_partial,
        tokens_out=total_a,
        stage="relay_0",
    )
    db.add(msg_a)
    await db.flush()  # get msg_a.id

    db.add(RelayHandoff(
        query_id=query_row.id,
        from_message_id=msg_a.id,
        to_model=whitelabel_b,
        trigger_reason=f"{triggered.kind}:{triggered.reason}",
        partial_output=stripped_partial,
    ))

    yield format_event(SseEvent("confidence", {"hex": whitelabel_a, "score": 10, "stage": "relay_0"}))
    yield format_event(SseEvent("hex_done", {"hex": whitelabel_a, "tokens": total_a or 0, "cached_tokens": cached_a or 0}))
    yield format_event(SseEvent("relay_handoff", {
        "from": whitelabel_a,
        "to": whitelabel_b,
        "trigger": triggered.kind,
        "reason": triggered.reason,
        "partial_chars": len(stripped_partial),
    }))

    # Stage B
    yield format_event(SseEvent("hex_start", {"hex": whitelabel_b}))

    try:
        baton_messages = await build_baton(apex_client, prompt, partial_text_a, triggered, whitelabel_a, whitelabel_b)
    except Exception as exc:
        logger.exception("relay: baton build failed")
        query_row.status = "error"
        query_row.error = str(exc)[:500]
        yield format_event(SseEvent("error", {"hex": whitelabel_b, "code": type(exc).__name__, "message": str(exc)[:500]}))
        yield format_event(SseEvent("done", {"session_id": session_id, "duration_ms": 0}))
        return

    partial_b: list[str] = []
    total_b: int | None = None
    cached_b: int | None = None

    try:
        async for item in _with_heartbeat(_client_tokens(client_b, baton_messages, whitelabel_b, partial_b)):
            if isinstance(item, _TokenCarry):
                total_b = item.total_tokens
                cached_b = item.cached_tokens
            else:
                yield item
    except Exception as exc:
        query_row.status = "error"
        query_row.error = str(exc)[:500]
        yield format_event(SseEvent("error", {"hex": whitelabel_b, "code": type(exc).__name__, "message": str(exc)[:500]}))
        yield format_event(SseEvent("done", {"session_id": session_id, "duration_ms": 0}))
        return

    full_b = "".join(partial_b)
    db.add(MessageRow(
        query_id=query_row.id,
        role="model",
        model=whitelabel_b,
        content=full_b,
        tokens_out=total_b,
        stage="relay_1",
    ))
    query_row.status = "done"
    query_row.completed_at = func.now()

    yield format_event(SseEvent("confidence", {"hex": whitelabel_b, "score": 10, "stage": "relay_1"}))
    yield format_event(SseEvent("hex_done", {"hex": whitelabel_b, "tokens": total_b or 0, "cached_tokens": cached_b or 0}))
    if quota is not None:
        if total_a:
            await QuotaService.deduct(db, quota, total_a, whitelabel_a)
        if total_b:
            await QuotaService.deduct(db, quota, total_b, whitelabel_b)
    duration_ms = (time.monotonic_ns() - start_ns) // 1_000_000
    yield format_event(SseEvent("done", {"session_id": session_id, "duration_ms": duration_ms}))


def _strip_partial(text: str) -> str:
    """Strip [[HANDOFF:...]] and [[CONF:...]] sentinels before persisting or passing to baton."""
    text = MARKER_RE.sub("", text)
    text = CONF_RE.sub("", text)
    return text.strip()
