from __future__ import annotations

import pytest

from app.config import Settings
from app.llm.anthropic_client import AnthropicClient
from app.llm.azure_client import AzureFoundryClient
from app.llm.factory import get_client


def _settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


def test_factory_returns_anthropic_for_apex() -> None:
    client = get_client("Apex", settings=_settings())
    assert isinstance(client, AnthropicClient)
    assert client.whitelabel == "Apex"


def test_factory_returns_azure_for_swift() -> None:
    client = get_client("Swift", settings=_settings())
    assert isinstance(client, AzureFoundryClient)
    assert client.whitelabel == "Swift"


def test_factory_unknown_whitelabel_raises() -> None:
    with pytest.raises(KeyError):
        get_client("Bogus", settings=_settings())
