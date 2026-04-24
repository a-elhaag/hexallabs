from __future__ import annotations

import asyncio
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from app.tools.registry import ToolSpec

WEB_SEARCH_SPEC = ToolSpec(
    name="web_search",
    description=(
        "Search the public web for up-to-date information. "
        "Use when the user asks about current events, prices, recent releases, "
        "or facts that may have changed after your training cutoff."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query, 3-12 words.",
            },
            "max_results": {
                "type": "integer",
                "minimum": 1,
                "maximum": 10,
                "default": 5,
            },
        },
        "required": ["query"],
    },
)

_SUMMARY_MAX_CHARS = 500


@dataclass(frozen=True, slots=True)
class SearchResult:
    summary: str
    urls: list[str]
    result_count: int
    raw: list[dict[str, Any]]


@lru_cache(maxsize=None)
def _get_tavily_client(api_key: str) -> Any:
    from tavily import AsyncTavilyClient  # lazy import — optional dep

    return AsyncTavilyClient(api_key=api_key)


async def execute_web_search(
    query: str,
    max_results: int = 5,
    *,
    api_key: str,
) -> SearchResult:
    client = _get_tavily_client(api_key)
    try:
        response = await asyncio.wait_for(
            client.search(query, max_results=max_results),
            timeout=15.0,
        )
    except TimeoutError as exc:
        raise RuntimeError(f"web_search timed out after 15s for query: {query!r}") from exc

    results: list[dict[str, Any]] = response.get("results", [])
    urls = [r.get("url", "") for r in results if r.get("url")]

    # Build a plain-text summary from titles + content snippets.
    parts: list[str] = []
    for r in results:
        title = r.get("title", "")
        content = r.get("content", "")
        if title or content:
            parts.append(f"{title}: {content}" if title else content)

    raw_summary = " | ".join(parts)
    summary = raw_summary[:_SUMMARY_MAX_CHARS]

    return SearchResult(
        summary=summary,
        urls=urls,
        result_count=len(results),
        raw=results,
    )


def format_search_context(result: SearchResult) -> str:
    """Format search results as a system-context string for injection."""
    lines = ["[Web search results]"]
    for i, (url, r) in enumerate(zip(result.urls, result.raw), 1):
        title = r.get("title", "")
        content = r.get("content", "")
        lines.append(f"{i}. {title} ({url})\n   {content[:300]}")
    return "\n".join(lines)
