"""
Tavily search client — Scout feature.
Uses AsyncTavilyClient so it fits naturally in the async council flow.
"""
from __future__ import annotations

from tavily import AsyncTavilyClient

from app.config import settings

_client: AsyncTavilyClient | None = None


def get_client() -> AsyncTavilyClient:
    global _client
    if _client is None:
        _client = AsyncTavilyClient(api_key=settings.tavily_api_key)
    return _client


async def scout(
    query: str,
    max_results: int = 5,
    search_depth: str = "basic",  # "basic" (1 credit) | "advanced" (2 credits)
) -> list[dict]:
    """
    Run a Tavily search and return result dicts.

    Each result: {"url": str, "title": str, "content": str, "score": float}
    """
    client = get_client()
    response = await client.search(
        query=query,
        max_results=max_results,
        search_depth=search_depth,
        include_answer=False,
    )
    return response.get("results", [])


def format_scout_context(results: list[dict]) -> str:
    """Format search results as a context block to inject into the query."""
    if not results:
        return ""
    lines = ["--- Web Search Results (Scout) ---"]
    for i, r in enumerate(results, 1):
        lines.append(f"[{i}] {r.get('title', 'No title')}")
        lines.append(f"    {r.get('url', '')}")
        lines.append(f"    {r.get('content', '')}")
    lines.append("--- End Scout Results ---")
    return "\n".join(lines)
