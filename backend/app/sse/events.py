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
