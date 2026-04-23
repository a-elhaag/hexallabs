from __future__ import annotations

from functools import lru_cache

from app.config import Settings, get_settings
from app.llm.anthropic_client import AnthropicClient
from app.llm.azure_client import AzureFoundryClient
from app.llm.base import LLMClient


def get_client(whitelabel: str, settings: Settings | None = None) -> LLMClient:
    if settings is not None:
        return _build_client(whitelabel, settings)
    return _cached_client(whitelabel)


@lru_cache(maxsize=None)
def _cached_client(whitelabel: str) -> LLMClient:
    return _build_client(whitelabel, get_settings())


def _build_client(whitelabel: str, settings: Settings) -> LLMClient:
    if whitelabel not in settings.models:
        raise KeyError(f"Unknown white-label {whitelabel!r}. Known: {sorted(settings.models)}")
    provider = settings.providers[whitelabel]
    model = settings.models[whitelabel]

    if provider == "anthropic":
        return AnthropicClient(
            whitelabel=whitelabel,
            api_key=settings.anthropic_api_key,
            model=model,
        )
    if provider == "azure":
        return AzureFoundryClient(
            whitelabel=whitelabel,
            endpoint=settings.azure_foundry_endpoint,
            api_version=settings.azure_foundry_api_version,
            deployment=model,
            api_key=settings.azure_foundry_api_key,
        )
    raise ValueError(f"Unsupported provider {provider!r} for {whitelabel}")
