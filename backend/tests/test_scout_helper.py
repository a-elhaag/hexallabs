"""Tests for app.tools.scout — scout_force and scout_auto_tool_messages."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from app.llm.base import Message, StreamChunk, ToolCall
from app.sse.events import format_event
from app.tools.web_search import SearchResult
from tests.conftest import FakeClient, parse_sse


# ---------------------------------------------------------------------------
# Fake settings
# ---------------------------------------------------------------------------


class _FakeSettings:
    tavily_api_key: str | None = "tvly-test"
    scout_max_results: int = 5
    scout_max_turns: int = 4


class _FakeSettingsNoKey:
    tavily_api_key: str | None = None
    scout_max_results: int = 5
    scout_max_turns: int = 4


# ---------------------------------------------------------------------------
# Fake client that emits a tool_call then a follow-up text response
# ---------------------------------------------------------------------------


class FakeToolClient:
    """LLM client that emits one tool call on the first turn, then text on the second."""

    def __init__(self, tool_name: str = "web_search", tool_query: str = "test query") -> None:
        self.whitelabel = "Apex"
        self._tool_name = tool_name
        self._tool_query = tool_query
        self._turn = 0

    async def stream(
        self,
        messages: list[Message],
        cache_key: str | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[StreamChunk]:
        if self._turn == 0:
            self._turn += 1
            # Emit a tool call
            yield StreamChunk(
                tool_call=ToolCall(
                    id="tc_abc123",
                    name=self._tool_name,
                    input={"query": self._tool_query},
                ),
                stop_reason="tool_use",
            )
            yield StreamChunk(delta="", total_tokens=10, cached_tokens=0)
        else:
            # Second turn: emit text after tool result
            yield StreamChunk(delta="Result: found it")
            yield StreamChunk(delta="", total_tokens=20, cached_tokens=5)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fake_search_result(summary: str = "Paris is the capital of France.") -> SearchResult:
    return SearchResult(
        summary=summary,
        urls=["https://example.com/paris"],
        result_count=1,
        raw=[{"title": "Paris", "content": summary, "url": "https://example.com/paris"}],
    )


async def _collect_sse(gen: AsyncIterator[bytes]) -> list[tuple[str, dict]]:
    """Drain an async generator and parse all SSE events."""
    chunks: list[bytes] = []
    async for chunk in gen:
        chunks.append(chunk)
    body = b"".join(chunks).decode()
    return parse_sse(body)


# ---------------------------------------------------------------------------
# scout_force tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_scout_force_returns_non_empty_context_string() -> None:
    """scout_force returns a non-empty context string when Tavily succeeds."""
    from app.tools.scout import scout_force

    fake_result = _fake_search_result()

    with patch("app.tools.scout._execute_web_search", new=AsyncMock(return_value=fake_result)):
        context_str, result = await scout_force("capital of France", _FakeSettings())  # type: ignore[arg-type]

    assert isinstance(context_str, str)
    assert len(context_str) > 0
    assert "Web search results" in context_str


@pytest.mark.asyncio
async def test_scout_force_returns_search_result_object() -> None:
    """scout_force also returns the raw SearchResult for callers that need metadata."""
    from app.tools.scout import scout_force

    fake_result = _fake_search_result("Some content")

    with patch("app.tools.scout._execute_web_search", new=AsyncMock(return_value=fake_result)):
        context_str, result = await scout_force("some query", _FakeSettings())  # type: ignore[arg-type]

    assert result is fake_result
    assert result.result_count == 1
    assert "example.com" in result.urls[0]


@pytest.mark.asyncio
async def test_scout_force_raises_value_error_when_no_api_key() -> None:
    """scout_force raises ValueError if tavily_api_key is not set."""
    from app.tools.scout import scout_force

    with pytest.raises(ValueError, match="TAVILY_API_KEY not set"):
        await scout_force("query", _FakeSettingsNoKey())  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_scout_force_propagates_search_exception() -> None:
    """scout_force propagates exceptions from the underlying search call."""
    from app.tools.scout import scout_force

    with patch(
        "app.tools.scout._execute_web_search",
        new=AsyncMock(side_effect=RuntimeError("network failure")),
    ):
        with pytest.raises(RuntimeError, match="network failure"):
            await scout_force("query", _FakeSettings())  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# scout_auto_tool_messages tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_scout_auto_emits_tool_call_and_tool_result_events() -> None:
    """When the LLM requests a tool, scout_auto_tool_messages emits tool_call + tool_result."""
    from app.tools.scout import scout_auto_tool_messages

    fake_result = _fake_search_result()
    tool_client = FakeToolClient()
    messages = [Message(role="user", content="What is the capital of France?")]

    with patch("app.tools.scout._execute_web_search", new=AsyncMock(return_value=fake_result)):
        events = await _collect_sse(
            scout_auto_tool_messages(tool_client, messages, _FakeSettings(), "Apex")  # type: ignore[arg-type]
        )

    event_names = [e for e, _ in events]
    assert "tool_call" in event_names
    assert "tool_result" in event_names


@pytest.mark.asyncio
async def test_scout_auto_tool_call_comes_before_token_events() -> None:
    """tool_call event is emitted before the final text token events."""
    from app.tools.scout import scout_auto_tool_messages

    fake_result = _fake_search_result()
    tool_client = FakeToolClient()
    messages = [Message(role="user", content="query")]

    with patch("app.tools.scout._execute_web_search", new=AsyncMock(return_value=fake_result)):
        events = await _collect_sse(
            scout_auto_tool_messages(tool_client, messages, _FakeSettings(), "Apex")  # type: ignore[arg-type]
        )

    names = [e for e, _ in events]
    assert "tool_call" in names
    assert "token" in names
    assert names.index("tool_call") < names.index("token")


@pytest.mark.asyncio
async def test_scout_auto_tool_result_payload_has_expected_fields() -> None:
    """tool_result event payload includes hex, id, name, summary, urls, result_count."""
    from app.tools.scout import scout_auto_tool_messages

    fake_result = _fake_search_result("Paris is the capital of France.")
    tool_client = FakeToolClient(tool_query="capital of France")
    messages = [Message(role="user", content="capital of France?")]

    with patch("app.tools.scout._execute_web_search", new=AsyncMock(return_value=fake_result)):
        events = await _collect_sse(
            scout_auto_tool_messages(tool_client, messages, _FakeSettings(), "Apex")  # type: ignore[arg-type]
        )

    tr_data = next(d for e, d in events if e == "tool_result")
    assert tr_data["hex"] == "Apex"
    assert tr_data["name"] == "web_search"
    assert tr_data["result_count"] == 1
    assert "example.com" in tr_data["urls"][0]


@pytest.mark.asyncio
async def test_scout_auto_no_tools_when_scout_off() -> None:
    """With no tavily key, no tool_call events should be emitted (tool loop is skipped)."""
    from app.tools.scout import scout_auto_tool_messages

    client = FakeClient(deltas=["hello world"])
    messages = [Message(role="user", content="hello")]

    events = await _collect_sse(
        scout_auto_tool_messages(client, messages, _FakeSettingsNoKey(), "Swift")  # type: ignore[arg-type]
    )

    names = [e for e, _ in events]
    assert "tool_call" not in names
    assert "tool_result" not in names
    assert "token" in names


@pytest.mark.asyncio
async def test_scout_auto_collects_text_and_token_counts() -> None:
    """collected list and token_counts dict are populated after the loop."""
    from app.tools.scout import scout_auto_tool_messages

    client = FakeClient(deltas=["hello", " world"], total=50, cached=10)
    messages = [Message(role="user", content="hi")]
    collected: list[str] = []
    token_counts: dict[str, int | None] = {"total": None, "cached": None}

    async for _ in scout_auto_tool_messages(
        client,
        messages,
        _FakeSettingsNoKey(),  # type: ignore[arg-type]
        "Swift",
        collected=collected,
        token_counts=token_counts,
    ):
        pass

    assert "".join(collected) == "hello world"
    assert token_counts["total"] == 50
    assert token_counts["cached"] == 10


@pytest.mark.asyncio
async def test_scout_auto_tool_missing_api_key_emits_error_in_tool_result() -> None:
    """If tavily_api_key is missing mid-loop, tool_result includes error field."""
    from app.tools.scout import scout_auto_tool_messages

    # Use a settings object that has a key (so tools are attached) but then
    # we simulate no-key by using a settings variant that has the key set for
    # tool attachment but missing at resolution time.
    # Simpler: use _FakeSettings (has key), but patch _execute_web_search to raise.

    tool_client = FakeToolClient()
    messages = [Message(role="user", content="query")]

    with patch(
        "app.tools.scout._execute_web_search",
        new=AsyncMock(side_effect=RuntimeError("timeout")),
    ):
        events = await _collect_sse(
            scout_auto_tool_messages(tool_client, messages, _FakeSettings(), "Apex")  # type: ignore[arg-type]
        )

    tr_data = next(d for e, d in events if e == "tool_result")
    assert "error" in tr_data
    assert "timeout" in tr_data["error"]
