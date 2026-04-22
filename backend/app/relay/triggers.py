from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass
from typing import Literal

from app.llm.base import LLMClient, Message

logger = logging.getLogger(__name__)

MARKER_RE = re.compile(r"\[\[HANDOFF:([^\]]{0,200})\]\]")
CONF_RE = re.compile(r"\[\[CONF:([0-9]{1,2})\]\]")

_TAIL_WINDOW = 512  # chars to search for partial sentinel detection


@dataclass(frozen=True)
class TriggerFired:
    kind: Literal["marker", "confidence", "apex"]
    reason: str


def scan_marker(buffer: str) -> TriggerFired | None:
    """Search buffer tail for [[HANDOFF:reason]] sentinel."""
    tail = buffer[-_TAIL_WINDOW:] if len(buffer) > _TAIL_WINDOW else buffer
    m = MARKER_RE.search(tail)
    if m:
        return TriggerFired("marker", m.group(1))
    return None


def scan_confidence(buffer: str, threshold: int = 4) -> TriggerFired | None:
    """Search buffer for [[CONF:N]] self-ratings; trigger if latest <= threshold."""
    tail = buffer[-_TAIL_WINDOW:] if len(buffer) > _TAIL_WINDOW else buffer
    scores = [int(x) for x in CONF_RE.findall(tail)]
    if scores and scores[-1] <= threshold:
        return TriggerFired("confidence", f"self_score={scores[-1]}")
    return None


_APEX_WATCHER_SYSTEM = """You are a relay watcher. Given a partial answer from an assistant, decide if the assistant is going off-track, hallucinating, or clearly out of its depth. Respond with ONLY valid JSON: {"handoff": true|false, "reason": "short reason string"}. Be decisive."""

_APEX_WATCHER_CACHE_KEY = "relay_apex_watcher_v1"


async def apex_watcher(
    apex: LLMClient,
    buffer_ref: list[str],
    fire_event: asyncio.Event,
    reason_box: list[str],
    poll_interval: float = 2.0,
    min_chars: int = 300,
) -> None:
    """Poll partial_a buffer; ask Apex if model A is off-track. Sets fire_event if handoff needed."""
    try:
        while not fire_event.is_set():
            await asyncio.sleep(poll_interval)
            if fire_event.is_set():
                return
            snapshot = "".join(buffer_ref)
            if len(snapshot) < min_chars:
                continue
            try:
                verdict = await _apex_verdict(apex, snapshot)
            except Exception:
                logger.exception("apex_watcher: verdict call failed, continuing")
                continue
            if verdict.get("handoff"):
                if not reason_box:
                    reason_box.append(verdict.get("reason", "apex flagged off-track"))
                fire_event.set()
                return
    except asyncio.CancelledError:
        pass
    except Exception:
        logger.exception("apex_watcher: unexpected error, watcher exiting")


async def _apex_verdict(apex: LLMClient, snapshot: str) -> dict:
    """Ask Apex to judge whether model A should hand off. Returns {"handoff": bool, "reason": str}."""
    messages = [
        Message(role="system", content=_APEX_WATCHER_SYSTEM, cache=True),
        Message(role="user", content=f"Partial answer so far:\n\n{snapshot}\n\nShould the assistant hand off?"),
    ]
    collected: list[str] = []
    async for chunk in apex.stream(messages, cache_key=_APEX_WATCHER_CACHE_KEY):
        if chunk.delta:
            collected.append(chunk.delta)
    raw = "".join(collected).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # If Apex doesn't return valid JSON, don't trigger handoff
        logger.warning("apex_watcher: non-JSON response %r", raw[:200])
        return {"handoff": False, "reason": ""}
