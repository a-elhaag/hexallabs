"""
Council orchestration service.

Flow per execution:
  1. All models answer the query in parallel
  2. Models anonymously peer-review each other's responses
  3. Chairman (gpt-4o) synthesizes a final answer
  4. Results + cost are persisted to the Execution row
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any, AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.council import CouncilConfig
from app.models.execution import Execution
from app.schemas.council import CouncilConfigCreate, ExecuteRequest
from app.services import foundry

CHAIRMAN_MODEL = "gpt-4o"

# Approximate cost per 1k tokens (USD) — update as pricing changes
COST_PER_1K: dict[str, float] = {
    "gpt-4o": 0.005,
    "o1": 0.015,
    "deepseek-r1": 0.002,
    "mistral-large-3": 0.002,
}


# ---------------------------------------------------------------------------
# CRUD helpers
# ---------------------------------------------------------------------------


async def create_council(
    db: AsyncSession, user_id: str, body: CouncilConfigCreate
) -> CouncilConfig:
    config = CouncilConfig(
        id=str(uuid.uuid4()),
        user_id=user_id,
        name=body.name,
        models=body.models,
        system_prompt=body.system_prompt,
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)
    return config


async def get_council(
    db: AsyncSession, council_id: str, user_id: str
) -> CouncilConfig | None:
    result = await db.execute(
        select(CouncilConfig).where(
            CouncilConfig.id == council_id,
            CouncilConfig.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


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
    db: AsyncSession, execution_id: str, user_id: str
) -> AsyncGenerator[dict[str, Any], None]:
    """
    Generator that drives a full council run and yields WebSocket events.
    Events mirror the WS message protocol defined in the design doc.
    """
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

    # Mark running
    execution.status = "running"
    await db.commit()

    # --- Phase 1: parallel streaming model responses ---
    model_responses: dict[str, str] = {}
    queue: asyncio.Queue[tuple[str, str | None]] = asyncio.Queue()

    async def _stream_model(model: str) -> None:
        chunks: list[str] = []
        async for chunk in foundry.stream_complete(
            model=model,
            system_prompt=config.system_prompt,
            user_message=execution.query,
        ):
            await queue.put((model, chunk))
            chunks.append(chunk)
        model_responses[model] = "".join(chunks)
        await queue.put((model, None))  # sentinel: this model is done

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

    # --- Phase 2: anonymous peer review ---
    peer_reviews: dict[str, dict[str, Any]] = {}

    async def peer_review(reviewer: str, target: str, response: str) -> None:
        prompt = (
            "You are reviewing an anonymous AI response. "
            "Give a score (0.0–1.0) and brief feedback.\n\n"
            f"Response to review:\n{response}\n\n"
            "Reply as JSON: {\"score\": 0.0, \"feedback\": \"...\"}"
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

    # --- Phase 3: chairman synthesis (streamed) ---
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
        model: COST_PER_1K.get(model, 0.0) for model in config.models
    }
    execution.model_responses = model_responses
    execution.peer_reviews = peer_reviews
    execution.synthesis = synthesis
    execution.cost_breakdown = cost_breakdown
    execution.status = "complete"
    await db.commit()

    yield {
        "type": "complete",
        "executionId": execution_id,
        "totalCost": sum(cost_breakdown.values()),
    }
