from __future__ import annotations

import logging

from app.llm.base import LLMClient, Message
from app.relay.triggers import CONF_RE, MARKER_RE, TriggerFired

logger = logging.getLogger(__name__)

_SHORT_THRESHOLD = 600  # chars — summarise only when strictly above this

_RELAY_B_SYSTEM = """You are continuing an assistant response that was handed off to you mid-generation. The original assistant began answering but transferred control to you. Your job is to continue seamlessly and naturally, as if you were always the one answering. Do not say "as the previous assistant said" or acknowledge the handoff. Just continue the response."""

_APEX_SUMMARISER_CACHE_KEY = "relay_apex_summariser_v1"

_APEX_SUMMARISER_SYSTEM = """You are a precise summariser. Given a partial assistant response, produce a single sentence (max 30 words) that captures the core reasoning or conclusion so far. Output only the summary sentence, nothing else."""


async def build_baton(
    apex: LLMClient,
    original_prompt: str,
    partial_a: str,
    trigger: TriggerFired,
    whitelabel_a: str,
    whitelabel_b: str,
) -> list[Message]:
    """Build the message list for model B. Strips sentinels, adapts context depth."""
    stripped = _strip_sentinels(partial_a)

    parts: list[str] = [
        f"The user originally asked:\n\n{original_prompt}",
        f"Another assistant ({whitelabel_a}) began answering but handed off because: {trigger.reason}",
        f"Here is everything {whitelabel_a} produced before handing off:\n\n{stripped}",
    ]

    if len(stripped) > _SHORT_THRESHOLD:
        try:
            summary = await _apex_summarise(apex, stripped)
            parts.append(f"Summary of {whitelabel_a}'s reasoning so far: {summary}")
        except Exception:
            logger.warning("baton: apex summarise failed, omitting summary")

    parts.append(
        f"Continue seamlessly from where {whitelabel_a} left off. "
        "Do not repeat the previous content verbatim. Build on it."
    )

    return [
        Message(role="system", content=_RELAY_B_SYSTEM, cache=True),
        Message(role="user", content="\n\n".join(parts)),
    ]


def _strip_sentinels(text: str) -> str:
    """Remove [[HANDOFF:...]] and [[CONF:...]] sentinels from text."""
    text = MARKER_RE.sub("", text)
    text = CONF_RE.sub("", text)
    return text.strip()


async def _apex_summarise(apex: LLMClient, text: str) -> str:
    """Ask Apex for a one-sentence summary of model A's partial output."""
    messages = [
        Message(role="system", content=_APEX_SUMMARISER_SYSTEM, cache=True),
        Message(role="user", content=f"Partial response to summarise:\n\n{text}"),
    ]
    collected: list[str] = []
    async for chunk in apex.stream(messages, cache_key=_APEX_SUMMARISER_CACHE_KEY):
        if chunk.delta:
            collected.append(chunk.delta)
    return "".join(collected).strip()
