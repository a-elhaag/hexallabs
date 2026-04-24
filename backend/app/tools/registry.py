from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]


def anthropic_schema(spec: ToolSpec, cache: bool = False) -> dict[str, Any]:
    """Render a ToolSpec for the Anthropic tools array.

    Set cache=True on the last tool to enable prompt caching (hexal-caching-rules).
    """
    result: dict[str, Any] = {
        "name": spec.name,
        "description": spec.description,
        "input_schema": spec.input_schema,
    }
    if cache:
        result["cache_control"] = {"type": "ephemeral"}
    return result


def openai_schema(spec: ToolSpec) -> dict[str, Any]:
    """Render a ToolSpec for the Azure OpenAI (OpenAI-compatible) tools array."""
    return {
        "type": "function",
        "function": {
            "name": spec.name,
            "description": spec.description,
            "parameters": spec.input_schema,
        },
    }
