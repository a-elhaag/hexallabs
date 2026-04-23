"""Apex synthesis module — Council mode final answer synthesizer.

Apex is the chairman model (Anthropic direct, white-label "Apex"). It receives
anonymized council responses weighted by post-review confidence scores and
produces a single authoritative answer streamed as SSE bytes.

Optionally runs a second pass (Primal Protocol) that rewrites the synthesis
in brutally compressed caveman style.

Caching strategy (hexal-caching-rules):
  - System prompts use cache=True so the invariant rubric prefix is cached
    with Anthropic (cache_control: ephemeral, ~90% discount on hits).
  - User message (query + council responses) is never cached — it changes
    every request.
"""

from __future__ import annotations

import string
from collections.abc import AsyncIterator
from dataclasses import dataclass

from app.llm.base import LLMClient, Message
from app.sse.events import SseEvent, format_event

# ---------------------------------------------------------------------------
# Cached system prompts
# ---------------------------------------------------------------------------

_APEX_SYNTH_SYSTEM = """\
You are Apex, the synthesis chairman of a council of AI models.

Your role is to produce the best possible answer to the user's query by \
thoughtfully weighing the responses provided by council models. Each response \
is labeled with an anonymized model identifier and its confidence score (1-10) \
reflecting post-peer-review self-assessment.

Synthesis rules:
- Weight responses by confidence: higher confidence = more authority.
- Identify points of strong agreement across models and lead with those.
- Where models disagree, use your judgment to resolve or acknowledge the tension.
- If a lower-confidence model makes a uniquely valuable point absent from \
higher-confidence responses, incorporate it.
- Produce a single, cohesive, authoritative answer. Do not list models or \
attribute claims — synthesize into one voice.
- Do not mention confidence scores, model identifiers, or council mechanics \
in your response.
- Respond directly to the user's query. Be clear, precise, and complete.\
"""

_PRIMAL_SYSTEM = """\
You are Apex in Primal Protocol mode.

Rewrite the synthesis below as brutally compressed caveman speech:
- No articles (a, an, the)
- No filler words (however, therefore, in order to, it is important to note)
- No passive voice
- Short declarative bursts. Subject-verb-object only.
- Preserve ALL technical accuracy and key information — just strip the fat.
- Output caveman rewrite only. No preamble, no explanation.\
"""

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ModelResponse:
    """One council model's completed response, ready for synthesis."""

    whitelabel: str  # e.g. "Swift", "Prism" — used only for internal labeling
    text: str  # full response text
    confidence: int  # 1-10, post-review confidence score
    tokens: int
    cached_tokens: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_LABELS = list(string.ascii_uppercase)  # A–Z; councils of >26 are unsupported


def _anonymize_label(index: int) -> str:
    """Return 'Model A', 'Model B', … — never exposes white-label names."""
    return f"Model {_LABELS[index % len(_LABELS)]}"


def _build_synthesis_user_message(query: str, responses: list[ModelResponse]) -> str:
    """Build the user message that presents council responses to Apex.

    White-label names are deliberately excluded per hexal-whitelabel-names:
    models are anonymized as 'Model A', 'Model B', etc. to prevent Apex from
    being biased by brand associations.
    """
    lines: list[str] = [
        "## User Query",
        "",
        query,
        "",
        "## Council Responses",
        "",
    ]
    for i, resp in enumerate(responses):
        label = _anonymize_label(i)
        lines.append(f"### {label} (confidence: {resp.confidence}/10)")
        lines.append("")
        lines.append(resp.text)
        lines.append("")

    lines.append("## Task")
    lines.append(
        "Synthesize the council responses into the best possible answer to the user's query."
    )
    return "\n".join(lines)


def _build_primal_user_message(synthesis_text: str) -> str:
    return f"## Synthesis to rewrite\n\n{synthesis_text}"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def synthesize(
    apex_client: LLMClient,
    query: str,
    responses: list[ModelResponse],
    *,
    primal: bool = False,
) -> AsyncIterator[bytes]:
    """Stream Apex synthesis as SSE bytes.

    Emits (in order):
      synth_start  {}
      synth_token  {delta: str}   (many)
      synth_done   {tokens: int}

    If primal=True, additionally emits AFTER synth_done:
      primal       {text: str}    (second Apex pass, caveman rewrite)

    Args:
        apex_client: Pre-constructed LLMClient for Apex (Anthropic direct).
                     Callers must provide this — synthesize() never calls
                     get_client() internally so it remains testable.
        query: Original user query.
        responses: Council model responses with post-review confidence scores.
        primal: If True, run a second Apex pass for Primal Protocol rewrite.
    """
    # System prompt uses cache=True so the invariant rubric is cached on
    # Anthropic side (cache_control: ephemeral). User message is never cached.
    synth_messages: list[Message] = [
        Message(role="system", content=_APEX_SYNTH_SYSTEM, cache=True),
        Message(
            role="user",
            content=_build_synthesis_user_message(query, responses),
        ),
    ]

    yield format_event(SseEvent("synth_start", {}))

    synth_parts: list[str] = []
    total_tokens: int = 0

    async for chunk in apex_client.stream(synth_messages):
        if chunk.total_tokens is not None:
            total_tokens = chunk.total_tokens
        if chunk.delta:
            synth_parts.append(chunk.delta)
            yield format_event(SseEvent("synth_token", {"delta": chunk.delta}))

    yield format_event(SseEvent("synth_done", {"tokens": total_tokens}))

    if not primal:
        return

    # --- Primal Protocol second pass ---
    # Collect full synthesis text (already accumulated above)
    full_synthesis = "".join(synth_parts)

    # Primal system prompt is also cached — it's invariant across requests.
    primal_messages: list[Message] = [
        Message(role="system", content=_PRIMAL_SYSTEM, cache=True),
        Message(role="user", content=_build_primal_user_message(full_synthesis)),
    ]

    caveman_parts: list[str] = []
    async for chunk in apex_client.stream(primal_messages):
        if chunk.delta:
            caveman_parts.append(chunk.delta)

    caveman_text = "".join(caveman_parts)
    yield format_event(SseEvent("primal", {"text": caveman_text}))
