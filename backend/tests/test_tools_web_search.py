from __future__ import annotations

import pytest

from app.tools.registry import ToolSpec, anthropic_schema, openai_schema
from app.tools.web_search import WEB_SEARCH_SPEC, SearchResult, execute_web_search


# --- Registry schema renderers ---

def test_anthropic_schema_shape() -> None:
    schema = anthropic_schema(WEB_SEARCH_SPEC)
    assert schema["name"] == "web_search"
    assert "description" in schema
    assert "input_schema" in schema
    assert "cache_control" not in schema


def test_anthropic_schema_with_cache() -> None:
    schema = anthropic_schema(WEB_SEARCH_SPEC, cache=True)
    assert schema["cache_control"] == {"type": "ephemeral"}


def test_openai_schema_shape() -> None:
    schema = openai_schema(WEB_SEARCH_SPEC)
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "web_search"
    assert "parameters" in schema["function"]


def test_tool_spec_input_schema_has_required_query() -> None:
    assert "query" in WEB_SEARCH_SPEC.input_schema["required"]


# --- Tavily adapter ---

@pytest.mark.asyncio
async def test_execute_web_search_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_response = {
        "results": [
            {"title": "Foo", "url": "https://foo.com", "content": "Foo content"},
            {"title": "Bar", "url": "https://bar.com", "content": "Bar content"},
        ]
    }

    class _FakeTavily:
        def __init__(self, api_key: str) -> None:
            pass

        async def search(self, query: str, max_results: int = 5) -> dict:  # type: ignore[type-arg]
            return fake_response

    import app.tools.web_search as ws_mod
    monkeypatch.setattr(ws_mod, "_get_tavily_client", lambda key: _FakeTavily(key))

    result = await execute_web_search("test query", max_results=2, api_key="fake-key")

    assert isinstance(result, SearchResult)
    assert result.result_count == 2
    assert "https://foo.com" in result.urls
    assert len(result.summary) <= 500


@pytest.mark.asyncio
async def test_execute_web_search_summary_truncated(monkeypatch: pytest.MonkeyPatch) -> None:
    long_content = "X" * 1000
    fake_response = {
        "results": [
            {"title": "T", "url": "https://t.com", "content": long_content},
        ]
    }

    class _FakeTavily:
        def __init__(self, api_key: str) -> None:
            pass

        async def search(self, query: str, max_results: int = 5) -> dict:  # type: ignore[type-arg]
            return fake_response

    import app.tools.web_search as ws_mod
    monkeypatch.setattr(ws_mod, "_get_tavily_client", lambda key: _FakeTavily(key))

    result = await execute_web_search("test", api_key="fake-key")
    assert len(result.summary) <= 500


@pytest.mark.asyncio
async def test_execute_web_search_empty_results(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FakeTavily:
        def __init__(self, api_key: str) -> None:
            pass

        async def search(self, query: str, max_results: int = 5) -> dict:  # type: ignore[type-arg]
            return {"results": []}

    import app.tools.web_search as ws_mod
    monkeypatch.setattr(ws_mod, "_get_tavily_client", lambda key: _FakeTavily(key))

    result = await execute_web_search("nothing", api_key="fake-key")
    assert result.result_count == 0
    assert result.urls == []
    assert result.summary == ""
