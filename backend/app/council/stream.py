"""Council mode streaming — parallel fan-out, peer review, Apex synthesis.

Execution phases:
  1. Fan-out: N models stream in parallel, each self-rates with [[CONF:N]].
  2. Peer review: each model reviews anonymized responses from all others,
     may update its confidence.
  3. Synthesis: Apex weighs post-review confidence scores and synthesizes.

Caching strategy (hexal-caching-rules):
  - Phase 1 system prompt: cache=True — invariant rubric, cached on Anthropic;
    Azure uses automatic prefix cache with session_id as cache_key.
  - Phase 2 peer-review system prompt: cache=True (invariant rubric); user
    message (anonymized responses block) is NOT cached — it changes per run.
  - Synthesis delegated to app.synthesis.apex.synthesize() which applies its
    own caching rules.

White-label rules (hexal-whitelabel-names):
  - Prompts use "Model A/B/C" labels — never real model names or white-labels.
  - SSE events use white-label names (hex field).
  - DB rows use white-label names (model field).
"""

from __future__ import annotations

import asyncio
import logging
import string
import time
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Literal, NamedTuple

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession

from app.billing.quota import QuotaService
from app.db.models import Message as MessageRow
from app.db.models import PeerReview as PeerReviewRow
from app.db.models import PromptLensEntry
from app.db.models import Query as QueryRow
from app.db.models.user_quota import UserQuota
from app.lens.analyzer import LensInput, analyze_responses
from app.llm.base import LLMClient, Message
from app.llm.factory import get_client
from app.relay.triggers import CONF_RE
from app.sse.events import SseEvent, format_event
from app.synthesis.apex import ModelResponse, synthesize
from app.tools.scout import scout_force

ScoutMode = Literal["off", "auto", "force"]

logger = logging.getLogger(__name__)

_DEFAULT_CONFIDENCE = 5

# ---------------------------------------------------------------------------
# Labels for anonymization in prompts (hexal-whitelabel-names)
# ---------------------------------------------------------------------------

_LABELS = list(string.ascii_uppercase)  # A–Z


def _anon_label(index: int) -> str:
    """Return 'Model A', 'Model B', … — never exposes white-label names."""
    return f"Model {_LABELS[index % len(_LABELS)]}"


# ---------------------------------------------------------------------------
# System prompts (cache=True per hexal-caching-rules)
# ---------------------------------------------------------------------------

_COUNCIL_FANOUT_SYSTEM = """\
You are an expert answering a user's question as part of an anonymous AI council.

Instructions:
- Answer the user's question thoroughly and accurately.
- At the very end of your response, write your self-confidence score using this
  exact format on a new line: [[CONF:N]] where N is an integer from 1 (very
  uncertain) to 10 (highly confident).
- Do NOT mention that you are part of a council or that your response will be
  reviewed. Just answer the question.\
"""

_PEER_REVIEW_SYSTEM = """\
You are reviewing anonymous responses from fellow expert models in a council.

Instructions:
- Read each model's response and confidence score.
- Provide a brief critique of EACH response (1-3 sentences per model), noting
  gaps, errors, or missed nuances.
- After reviewing, if seeing the other models' answers changes your confidence
  in YOUR OWN response, end with [[CONF:N]] where N is your updated score (1-10).
- Omit [[CONF:N]] if your confidence is unchanged.
- Be precise: point to specific claims, not vague quality judgments.\
"""

# ---------------------------------------------------------------------------
# Internal data structures
# ---------------------------------------------------------------------------


@dataclass
class _ModelResult:
    """Accumulates one model's Phase 1 output and tracks its DB row."""

    whitelabel: str
    parts: list[str] = field(default_factory=list)
    total_tokens: int = 0
    cached_tokens: int = 0
    confidence: int = _DEFAULT_CONFIDENCE
    msg_row: MessageRow | None = None  # set after Phase 1 DB persist + flush


class _ReviewOutcome(NamedTuple):
    """Return type of _peer_review_one."""

    sse_chunks: list[bytes]
    final_confidence: int
    critique_text: str  # stripped, for DB PeerReview.critique


# ---------------------------------------------------------------------------
# Phase 1 helpers
# ---------------------------------------------------------------------------


def _extract_confidence(text: str) -> int:
    """Extract last [[CONF:N]] value (1-10); return _DEFAULT_CONFIDENCE if absent."""
    matches = CONF_RE.findall(text)
    if matches:
        try:
            return max(1, min(10, int(matches[-1])))
        except ValueError:
            pass
    return _DEFAULT_CONFIDENCE


def _strip_conf(text: str) -> str:
    """Remove [[CONF:N]] sentinels before persisting or passing to peers."""
    return CONF_RE.sub("", text).strip()


async def _fanout_one(
    client: LLMClient,
    prompt: str,
    result: _ModelResult,
    session_id: str,
    *,
    scout_context: Message | None = None,
) -> list[bytes]:
    """Stream one council model; fill result.parts, .confidence, .tokens.

    Returns list of SSE token bytes for this model. Caller collects all models
    in parallel via asyncio.gather then emits bytes in order.
    """
    sse_chunks: list[bytes] = []
    messages: list[Message] = []
    if scout_context is not None:
        messages.append(scout_context)
    messages += [
        # Invariant rubric: cache=True (hexal-caching-rules)
        Message(role="system", content=_COUNCIL_FANOUT_SYSTEM, cache=True),
        # Dynamic user query: NOT cached
        Message(role="user", content=prompt),
    ]

    async for chunk in client.stream(messages, cache_key=session_id):
        if chunk.total_tokens is not None:
            result.total_tokens = chunk.total_tokens
        if chunk.cached_tokens is not None:
            result.cached_tokens = chunk.cached_tokens
        if chunk.delta:
            result.parts.append(chunk.delta)
            sse_chunks.append(
                format_event(SseEvent("token", {"hex": result.whitelabel, "delta": chunk.delta}))
            )

    result.confidence = _extract_confidence("".join(result.parts))
    return sse_chunks


# ---------------------------------------------------------------------------
# Phase 2 helpers
# ---------------------------------------------------------------------------


async def _peer_review_one(
    client: LLMClient,
    reviewer_index: int,
    results: list[_ModelResult],
    session_id: str,
) -> _ReviewOutcome:
    """Run one model's peer review pass.

    The anonymized context uses "Model A/B/C" labels per hexal-whitelabel-names.
    SSE peer_review and confidence events use real white-label names.

    Returns:
        _ReviewOutcome(sse_chunks, final_confidence, critique_text)
    """
    reviewer = results[reviewer_index]
    sse_chunks: list[bytes] = []

    # Build anonymized responses block — "Model A/B/C" labels only (hexal-whitelabel-names)
    lines: list[str] = ["## Council Responses for Review", ""]
    for i, r in enumerate(results):
        label = _anon_label(i)
        clean = _strip_conf("".join(r.parts))
        lines.append(f"### {label} (confidence: {r.confidence}/10)")
        lines.append("")
        lines.append(clean)
        lines.append("")

    my_label = _anon_label(reviewer_index)
    lines += [
        "## Your Identity",
        f"You submitted the response labeled **{my_label}**.",
        "",
        "## Task",
        "Critique each response above (including your own if warranted). "
        "If reviewing peers changes your confidence, end with [[CONF:N]].",
    ]

    messages: list[Message] = [
        # Invariant rubric: cache=True (hexal-caching-rules)
        Message(role="system", content=_PEER_REVIEW_SYSTEM, cache=True),
        # Dynamic anonymized responses: NOT cached
        Message(role="user", content="\n".join(lines)),
    ]

    critique_parts: list[str] = []
    async for chunk in client.stream(messages, cache_key=session_id):
        if chunk.delta:
            critique_parts.append(chunk.delta)

    critique_text = "".join(critique_parts)
    clean_critique = _strip_conf(critique_text)

    # Emit peer_review events: one per target model (using white-labels in SSE events)
    for target in results:
        if target.whitelabel == reviewer.whitelabel:
            continue
        sse_chunks.append(
            format_event(
                SseEvent(
                    "peer_review",
                    {
                        "from": reviewer.whitelabel,
                        "to": target.whitelabel,
                        "critique": clean_critique,
                    },
                )
            )
        )

    # Determine final confidence; emit update event if changed
    conf_match = CONF_RE.search(critique_text)
    if conf_match:
        updated_conf = max(1, min(10, int(conf_match.group(1))))
        sse_chunks.append(
            format_event(
                SseEvent(
                    "confidence",
                    {"hex": reviewer.whitelabel, "score": updated_conf, "stage": "post_review"},
                )
            )
        )
        final_conf = updated_conf
    else:
        final_conf = reviewer.confidence

    return _ReviewOutcome(
        sse_chunks=sse_chunks,
        final_confidence=final_conf,
        critique_text=clean_critique,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def _council_stream(
    db: AsyncSession,
    clients: list[LLMClient],
    apex_client: LLMClient,
    query_row: QueryRow,
    prompt: str,
    whitelabels: list[str],
    *,
    primal: bool = False,
    scout: ScoutMode = "off",
    quota: UserQuota | None = None,
) -> AsyncIterator[bytes]:
    """Stream Council mode: fan-out → peer review → Apex synthesis.

    Args:
        db: Async SQLAlchemy session.
        clients: One LLMClient per selected model, matching whitelabels order.
        apex_client: LLMClient for Apex (chairman / synthesizer).
        query_row: Persisted QueryRow for this request.
        prompt: Original user query.
        whitelabels: White-label names matching clients order.
        primal: If True, Apex runs Primal Protocol rewrite after synthesis.
        scout: Web search injection mode ("off", "force", "auto").
    """
    start_ns = time.monotonic_ns()
    session_id = str(query_row.session_id)

    yield format_event(SseEvent("session", {"session_id": session_id, "mode": "council"}))

    # -----------------------------------------------------------------------
    # Scout pre-injection (force/auto both do pre-execution in council)
    # -----------------------------------------------------------------------
    scout_system_msg: Message | None = None
    if scout in ("force", "auto"):
        from app.config import get_settings
        settings = get_settings()
        try:
            context_text, pre_result = await scout_force(prompt, settings)
        except ValueError:
            yield format_event(SseEvent("error", {"hex": "council", "code": "MissingConfig", "message": "TAVILY_API_KEY not set"}))
            duration_ms = (time.monotonic_ns() - start_ns) // 1_000_000
            yield format_event(SseEvent("done", {"session_id": session_id, "duration_ms": duration_ms}))
            return
        except Exception as exc:
            yield format_event(SseEvent("error", {"hex": "council", "code": type(exc).__name__, "message": str(exc)[:500]}))
            duration_ms = (time.monotonic_ns() - start_ns) // 1_000_000
            yield format_event(SseEvent("done", {"session_id": session_id, "duration_ms": duration_ms}))
            return
        force_id = f"force_{uuid.uuid4().hex[:8]}"
        yield format_event(SseEvent("tool_call", {"hex": "council", "id": force_id, "name": "web_search", "input": {"query": prompt}, "forced": True}))
        yield format_event(SseEvent("tool_result", {"hex": "council", "id": force_id, "name": "web_search", "summary": pre_result.summary, "urls": pre_result.urls, "result_count": pre_result.result_count}))
        scout_system_msg = Message(role="system", content=context_text, cache=True)

    results: list[_ModelResult] = [_ModelResult(whitelabel=wl) for wl in whitelabels]

    # -----------------------------------------------------------------------
    # Phase 1 — Parallel fan-out
    # -----------------------------------------------------------------------

    for wl in whitelabels:
        yield format_event(SseEvent("hex_start", {"hex": wl}))

    try:
        per_model_sse: list[list[bytes]] = await asyncio.gather(
            *[
                _fanout_one(client, prompt, result, session_id, scout_context=scout_system_msg)
                for client, result in zip(clients, results)
            ]
        )
    except Exception as exc:
        logger.exception("council: phase 1 fan-out failed")
        query_row.status = "error"
        query_row.error = str(exc)[:500]
        yield format_event(
            SseEvent(
                "error",
                {"hex": "council", "code": type(exc).__name__, "message": str(exc)[:500]},
            )
        )
        duration_ms = (time.monotonic_ns() - start_ns) // 1_000_000
        yield format_event(SseEvent("done", {"session_id": session_id, "duration_ms": duration_ms}))
        return

    # Emit token bytes in per-model order (each model's tokens are sequential)
    for model_chunks in per_model_sse:
        for chunk_bytes in model_chunks:
            yield chunk_bytes

    # Persist Phase 1 messages; emit hex_done + confidence(initial) per model
    for result in results:
        clean_text = _strip_conf("".join(result.parts))
        msg_row = MessageRow(
            query_id=query_row.id,
            role="model",
            model=result.whitelabel,
            content=clean_text,
            confidence=result.confidence,
            tokens_out=result.total_tokens,
            stage="council_0",
        )
        db.add(msg_row)
        result.msg_row = msg_row  # hold ref; IDs populated after flush below

        yield format_event(
            SseEvent(
                "confidence",
                {"hex": result.whitelabel, "score": result.confidence, "stage": "initial"},
            )
        )
        yield format_event(
            SseEvent(
                "hex_done",
                {
                    "hex": result.whitelabel,
                    "tokens": result.total_tokens,
                    "cached_tokens": result.cached_tokens,
                },
            )
        )
        if quota is not None and result.total_tokens:
            await QuotaService.deduct(db, quota, result.total_tokens, result.whitelabel)

    # Flush so MessageRow IDs are populated (needed as PeerReview FKs)
    await db.flush()

    # -----------------------------------------------------------------------
    # Phase 2 — Parallel peer review
    # -----------------------------------------------------------------------

    try:
        review_outcomes: list[_ReviewOutcome] = await asyncio.gather(
            *[
                _peer_review_one(client, i, results, session_id)
                for i, client in enumerate(clients)
            ]
        )
    except Exception as exc:
        logger.exception("council: phase 2 peer review failed")
        query_row.status = "error"
        query_row.error = str(exc)[:500]
        yield format_event(
            SseEvent(
                "error",
                {"hex": "council", "code": type(exc).__name__, "message": str(exc)[:500]},
            )
        )
        duration_ms = (time.monotonic_ns() - start_ns) // 1_000_000
        yield format_event(SseEvent("done", {"session_id": session_id, "duration_ms": duration_ms}))
        return

    # Emit peer review SSE bytes and update final confidences in results
    for i, outcome in enumerate(review_outcomes):
        results[i].confidence = outcome.final_confidence
        for chunk_bytes in outcome.sse_chunks:
            yield chunk_bytes

    # Persist PeerReview rows (reviewer → each target it reviewed)
    for reviewer_idx, outcome in enumerate(review_outcomes):
        reviewer_msg = results[reviewer_idx].msg_row
        if reviewer_msg is None:
            continue
        for target_idx, target in enumerate(results):
            if target_idx == reviewer_idx:
                continue
            target_msg = target.msg_row
            if target_msg is None:
                continue
            db.add(
                PeerReviewRow(
                    query_id=query_row.id,
                    reviewer_message_id=reviewer_msg.id,
                    target_message_id=target_msg.id,
                    critique=outcome.critique_text or "(no critique)",
                    adjusted_confidence=(
                        outcome.final_confidence
                        if outcome.final_confidence != results[reviewer_idx].confidence
                        else None
                    ),
                )
            )

    # -----------------------------------------------------------------------
    # Phase 3 — Apex synthesis
    # -----------------------------------------------------------------------

    model_responses: list[ModelResponse] = [
        ModelResponse(
            whitelabel=result.whitelabel,
            text=_strip_conf("".join(result.parts)),
            confidence=result.confidence,
            tokens=result.total_tokens,
            cached_tokens=result.cached_tokens,
        )
        for result in results
    ]

    try:
        async for synth_bytes in synthesize(apex_client, prompt, model_responses, primal=primal):
            yield synth_bytes
    except Exception as exc:
        logger.exception("council: apex synthesis failed")
        query_row.status = "error"
        query_row.error = str(exc)[:500]
        yield format_event(
            SseEvent(
                "error",
                {"hex": "Apex", "code": type(exc).__name__, "message": str(exc)[:500]},
            )
        )
        duration_ms = (time.monotonic_ns() - start_ns) // 1_000_000
        yield format_event(SseEvent("done", {"session_id": session_id, "duration_ms": duration_ms}))
        return

    query_row.status = "done"
    query_row.completed_at = func.now()

    # -----------------------------------------------------------------------
    # Phase 4 — Prompt Lens (per-model interpretation analysis via Spark)
    # -----------------------------------------------------------------------
    # Lens runs after synthesis. Individual model failures are caught inside
    # analyze_responses and skipped — they must not crash the stream.

    try:
        spark_client = get_client("Spark")
        lens_inputs = [
            LensInput(
                whitelabel=r.whitelabel,
                text=r.text,
                confidence=r.confidence,
            )
            for r in model_responses
        ]
        lens_results = await analyze_responses(
            spark_client, prompt, lens_inputs, cache_key=session_id
        )
        for lr in lens_results:
            db.add(
                PromptLensEntry(
                    query_id=query_row.id,
                    model=lr.whitelabel,
                    interpretation=lr.interpretation,
                    divergence_score=lr.divergence_score,
                )
            )
            yield format_event(
                SseEvent("lens", {"hex": lr.whitelabel, "interpretation": lr.interpretation})
            )
    except Exception:
        # Lens phase failure must never prevent done from being emitted
        logger.exception("council: prompt lens phase failed — skipping")

    duration_ms = (time.monotonic_ns() - start_ns) // 1_000_000
    yield format_event(SseEvent("done", {"session_id": session_id, "duration_ms": duration_ms}))
