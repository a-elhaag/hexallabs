from tavily import TavilyClient

from app.config import settings

_client: TavilyClient | None = None


def get_client() -> TavilyClient:
    global _client
    if _client is None:
        _client = TavilyClient(api_key=settings.tavily_api_key)
    return _client


async def search(query: str, max_results: int = 5) -> list[dict]:
    """Run a Tavily search and return a list of result dicts."""
    client = get_client()
    response = client.search(query=query, max_results=max_results)
    return response.get("results", [])
