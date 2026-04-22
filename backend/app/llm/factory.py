from __future__ import annotations

from functools import lru_cache

from app.config import Settings, get_settings
from app.llm.anthropic_client import AnthropicClient
from app.llm.azure_client import AzureFoundryClient
from app.llm.base import LLMClient

def get_client(whitelabel: str, settings: Settings | None = None) -> LLMClient:
    s = settings or _cached_settings()
    if whitelabel not in s.models:
        raise KeyError(f"Unknown white-label {whitelabel!r}. Known: {sorted(s.models)}")
    provider = s.providers[whitelabel]
    model = s.models[whitelabel]

    if provider == "anthropic":
        return AnthropicClient(
            whitelabel=whitelabel,
            api_key=s.anthropic_api_key,
            model=model,
        )
    if provider == "azure":
        return AzureFoundryClient(
            whitelabel=whitelabel,
            endpoint=s.azure_foundry_endpoint,
            api_version=s.azure_foundry_api_version,
            deployment=model,
            api_key=s.azure_foundry_api_key,
        )
    raise ValueError(f"Unsupported provider {provider!r} for {whitelabel}")


@lru_cache(maxsize=1)
def _cached_settings() -> Settings:
    return get_settings()
