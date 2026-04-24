"""Prompt Lens — post-run per-model interpretation analysis.

For each model that participated in a Council run, Spark (cheap/fast Azure
model) generates:
  - A short interpretation: how did this model interpret the query?
  - A divergence score (1-10): how much did it diverge from a literal reading?

Results are emitted as `lens` SSE events before `done`, and persisted to DB.

Caching strategy (hexal-caching-rules):
  - System prompt: cache=True — invariant rubric, benefits from Azure automatic
    prefix cache (Spark is Azure; first 1024 tokens must be identical across
    requests for a cache hit). Session or user ID passed as cache_key for
    sticky routing and higher hit rate.
  - User message (query + response text): NOT cached — changes per model/run.

White-label rules (hexal-whitelabel-names):
  - `whitelabel` field in LensInput/LensResult uses white-label names only.
  - Lens prompt does NOT reference real model names — uses "a model" / "this
    model" neutrally so Spark has no brand bias.
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass

from app.llm.base import LLMClient, Message

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cached system prompt (hexal-caching-rules: put FIRST, invariant)
# ---------------------------------------------------------------------------

_LENS_SYSTEM = """\
You analyze how an AI model interpreted a user query.

Given a user query and a model's response, do the following:
1. Write 1-2 sentences explaining what angle, framing, or interpretation this
   model took when answering. Be specific: what did it prioritize, what did it
   emphasize, or what aspect of the question did it focus on?
2. Rate divergence from a strictly literal reading of the query on a scale of
   1 to 10, where:
   1 = very literal (answered exactly what was asked, no creative reframing)
   10 = very creative or tangential (reframed, broadened, or shifted the query
        significantly)

Output format (follow exactly):
First, write the interpretation paragraph (1-2 sentences).
Then, on a new line by itself: DIVERGENCE:N
where N is an integer from 1 to 10.

Do not include any preamble, labels, or explanation beyond this format.\
"""

# Regex to parse "DIVERGENCE:N" from the end of Spark's output
_DIVERGENCE_RE = re.compile(r"DIVERGENCE:(\d+)", re.IGNORECASE)

_DEFAULT_DIVERGENCE = 5

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class LensInput:
    """One council model's completed response, ready for Lens analysis."""

    whitelabel: str  # e.g. "Swift" — white-label name (hexal-whitelabel-names)
    text: str        # full model response text (conf sentinel already stripped)
    confidence: int  # final post-review confidence score (1-10)


@dataclass(frozen=True, slots=True)
class LensResult:
    """Prompt Lens analysis result for one council model."""

    whitelabel: str        # white-label name — used in SSE `hex` field and DB
    interpretation: str    # 1-2 sentence interpretation paragraph
    divergence_score: int  # 1-10, clamped; default 5 if parsing fails


# ---------------------------------------------------------------------------
# Single-model analysis
# ---------------------------------------------------------------------------


async def _analyze_one(
    spark_client: LLMClient,
    query: str,
    inp: LensInput,
    cache_key: str | None = None,
) -> LensResult:
    """Call Spark to analyze one model's response.

    Raises on LLM errors — caller (`analyze_responses`) catches per-model
    and skips rather than crashing the whole lens phase.

    Args:
        spark_client: LLMClient for Spark (Azure). Never leaks real model name.
        query: Original user query.
        inp: The council model's response data.
        cache_key: Optional session/user ID for Azure sticky routing.

    Returns:
        LensResult with parsed interpretation and clamped divergence score.
    """
    messages: list[Message] = [
        # Invariant rubric: cache=True (hexal-caching-rules, Azure prefix cache)
        Message(role="system", content=_LENS_SYSTEM, cache=True),
        # Dynamic per-model content: NOT cached (changes every call)
        Message(role="user", content=f"Query: {query}\n\nResponse:\n{inp.text}"),
    ]

    parts: list[str] = []
    async for chunk in spark_client.stream(messages, cache_key=cache_key):
        if chunk.delta:
            parts.append(chunk.delta)

    raw = "".join(parts).strip()

    # Parse DIVERGENCE:N — take the last match in case of extra text
    matches = _DIVERGENCE_RE.findall(raw)
    if matches:
        try:
            score = max(1, min(10, int(matches[-1])))
        except ValueError:
            score = _DEFAULT_DIVERGENCE
    else:
        score = _DEFAULT_DIVERGENCE

    # Interpretation = everything before the last DIVERGENCE: line
    # Split on the matched sentinel and take the prefix
    div_match = _DIVERGENCE_RE.search(raw)
    if div_match:
        interpretation = raw[: div_match.start()].strip()
    else:
        interpretation = raw

    # Guard: never return an empty interpretation
    if not interpretation:
        interpretation = "(interpretation unavailable)"

    return LensResult(
        whitelabel=inp.whitelabel,
        interpretation=interpretation,
        divergence_score=score,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def analyze_responses(
    spark_client: LLMClient,
    query: str,
    inputs: list[LensInput],
    cache_key: str | None = None,
) -> list[LensResult]:
    """Run Spark on each model response in parallel, return LensResult list.

    Failures for individual models are caught and logged; that model is
    omitted from the returned list rather than crashing the stream.

    Args:
        spark_client: LLMClient for Spark (Azure AI Foundry).
        query: Original user query string.
        inputs: One LensInput per council model.
        cache_key: Optional session/user ID for Azure sticky routing /
                   higher prefix-cache hit rate.

    Returns:
        List of LensResult (length ≤ len(inputs); failed models are skipped).
    """
    async def _safe_analyze(inp: LensInput) -> LensResult | None:
        try:
            return await _analyze_one(spark_client, query, inp, cache_key=cache_key)
        except Exception:
            logger.exception(
                "lens: analysis failed for model %r — skipping", inp.whitelabel
            )
            return None

    raw_results = await asyncio.gather(*[_safe_analyze(inp) for inp in inputs])
    return [r for r in raw_results if r is not None]
