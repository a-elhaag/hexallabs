"""
Azure AI Foundry client — OpenAI-compatible endpoint.
Supports text and image (vision) inputs, with streaming.
"""

from __future__ import annotations

import base64
from typing import Any, AsyncGenerator

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


async def stream_complete(
    model: str,
    system_prompt: str,
    user_message: str,
    images: list[bytes] | None = None,
    image_urls: list[str] | None = None,
    mime_type: str = "image/jpeg",
) -> AsyncGenerator[str, None]:
    """
    Stream text chunks from a model on Azure AI Foundry.

    Yields each text delta as it arrives from the model.
    """
    deployment = _models().get(model, model)
    client = get_client()

    content = _build_user_content(
        text=user_message,
        images=images,
        image_urls=image_urls,
        mime_type=mime_type,
    )

    stream = await client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content},
        ],
        stream=True,
    )

    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


async def complete(
    model: str,
    system_prompt: str,
    user_message: str,
    images: list[bytes] | None = None,
    image_urls: list[str] | None = None,
    mime_type: str = "image/jpeg",
) -> str:
    """
    Call a model on Azure AI Foundry and return the full response text.
    Implemented on top of stream_complete.
    """
    chunks: list[str] = []
    async for chunk in stream_complete(
        model=model,
        system_prompt=system_prompt,
        user_message=user_message,
        images=images,
        image_urls=image_urls,
        mime_type=mime_type,
    ):
        chunks.append(chunk)
    return "".join(chunks)
