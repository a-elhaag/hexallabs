from __future__ import annotations

import json

import pytest

from app.sse import HEARTBEAT, SseEvent, format_event


def test_format_event_shape() -> None:
    wire = format_event(SseEvent("session", {"session_id": "abc", "mode": "oracle"}))
    text = wire.decode()
    assert text.startswith("event: session\n")
    assert text.endswith("\n\n")
    payload = text.split("data: ", 1)[1].rstrip("\n")
    assert json.loads(payload) == {"session_id": "abc", "mode": "oracle"}


def test_format_event_uses_compact_json() -> None:
    wire = format_event(SseEvent("token", {"hex": "Apex", "delta": "hi"}))
    assert b'"hex":"Apex"' in wire  # no spaces around colons / commas


def test_unknown_event_rejected() -> None:
    with pytest.raises(ValueError):
        SseEvent("not_a_real_event", {})


def test_heartbeat_is_sse_comment() -> None:
    assert HEARTBEAT == b": keep-alive\n\n"
