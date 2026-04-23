"""Scout helpers — reusable web-search injection for Oracle, Council, Relay, Workflow.

Public API
----------
scout_force(query, settings)
    Pre-execute web search and return a context string to inject as a system
    message before calling the LLM.

scout_auto_tool_messages(client, messages, settings, hex_name)
    Run the agentic tool-use loop with the Scout tool available.  Yields SSE
    bytes (tool_call, tool_result, token events).  Caller wraps with
    hex_start / hex_done.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

from app.llm.base import LLMClient, Message, ToolCall
from app.sse import SseEvent, _TokenCarry, _ToolCallCarry, _client_tokens, _with_heartbeat, format_event
from app.tools.registry import anthropic_schema, openai_schema
from app.tools.web_search import WEB_SEARCH_SPEC, SearchResult, execute_web_search, format_search_context

if TYPE_CHECKING:
    from app.config import Settings


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _execute_web_search(
    query: str,
    max_results: int,
    api_key: str,
) -> SearchResult:
    """Thin wrapper around execute_web_search — kept private to this module."""
    return await execute_web_search(query, max_results, api_key=api_key)


def _build_tools_for_client(client: object) -> list[dict[str, Any]]:
    """Render the web_search tool in the correct schema for this client's provider."""
    from app.llm.anthropic_client import AnthropicClient
    from app.llm.azure_client import AzureFoundryClient

    if isinstance(client, AnthropicClient):
        return [anthropic_schema(WEB_SEARCH_SPEC, cache=True)]
    if isinstance(client, AzureFoundryClient):
        return [openai_schema(WEB_SEARCH_SPEC)]
    # Fallback: use Anthropic shape
    return [anthropic_schema(WEB_SEARCH_SPEC, cache=True)]


async def _dispatch_tool(
    tc: ToolCall,
    *,
    tavily_api_key: str,
    scout_max_results: int,
) -> SearchResult:
    if tc.name == "web_search":
        query_str = tc.input.get("query", "")
        max_results = int(tc.input.get("max_results", scout_max_results))
        return await _execute_web_search(query_str, max_results, api_key=tavily_api_key)
    raise ValueError(f"unknown tool: {tc.name!r}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def scout_force(
    query: str,
    settings: "Settings",
) -> tuple[str, SearchResult]:
    """Pre-execute web search, return ``(context_str, result)`` for injection.

    ``context_str`` should be injected as a system message (role="system",
    cache=True) before the user message.  ``result`` carries the raw
    SearchResult for callers that need to emit a ``tool_result`` SSE event.

    Raises
    ------
    ValueError
        If TAVILY_API_KEY is not configured.
    Exception
        Propagates any error from the underlying search call so callers can
        catch and emit an appropriate SSE error event.
    """
    if not settings.tavily_api_key:
        raise ValueError("TAVILY_API_KEY not set")

    result = await _execute_web_search(
        query,
        settings.scout_max_results,
        api_key=settings.tavily_api_key,
    )
    return format_search_context(result), result


async def scout_auto_tool_messages(
    client: object,
    messages: list[Message],
    settings: "Settings",
    hex_name: str,
    *,
    with_tools: bool = True,
    collected: list[str] | None = None,
    token_counts: dict[str, int | None] | None = None,
) -> AsyncIterator[bytes]:
    """Run agentic tool-use loop with Scout tool available.

    Yields SSE bytes (tool_call, tool_result, token events).
    Caller wraps with hex_start / hex_done.

    Parameters
    ----------
    client:
        LLM client instance (AnthropicClient or AzureFoundryClient).
    messages:
        Conversation messages so far.  This list is mutated in-place as
        assistant + tool turns accumulate.
    settings:
        Application settings (for tavily_api_key, scout_max_results,
        scout_max_turns).
    hex_name:
        Whitelabel model name used in SSE event payloads.
    with_tools:
        Whether to attach the Scout tool to the request.  Set to False for
        ``scout="off"`` so that no tool schema is sent to the LLM.
    collected:
        Optional list to accumulate all text deltas across turns.
    token_counts:
        Optional dict with keys ``"total"`` and ``"cached"``.  If provided,
        the final token counts from the last LLM turn are written here so the
        caller can use them for hex_done / DB persistence.

    Yields
    ------
    bytes
        Raw SSE-encoded event bytes ready to send to the client.

    Returns (via StopAsyncIteration)
    ----------------------------------
    The generator raises StopAsyncIteration when the loop completes
    (no pending tool calls, or max_turns exhausted).  Callers should
    follow up with hex_done / done events.
    """
    tools_arg: list[dict[str, Any]] | None = None
    if with_tools and settings.tavily_api_key:
        tools_arg = _build_tools_for_client(client)

    for _turn in range(settings.scout_max_turns):
        pending_tool_calls: list[ToolCall] = []
        turn_text: list[str] = []

        async for sse_chunk in _with_heartbeat(
            _client_tokens(client, messages, hex_name, turn_text, tools=tools_arg)
        ):
            if isinstance(sse_chunk, _TokenCarry):
                if token_counts is not None:
                    token_counts["total"] = sse_chunk.total_tokens
                    token_counts["cached"] = sse_chunk.cached_tokens
                continue
            if isinstance(sse_chunk, _ToolCallCarry):
                tc = sse_chunk.tool_call
                pending_tool_calls.append(tc)
                yield format_event(SseEvent("tool_call", {
                    "hex": hex_name,
                    "id": tc.id,
                    "name": tc.name,
                    "input": tc.input,
                }))
                continue
            # Raw bytes (token SSE event)
            yield sse_chunk

        if collected is not None:
            collected.extend(turn_text)

        if not pending_tool_calls:
            break

        # Append assistant turn with tool_calls, then resolve each tool.
        messages.append(Message(
            role="assistant",
            content="".join(turn_text),
            tool_calls=tuple(pending_tool_calls),
        ))

        for tc in pending_tool_calls:
            if not settings.tavily_api_key:
                err_msg = "TAVILY_API_KEY not set"
                yield format_event(SseEvent("tool_result", {
                    "hex": hex_name,
                    "id": tc.id,
                    "name": tc.name,
                    "summary": "",
                    "urls": [],
                    "result_count": 0,
                    "error": err_msg,
                }))
                messages.append(Message(
                    role="tool",
                    content=json.dumps({"error": err_msg}),
                    tool_use_id=tc.id,
                ))
                continue

            try:
                result = await _dispatch_tool(
                    tc,
                    tavily_api_key=settings.tavily_api_key,
                    scout_max_results=settings.scout_max_results,
                )
                yield format_event(SseEvent("tool_result", {
                    "hex": hex_name,
                    "id": tc.id,
                    "name": tc.name,
                    "summary": result.summary,
                    "urls": result.urls,
                    "result_count": result.result_count,
                }))
                messages.append(Message(
                    role="tool",
                    content=json.dumps({
                        "summary": result.summary,
                        "urls": result.urls,
                        "results": result.raw,
                    }),
                    tool_use_id=tc.id,
                ))
            except Exception as e:
                err_msg = str(e)[:500]
                yield format_event(SseEvent("tool_result", {
                    "hex": hex_name,
                    "id": tc.id,
                    "name": tc.name,
                    "summary": "",
                    "urls": [],
                    "result_count": 0,
                    "error": err_msg,
                }))
                messages.append(Message(
                    role="tool",
                    content=json.dumps({"error": err_msg}),
                    tool_use_id=tc.id,
                ))
