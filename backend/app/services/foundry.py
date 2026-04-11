"""
Azure AI Foundry client — OpenAI-compatible endpoint.
Supports text and image (vision) inputs.
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

from openai import AsyncOpenAI

from app.config import settings

def _models() -> dict[str, str]:
    """Build model key → deployment name map from settings."""
    return {
        "gpt-5.1-chat": settings.model_gpt,
        "deepseek-v3": settings.model_deepseek,
        "llama-3.3-70b": settings.model_llama,
        "kimi-k2.5": settings.model_kimi,
        "grok-4": settings.model_grok,
    }

# Models that support image inputs
VISION_MODELS = {"gpt-5.1-chat", "kimi-k2.5"}

_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            base_url=settings.azure_ai_foundry_endpoint,
            api_key=settings.azure_ai_foundry_key,
        )
    return _client


def _image_to_data_url(image: bytes, mime_type: str = "image/jpeg") -> str:
    encoded = base64.b64encode(image).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def _build_user_content(
    text: str,
    images: list[bytes] | None = None,
    image_urls: list[str] | None = None,
    mime_type: str = "image/jpeg",
) -> str | list[dict[str, Any]]:
    """Build message content — plain string if no images, list of parts if images."""
    if not images and not image_urls:
        return text

    parts: list[dict[str, Any]] = [{"type": "text", "text": text}]

    for img_bytes in images or []:
        parts.append({
            "type": "image_url",
            "image_url": {"url": _image_to_data_url(img_bytes, mime_type)},
        })

    for url in image_urls or []:
        parts.append({
            "type": "image_url",
            "image_url": {"url": url},
        })

    return parts


async def complete(
    model: str,
    system_prompt: str,
    user_message: str,
    images: list[bytes] | None = None,
    image_urls: list[str] | None = None,
    mime_type: str = "image/jpeg",
) -> str:
    """
    Call a model on Azure AI Foundry and return the response text.

    Args:
        model:        Short model key (e.g. "gpt-5.1-chat") or full deployment name.
        system_prompt: System instructions for the model.
        user_message: The user's text query.
        images:       Optional list of raw image bytes (base64-encoded automatically).
        image_urls:   Optional list of publicly accessible image URLs.
        mime_type:    MIME type for raw image bytes (default: image/jpeg).
    """
    deployment = _models().get(model, model)
    client = get_client()

    content = _build_user_content(
        text=user_message,
        images=images,
        image_urls=image_urls,
        mime_type=mime_type,
    )

    response = await client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content},
        ],
    )

    return response.choices[0].message.content
