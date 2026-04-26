"""SSE event schema for Hexal-LM streaming.

All modes (Oracle, Council, Relay, Workflow) emit the same event vocabulary so
the frontend has a single consumer.

Event payloads
--------------
session        {session_id: str, mode: str}
prompt_forge   {original: str, improved: str}
hex_start      {hex: str}
token          {hex: str, delta: str}
confidence     {hex: str, score: int, stage: "initial"|"post_review"}
peer_review    {from: str, to: str, critique: str}
hex_done       {hex: str, tokens: int, cached_tokens: int}
synth_start    {}
synth_token    {delta: str}
synth_done     {tokens: int}
lens           {hex: str, interpretation: str}
primal         {text: str}
relay_handoff  {from: str, to: str, trigger: "marker"|"confidence"|"apex", reason: str, partial_chars: int}
tool_call      {hex: str, id: str, name: str, input: dict, forced?: bool}
tool_result    {hex: str, id: str, name: str, summary: str, urls: [str], result_count: int, error?: str}
quota_warning  {percentage_used: float, resets_at: str}
done           {session_id: str, duration_ms: int}
error          {hex: str, code: str, message: str}
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

HEARTBEAT: bytes = b": keep-alive\n\n"

_ALLOWED_EVENTS = {
    "session",
    "prompt_forge",
    "hex_start",
    "token",
    "confidence",
    "peer_review",
    "hex_done",
    "synth_start",
    "synth_token",
    "synth_done",
    "lens",
    "primal",
    "relay_handoff",
    "tool_call",
    "tool_result",
    "quota_warning",
    "done",
    "error",
}


@dataclass(frozen=True, slots=True)
class SseEvent:
    event: str
    data: dict[str, Any]

    def __post_init__(self) -> None:
        if self.event not in _ALLOWED_EVENTS:
            raise ValueError(f"unknown SSE event {self.event!r}; see hexal-sse-contract")


def format_event(evt: SseEvent) -> bytes:
    """Serialize an SseEvent to the SSE wire format: `event: <name>\ndata: <json>\n\n`."""
    payload = json.dumps(evt.data, separators=(",", ":"), ensure_ascii=False)
    return f"event: {evt.event}\ndata: {payload}\n\n".encode()
