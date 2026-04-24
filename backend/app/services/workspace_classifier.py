"""
Workspace classifier — picks the best UI kind for a user query.

Runs BEFORE the main council/oracle fanout. One fast call to Swift
(gpt-5.4-mini) returns a single kind + short reason. The frontend uses the
kind to swap the main pane (code editor, spreadsheet, diagram, long doc, or
default chat feed).

Falls back to "chat" on any ambiguity, parse failure, or low confidence —
chat is a zero-regression default.
"""

from __future__ import annotations

import json
import logging

from app.services import foundry
from app.sse.events import WORKSPACE_KINDS

log = logging.getLogger(__name__)

CLASSIFIER_MODEL = "gpt-5.4-mini"  # Swift

_SYSTEM_PROMPT = (
    "You choose the best UI workspace for a user's query. Pick exactly one kind:\n"
    "- code: user wants code written, edited, debugged, or explained in an editor view\n"
    "- spreadsheet: user wants tabular data, comparisons, numeric analysis, or anything that fits a grid\n"
    "- diagram: user wants a visual — architecture, flowchart, sequence, entity relationships\n"
    "- document: user wants a long-form write-up — essay, report, tutorial, spec (>~500 words)\n"
    "- chat: anything else — simple Q&A, short answers, conversational replies\n"
    "\n"
    "Respond with JSON only: {\"kind\":\"<one>\",\"reason\":\"<<=12 words>\"}.\n"
    "Default to \"chat\" when unsure."
)


async def classify(query: str) -> dict[str, str]:
    """Return {"kind": <WORKSPACE_KIND>, "reason": <str>}. Never raises."""
    try:
        raw = await foundry.complete(
            model=CLASSIFIER_MODEL,
            system_prompt=_SYSTEM_PROMPT,
            user_message=query,
        )
        data = _parse(raw)
        kind = data.get("kind")
        if kind not in WORKSPACE_KINDS:
            return {"kind": "chat", "reason": "fallback: unknown kind"}
        reason = str(data.get("reason") or "").strip()[:120]
        return {"kind": kind, "reason": reason or "classifier pick"}
    except Exception as exc:
        log.warning("workspace classifier failed, defaulting to chat: %s", exc)
        return {"kind": "chat", "reason": "fallback: classifier error"}


def _parse(raw: str) -> dict:
    raw = raw.strip()
    # Tolerate fenced blocks like ```json ... ```
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1:
        return {}
    return json.loads(raw[start : end + 1])
