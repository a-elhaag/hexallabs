"""
Council orchestration service.

Flow per execution:
  0a. (Optional) Scout — Tavily web search injects results into query context
  0b. (Optional) Organizer model structures the query — streamed
  1.  All selected models answer the augmented query in parallel
  2.  (Skipped if only 1 model) Models anonymously peer-review each other
  3.  Chairman synthesizes a final answer — OR single model response returned directly
  Post. Budget check → run → deduct usage
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any, AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.council import CouncilConfig
from app.models.execution import Execution
from app.schemas.council import ExecuteRequest
from app.services import foundry
from app.services import search as search_service

CHAIRMAN_MODEL = "gpt-5.1-chat"
BILLING_RATE = 0.60  # users billed at 60% of Azure output price

# Azure output price per 1k tokens
_AZURE_OUTPUT_PRICE_PER_1K: dict[str, float] = {
    "gpt-5.1-chat":           0.015,
    "gpt-5.4-mini":           0.003,
    "o4-mini":                0.0044,
    "DeepSeek-V3.2-Speciale": 0.001,
    "Llama-3.3-70B-Instruct": 0.001,
    "Kimi-K2.5":              0.002,
    "grok-4-20-reasoning":    0.005,
}

# Pre-computed user-billed rate per 1k total tokens
COST_PER_1K: dict[str, float] = {
    k: round(v * BILLING_RATE, 6)
    for k, v in _AZURE_OUTPUT_PRICE_PER_1K.items()
}

ORGANIZER_SYSTEM_PROMPT = (
    "You are a query organizer. Analyze the user's query and return a concise structured breakdown:\n"
    "OBJECTIVE: <one sentence>\n"
    "CONSTRAINTS: <bullet list or 'None'>\n"
    "CONTEXT NEEDED: <bullet list or 'None'>\n"
    "EXPECTED FORMAT: <description>\n\n"
    "Be brief. Do not answer the query."
)

PRIMAL_PROTOCOL_SUFFIX = (
    "\n\nIMPORTANT: Respond in Primal Protocol mode — terse, direct, no filler. "
    "Drop articles, pleasantries, hedging. Fragments OK. "
    "Technical terms exact. Every word must earn its place."
)


# ---------------------------------------------------------------------------
# CRUD helpers
# ---------------------------------------------------------------------------


async def create_execution(
    db: AsyncSession, body: ExecuteRequest, user_id: str
) -> Execution:
    execution = Execution(
        id=str(uuid.uuid4()),
        council_id=body.council_id,
        user_id=user_id,
        query=body.query,
        status="pending",
    )
    db.add(execution)
    await db.commit()
    await db.refresh(execution)
    return execution


async def get_execution(
    db: AsyncSession, execution_id: str, user_id: str
) -> Execution | None:
    result = await db.execute(
        select(Execution).where(
            Execution.id == execution_id,
            Execution.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Orchestration — streamed via WebSocket
# ---------------------------------------------------------------------------


async def run_council(
    db: AsyncSession,
    execution_id: str,
    user_id: str,
    scout_enabled: bool = False,
    primal_protocol: bool = False,
) -> AsyncGenerator[dict[str, Any], None]:
    """
    Generator that drives a full council run and yields WebSocket events.
    """
    from app.services import billing  # avoid circular import

    execution = await get_execution(db, execution_id, user_id)
    if not execution:
        yield {"type": "error", "message": "Execution not found"}
        return

    result = await db.execute(
        select(CouncilConfig).where(CouncilConfig.id == execution.council_id)
    )
    config = result.scalar_one_or_none()
    if not config:
        yield {"type": "error", "message": "Council config not found"}
        return

    # --- Budget + model count enforcement ---
    can_proceed, budget_err = await billing.check_budget(db, user_id)
    if not can_proceed:
        yield {"type": "error", "message": budget_err}
        return

    can_proceed, model_err = await billing.check_max_models(db, user_id, len(config.models))
    if not can_proceed:
        yield {"type": "error", "message": model_err}
        return

    execution.status = "running"
    await db.commit()

    solo_mode = len(config.models) == 1

    # Build system prompt — apply Primal Protocol if requested
    system_prompt = config.system_prompt
    if primal_protocol:
        system_prompt += PRIMAL_PROTOCOL_SUFFIX

    # --- Phase 0a: Scout — web search (optional) ---
    scout_context = ""
    if scout_enabled:
        try:
            scout_results = await search_service.scout(execution.query)
            scout_context = search_service.format_scout_context(scout_results)
            yield {"type": "scout_results", "results": scout_results}
        except Exception as e:
            yield {"type": "scout_error", "message": str(e)}

    # --- Phase 0b: Organizer pre-processing (optional) ---
    organized_context = ""
    if config.organizer_model:
        organizer_chunks: list[str] = []
        async for chunk in foundry.stream_complete(
            model=config.organizer_model,
            system_prompt=ORGANIZER_SYSTEM_PROMPT,
            user_message=execution.query,
        ):
            yield {"type": "organizer_token", "chunk": chunk}
            organizer_chunks.append(chunk)
        organized_context = "".join(organizer_chunks)
        yield {"type": "organizer_done", "organized": organized_context}

    # Build augmented query
    augmented_query = execution.query
    if scout_context:
        augmented_query += f"\n\n{scout_context}"
    if organized_context:
        augmented_query += f"\n\n--- Query Analysis ---\n{organized_context}"

    # --- Phase 1: parallel streaming model responses ---
    model_responses: dict[str, str] = {}
    model_usage: dict[str, dict] = {}
    queue: asyncio.Queue[tuple[str, str | None]] = asyncio.Queue()

    async def _stream_model(model: str) -> None:
        chunks: list[str] = []
        usage: dict = {}
        async for chunk in foundry.stream_complete(
            model=model,
            system_prompt=system_prompt,
            user_message=augmented_query,
            usage_out=usage,
        ):
            await queue.put((model, chunk))
            chunks.append(chunk)
        model_responses[model] = "".join(chunks)
        model_usage[model] = usage
        await queue.put((model, None))  # sentinel

    tasks = [asyncio.create_task(_stream_model(m)) for m in config.models]
    done = 0
    while done < len(config.models):
        model, chunk = await queue.get()
        if chunk is None:
            done += 1
            yield {"type": "model_response", "model": model, "text": model_responses[model]}
        else:
            yield {"type": "token", "model": model, "chunk": chunk}
    await asyncio.gather(*tasks)

    # --- Phase 2: anonymous peer review (skipped in solo mode) ---
    peer_reviews: dict[str, dict[str, Any]] = {}

    if not solo_mode:
        async def peer_review(reviewer: str, target: str, response: str) -> None:
            prompt = (
                "You are reviewing an anonymous AI response. "
                "Give a score (0.0–1.0) and brief feedback.\n\n"
                f"Response to review:\n{response}\n\n"
                'Reply as JSON: {"score": 0.0, "feedback": "..."}'
            )
            review_text = await foundry.complete(
                model=reviewer,
                system_prompt="You are an impartial peer reviewer.",
                user_message=prompt,
            )
            peer_reviews.setdefault(target, {})[reviewer] = review_text

        review_tasks = [
            peer_review(reviewer, target, text)
            for target, text in model_responses.items()
            for reviewer in config.models
            if reviewer != target
        ]
        await asyncio.gather(*review_tasks)

        for target, reviews in peer_reviews.items():
            for reviewer, review in reviews.items():
                yield {
                    "type": "peer_review",
                    "fromModel": reviewer,
                    "toModel": target,
                    "review": review,
                }

    # --- Phase 3: synthesis ---
    if solo_mode:
        only_model = config.models[0]
        synthesis = model_responses[only_model]
        yield {"type": "synthesis_token", "chunk": synthesis}
    else:
        responses_block = "\n\n".join(
            f"[Model {i + 1}]:\n{text}"
            for i, (_, text) in enumerate(model_responses.items())
        )
        synthesis_chunks: list[str] = []
        async for chunk in foundry.stream_complete(
            model=CHAIRMAN_MODEL,
            system_prompt=(
                "You are the chairman of a council of AI models. "
                "Synthesize the following responses into a single, definitive answer."
            ),
            user_message=f"Query: {execution.query}\n\nResponses:\n{responses_block}",
        ):
            yield {"type": "synthesis_token", "chunk": chunk}
            synthesis_chunks.append(chunk)
        synthesis = "".join(synthesis_chunks)

    yield {"type": "synthesis", "text": synthesis}

    # --- Persist results ---
    cost_breakdown = {
        model: round(
            model_usage.get(model, {}).get("total_tokens", 0)
            / 1000
            * COST_PER_1K.get(model, 0.0),
            6,
        )
        for model in config.models
    }
    execution.model_responses = model_responses
    execution.peer_reviews = peer_reviews
    execution.synthesis = synthesis
    execution.cost_breakdown = cost_breakdown
    execution.status = "complete"
    await db.commit()

    # --- Deduct usage from billing ---
    await billing.log_and_deduct(
        db=db,
        user_id=user_id,
        execution_id=execution_id,
        model_usage=model_usage,
        cost_breakdown=cost_breakdown,
    )

    yield {
        "type": "complete",
        "executionId": execution_id,
        "totalCost": sum(cost_breakdown.values()),
    }
