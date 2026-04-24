#!/usr/bin/env python3
"""Live API tests: all models + Scout web search tool."""

from __future__ import annotations

import asyncio
import sys

from app.config import get_settings
from app.llm.anthropic_client import AnthropicClient
from app.llm.azure_client import AzureFoundryClient
from app.llm.base import Message
from app.tools.registry import anthropic_schema, openai_schema
from app.tools.web_search import WEB_SEARCH_SPEC, execute_web_search

_PASS = "✓"
_FAIL = "✗"
_results: list[tuple[str, bool, str]] = []


def _ok(name: str, detail: str = "") -> None:
    print(f"  {_PASS} {name}" + (f" — {detail}" if detail else ""))
    _results.append((name, True, detail))


def _fail(name: str, err: str) -> None:
    print(f"  {_FAIL} {name} — {err}")
    _results.append((name, False, err))


# ── Anthropic models ──────────────────────────────────────────────────────────

async def _test_anthropic(whitelabel: str) -> None:
    settings = get_settings()
    model = settings.models.get(whitelabel)
    if not model:
        _fail(whitelabel, "not configured in .env")
        return

    client = AnthropicClient(
        whitelabel=whitelabel,
        api_key=settings.anthropic_api_key,
        model=model,
    )
    try:
        chunks = []
        async for chunk in client.stream(
            [Message(role="user", content=f"Reply with exactly: 'Hello from {whitelabel}'")]
        ):
            if chunk.delta:
                chunks.append(chunk.delta)
        text = "".join(chunks).strip()
        _ok(whitelabel, repr(text[:60]))
    except Exception as e:
        _fail(whitelabel, str(e)[:120])


# ── Azure models ──────────────────────────────────────────────────────────────

async def _test_azure(whitelabel: str) -> None:
    settings = get_settings()
    model = settings.models.get(whitelabel)
    if not model:
        _fail(whitelabel, "not configured in .env")
        return

    client = AzureFoundryClient(
        whitelabel=whitelabel,
        endpoint=settings.azure_foundry_endpoint,
        api_version=settings.azure_foundry_api_version,
        deployment=model,
        api_key=settings.azure_foundry_api_key,
    )
    try:
        chunks = []
        async for chunk in client.stream(
            [Message(role="user", content=f"Reply with exactly: 'Hello from {whitelabel}'")]
        ):
            if chunk.delta:
                chunks.append(chunk.delta)
        text = "".join(chunks).strip()
        _ok(whitelabel, repr(text[:60]))
    except Exception as e:
        _fail(whitelabel, str(e)[:120])


# ── Scout: Tavily search ──────────────────────────────────────────────────────

async def _test_tavily() -> None:
    settings = get_settings()
    if not settings.tavily_api_key:
        _fail("Tavily search", "TAVILY_API_KEY not set")
        return
    try:
        result = await execute_web_search(
            "Anthropic Claude latest release", max_results=3, api_key=settings.tavily_api_key
        )
        assert result.result_count > 0, "no results returned"
        _ok("Tavily search", f"{result.result_count} results, first url: {result.urls[0] if result.urls else 'none'}")
    except Exception as e:
        _fail("Tavily search", str(e)[:120])


# ── Scout: tool calling via Anthropic (Apex) ──────────────────────────────────

async def _test_scout_anthropic() -> None:
    settings = get_settings()
    model = settings.models.get("Apex")
    if not model:
        _fail("Scout via Apex", "Apex not configured")
        return
    if not settings.tavily_api_key:
        _fail("Scout via Apex", "TAVILY_API_KEY not set")
        return

    client = AnthropicClient(
        whitelabel="Apex",
        api_key=settings.anthropic_api_key,
        model=model,
    )
    tools = [anthropic_schema(WEB_SEARCH_SPEC, cache=True)]
    messages = [Message(role="user", content="What is the current version of Python? Use web_search.")]

    try:
        tool_calls_seen = 0
        text_chunks: list[str] = []

        for _turn in range(4):
            pending = []
            turn_text: list[str] = []
            stop = None

            async for chunk in client.stream(messages, tools=tools):
                if chunk.tool_call:
                    pending.append(chunk.tool_call)
                    tool_calls_seen += 1
                elif chunk.delta:
                    turn_text.append(chunk.delta)
                if chunk.stop_reason:
                    stop = chunk.stop_reason

            text_chunks.extend(turn_text)

            if not pending:
                break

            messages = list(messages)
            messages.append(Message(
                role="assistant",
                content="".join(turn_text),
                tool_calls=tuple(pending),
            ))

            for tc in pending:
                result = await execute_web_search(
                    tc.input.get("query", ""), max_results=3, api_key=settings.tavily_api_key
                )
                import json
                messages.append(Message(
                    role="tool",
                    content=json.dumps({"summary": result.summary, "urls": result.urls}),
                    tool_use_id=tc.id,
                ))

        final = "".join(text_chunks).strip()
        _ok(
            "Scout via Apex (tool loop)",
            f"{tool_calls_seen} tool call(s), response: {repr(final[:80])}"
        )
    except Exception as e:
        _fail("Scout via Apex (tool loop)", str(e)[:120])


# ── Scout: tool calling via Azure (Prism = grok-4-20-reasoning) ──────────────

async def _test_scout_azure() -> None:
    settings = get_settings()
    model = settings.models.get("Prism")
    if not model:
        _fail("Scout via Prism", "Prism not configured")
        return
    if not settings.tavily_api_key:
        _fail("Scout via Prism", "TAVILY_API_KEY not set")
        return

    client = AzureFoundryClient(
        whitelabel="Prism",
        endpoint=settings.azure_foundry_endpoint,
        api_version=settings.azure_foundry_api_version,
        deployment=model,
        api_key=settings.azure_foundry_api_key,
    )
    tools = [openai_schema(WEB_SEARCH_SPEC)]
    messages = [Message(role="user", content="What is the current version of Python? Use web_search.")]

    try:
        tool_calls_seen = 0
        text_chunks: list[str] = []

        for _turn in range(4):
            pending = []
            turn_text: list[str] = []

            async for chunk in client.stream(messages, tools=tools):
                if chunk.tool_call:
                    pending.append(chunk.tool_call)
                    tool_calls_seen += 1
                elif chunk.delta:
                    turn_text.append(chunk.delta)

            text_chunks.extend(turn_text)

            if not pending:
                break

            messages = list(messages)
            messages.append(Message(
                role="assistant",
                content="".join(turn_text),
                tool_calls=tuple(pending),
            ))

            for tc in pending:
                result = await execute_web_search(
                    tc.input.get("query", ""), max_results=3, api_key=settings.tavily_api_key
                )
                import json
                messages.append(Message(
                    role="tool",
                    content=json.dumps({"summary": result.summary, "urls": result.urls}),
                    tool_use_id=tc.id,
                ))

        final = "".join(text_chunks).strip()
        _ok(
            "Scout via Prism (tool loop)",
            f"{tool_calls_seen} tool call(s), response: {repr(final[:80])}"
        )
    except Exception as e:
        _fail("Scout via Prism (tool loop)", str(e)[:120])


# ── main ──────────────────────────────────────────────────────────────────────

async def main() -> None:
    settings = get_settings()
    print(f"\nLoaded {len(settings.models)} models: {list(settings.models.keys())}\n")

    anthropic_models = [wl for wl, prov in settings.providers.items() if prov == "anthropic"]
    azure_models = [wl for wl, prov in settings.providers.items() if prov == "azure"]

    print("── Anthropic models ──")
    for wl in anthropic_models:
        await _test_anthropic(wl)

    print("\n── Azure models ──")
    # Run Azure concurrently — faster
    await asyncio.gather(*[_test_azure(wl) for wl in azure_models])

    print("\n── Scout (web search) ──")
    await _test_tavily()
    await _test_scout_anthropic()
    await _test_scout_azure()

    # Summary
    passed = sum(1 for _, ok, _ in _results if ok)
    failed = sum(1 for _, ok, _ in _results if not ok)
    print(f"\n{'─'*40}")
    print(f"{_PASS} {passed} passed   {_FAIL} {failed} failed")
    if failed:
        print("\nFailed:")
        for name, ok, err in _results:
            if not ok:
                print(f"  {_FAIL} {name}: {err}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
