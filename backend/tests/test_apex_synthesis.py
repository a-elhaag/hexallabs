"""Tests for Apex synthesis module (backend/app/synthesis/apex.py).

Covers:
- Event ordering: synth_start → synth_token(s) → synth_done
- synth_done carries tokens field
- primal=True emits primal event after synth_done
- primal=False does NOT emit primal event
- Multiple council responses are anonymized (no whitelabel leakage in messages)
- synthesize() accepts a pre-constructed client, never calls get_client()
"""
from __future__ import annotations

import pytest

from app.synthesis.apex import ModelResponse, synthesize
from tests.conftest import FakeClient, parse_sse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _collect(ait) -> list[tuple[str, dict]]:
    """Collect all SSE bytes from an async iterator and parse them."""
    chunks: list[bytes] = []
    async for chunk in ait:
        chunks.append(chunk)
    body = b"".join(chunks).decode()
    return parse_sse(body)


def _make_responses(n: int = 2) -> list[ModelResponse]:
    whitelabels = ["Swift", "Prism", "Depth", "Atlas", "Horizon"]
    return [
        ModelResponse(
            whitelabel=whitelabels[i % len(whitelabels)],
            text=f"Council response {i+1}. This is the answer from model {i+1}.",
            confidence=8 - i,
            tokens=50 + i * 10,
            cached_tokens=5,
        )
        for i in range(n)
    ]


# ---------------------------------------------------------------------------
# Event ordering tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_synthesize_event_order():
    """synth_start comes first, then synth_token(s), then synth_done."""
    client = FakeClient(deltas=["Hello", " world", "!"], whitelabel="Apex", total=20)
    events = await _collect(
        synthesize(client, "What is 2+2?", _make_responses())
    )

    event_names = [name for name, _ in events]
    assert event_names[0] == "synth_start"
    assert event_names[-1] == "synth_done"
    # All events between first and last must be synth_token
    middle = event_names[1:-1]
    assert all(name == "synth_token" for name in middle), f"Unexpected events in middle: {middle}"


@pytest.mark.asyncio
async def test_synthesize_emits_synth_start():
    client = FakeClient(deltas=["response"], whitelabel="Apex", total=10)
    events = await _collect(synthesize(client, "query", _make_responses()))

    assert events[0][0] == "synth_start"
    assert events[0][1] == {}


@pytest.mark.asyncio
async def test_synthesize_emits_synth_token_per_delta():
    deltas = ["token1", " token2", " token3"]
    client = FakeClient(deltas=deltas, whitelabel="Apex", total=15)
    events = await _collect(synthesize(client, "query", _make_responses()))

    token_events = [(name, data) for name, data in events if name == "synth_token"]
    assert len(token_events) == len(deltas)
    for i, (name, data) in enumerate(token_events):
        assert data["delta"] == deltas[i]


# ---------------------------------------------------------------------------
# synth_done payload
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_synth_done_has_tokens_field():
    """synth_done payload must include 'tokens' key."""
    expected_tokens = 42
    client = FakeClient(deltas=["answer"], whitelabel="Apex", total=expected_tokens)
    events = await _collect(synthesize(client, "query", _make_responses()))

    done_events = [(name, data) for name, data in events if name == "synth_done"]
    assert len(done_events) == 1
    assert "tokens" in done_events[0][1]
    assert done_events[0][1]["tokens"] == expected_tokens


@pytest.mark.asyncio
async def test_synth_done_tokens_zero_when_client_returns_none():
    """If client never emits total_tokens, synth_done tokens should be 0."""
    # FakeClient with total=0 simulates no usage chunk
    client = FakeClient(deltas=["answer"], whitelabel="Apex", total=0, cached=0)
    events = await _collect(synthesize(client, "query", _make_responses()))

    done_events = [(name, data) for name, data in events if name == "synth_done"]
    assert len(done_events) == 1
    assert done_events[0][1]["tokens"] == 0


# ---------------------------------------------------------------------------
# Primal Protocol
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_primal_true_emits_primal_event():
    """With primal=True, a 'primal' event must be emitted after synth_done."""
    client = FakeClient(
        deltas=["caveman", " answer"], whitelabel="Apex", total=30
    )
    events = await _collect(
        synthesize(client, "Tell me about the universe", _make_responses(), primal=True)
    )

    event_names = [name for name, _ in events]
    assert "primal" in event_names

    # primal must come AFTER synth_done
    synth_done_idx = event_names.index("synth_done")
    primal_idx = event_names.index("primal")
    assert primal_idx > synth_done_idx, "primal event must come after synth_done"


@pytest.mark.asyncio
async def test_primal_true_event_has_text_field():
    """primal event payload must have 'text' field with non-empty caveman string."""
    client = FakeClient(
        deltas=["fire", " good"], whitelabel="Apex", total=25
    )
    events = await _collect(
        synthesize(client, "query", _make_responses(), primal=True)
    )

    primal_events = [(name, data) for name, data in events if name == "primal"]
    assert len(primal_events) == 1
    payload = primal_events[0][1]
    assert "text" in payload
    assert isinstance(payload["text"], str)
    # FakeClient emits "fire good" so that should be the collected text
    assert payload["text"] == "fire good"


@pytest.mark.asyncio
async def test_primal_false_does_not_emit_primal_event():
    """With primal=False (default), no 'primal' event must be emitted."""
    client = FakeClient(deltas=["answer"], whitelabel="Apex", total=10)
    events = await _collect(synthesize(client, "query", _make_responses()))

    event_names = [name for name, _ in events]
    assert "primal" not in event_names


@pytest.mark.asyncio
async def test_primal_default_is_false():
    """synthesize() primal kwarg defaults to False — no primal event."""
    client = FakeClient(deltas=["answer"], whitelabel="Apex", total=10)
    # Call without primal kwarg
    events = await _collect(synthesize(client, "query", _make_responses()))

    event_names = [name for name, _ in events]
    assert "primal" not in event_names


# ---------------------------------------------------------------------------
# Full sequence with primal=True
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_full_event_sequence_with_primal():
    """Full order: synth_start → synth_token(s) → synth_done → primal."""
    client = FakeClient(
        deltas=["synthesis", " text"], whitelabel="Apex", total=50
    )
    events = await _collect(
        synthesize(client, "complex query", _make_responses(3), primal=True)
    )

    event_names = [name for name, _ in events]
    assert event_names[0] == "synth_start"
    assert event_names[-1] == "primal"
    assert "synth_done" in event_names
    synth_done_idx = event_names.index("synth_done")
    # Everything between synth_start (exclusive) and synth_done (exclusive) is synth_token
    middle = event_names[1:synth_done_idx]
    assert all(name == "synth_token" for name in middle)


# ---------------------------------------------------------------------------
# Whitelabel / anonymization guard
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_whitelabel_names_not_in_user_message():
    """ModelResponse whitelabel names must NOT appear in the message sent to Apex.

    We verify by capturing what messages are streamed to the client.
    """
    captured_messages: list = []

    class SpyClient:
        whitelabel = "Apex"

        async def stream(self, messages, cache_key=None, tools=None):
            captured_messages.extend(messages)
            yield __import__("app.llm.base", fromlist=["StreamChunk"]).StreamChunk(
                delta="ok", total_tokens=5
            )

    responses = [
        ModelResponse(whitelabel="Swift", text="Swift response", confidence=9, tokens=20, cached_tokens=0),
        ModelResponse(whitelabel="Depth", text="Depth response", confidence=7, tokens=30, cached_tokens=0),
    ]

    events = await _collect(synthesize(SpyClient(), "test query", responses))  # type: ignore[arg-type]

    # Check user message content doesn't contain whitelabel names used as identifiers
    user_messages = [m for m in captured_messages if m.role == "user"]
    assert user_messages, "Expected at least one user message"
    user_content = user_messages[0].content

    # White-label names must not appear as model *headers/identifiers* in the prompt.
    # They may legitimately appear inside response body text (e.g. "Swift response"),
    # but must never be used as the section header label like "### Swift (confidence: ...)".
    assert "### Swift" not in user_content, "Whitelabel 'Swift' used as section header"
    assert "### Depth" not in user_content, "Whitelabel 'Depth' used as section header"
    # Anonymous labels must be used instead
    assert "### Model A" in user_content
    assert "### Model B" in user_content


# ---------------------------------------------------------------------------
# System prompt caching
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_system_prompt_has_cache_true():
    """System message must have cache=True for Anthropic prefix caching."""
    captured_messages: list = []

    class SpyClient:
        whitelabel = "Apex"

        async def stream(self, messages, cache_key=None, tools=None):
            captured_messages.extend(messages)
            yield __import__("app.llm.base", fromlist=["StreamChunk"]).StreamChunk(
                delta="result", total_tokens=10
            )

    await _collect(synthesize(SpyClient(), "query", _make_responses()))  # type: ignore[arg-type]

    system_messages = [m for m in captured_messages if m.role == "system"]
    assert system_messages, "Expected at least one system message"
    assert system_messages[0].cache is True, "Apex synthesis system prompt must have cache=True"


@pytest.mark.asyncio
async def test_primal_system_prompt_has_cache_true():
    """Primal system prompt must also have cache=True."""
    call_count = 0
    all_messages: list[list] = []

    class SpyClient:
        whitelabel = "Apex"

        async def stream(self, messages, cache_key=None, tools=None):
            nonlocal call_count
            call_count += 1
            all_messages.append(list(messages))
            yield __import__("app.llm.base", fromlist=["StreamChunk"]).StreamChunk(
                delta="caveman", total_tokens=8
            )

    await _collect(synthesize(SpyClient(), "query", _make_responses(), primal=True))  # type: ignore[arg-type]

    # Two stream calls: synthesis + primal
    assert call_count == 2, f"Expected 2 stream calls (synth + primal), got {call_count}"

    primal_call_messages = all_messages[1]
    primal_system = [m for m in primal_call_messages if m.role == "system"]
    assert primal_system, "Primal call must have a system message"
    assert primal_system[0].cache is True, "Primal system prompt must have cache=True"


# ---------------------------------------------------------------------------
# Empty / edge cases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_synthesize_with_single_response():
    """Single council response should work fine."""
    client = FakeClient(deltas=["answer"], whitelabel="Apex", total=5)
    events = await _collect(synthesize(client, "q", _make_responses(1)))

    event_names = [name for name, _ in events]
    assert "synth_start" in event_names
    assert "synth_done" in event_names


@pytest.mark.asyncio
async def test_synthesize_no_deltas():
    """Client that emits no deltas: synth_start + synth_done, no synth_token."""
    client = FakeClient(deltas=[], whitelabel="Apex", total=0, cached=0)
    events = await _collect(synthesize(client, "q", _make_responses()))

    event_names = [name for name, _ in events]
    assert event_names == ["synth_start", "synth_done"]
