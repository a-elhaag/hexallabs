#!/usr/bin/env python3
"""Live API test: Anthropic + Azure Foundry."""

from __future__ import annotations

import asyncio

from app.config import get_settings
from app.llm.anthropic_client import AnthropicClient
from app.llm.azure_client import AzureFoundryClient
from app.llm.base import Message


async def test_anthropic() -> None:
    """Test AnthropicClient with Apex."""
    print("\n=== Testing Anthropic (Apex) ===")
    settings = get_settings()

    client = AnthropicClient(
        whitelabel="Apex",
        api_key=settings.anthropic_api_key,
        model=settings.models.get("Apex", "claude-opus-4-7"),
    )

    print(f"Model: {settings.models.get('Apex')}")
    print("Streaming response:")

    async for chunk in client.stream(
        [Message(role="user", content="Say 'Hello from Apex' in one sentence.")]
    ):
        print(chunk.delta, end="", flush=True)

    print("\n✓ Anthropic test passed\n")


async def test_azure() -> None:
    """Test AzureFoundryClient with Atlas (DeepSeek)."""
    print("=== Testing Azure (Atlas / DeepSeek) ===")
    settings = get_settings()

    client = AzureFoundryClient(
        whitelabel="Atlas",
        endpoint=settings.azure_foundry_endpoint,
        api_version=settings.azure_foundry_api_version,
        deployment=settings.models.get("Atlas", "DeepSeek-V3.2-Speciale"),
    )

    print(f"Model: {settings.models.get('Atlas')}")
    print("Streaming response:")

    async for chunk in client.stream(
        [Message(role="user", content="Say 'Hello from Atlas' in one sentence.")]
    ):
        print(chunk.delta, end="", flush=True)

    print("\n✓ Azure test passed\n")


async def main() -> None:
    """Run both tests."""
    try:
        await test_anthropic()
        await test_azure()
        print("✓ All tests passed!")
    except Exception as e:
        print(f"\n✗ Error: {e}", flush=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
