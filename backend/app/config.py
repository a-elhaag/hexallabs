from __future__ import annotations

from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

WHITELABELS = ("Apex", "Pulse", "Swift", "Prism", "Depth", "Atlas", "Horizon")
VALID_PROVIDERS = {"anthropic", "azure"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
        case_sensitive=False,
    )

    anthropic_api_key: str = Field(alias="ANTHROPIC_API_KEY")
    azure_foundry_endpoint: str = Field(alias="AZURE_FOUNDRY_ENDPOINT")
    azure_foundry_api_version: str = Field(default="2024-10-21", alias="AZURE_FOUNDRY_API_VERSION")

    models: dict[str, str] = Field(default_factory=dict)
    providers: dict[str, str] = Field(default_factory=dict)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        import os

        for name in WHITELABELS:
            deploy = os.getenv(f"MODEL_{name.upper()}")
            prov = os.getenv(f"MODEL_{name.upper()}_PROVIDER")
            if deploy and prov:
                if prov not in VALID_PROVIDERS:
                    raise ValueError(
                        f"MODEL_{name.upper()}_PROVIDER={prov!r} invalid. "
                        f"Allowed: {sorted(VALID_PROVIDERS)}"
                    )
                self.models[name] = deploy
                self.providers[name] = prov

    @field_validator("azure_foundry_endpoint")
    @classmethod
    def _strip_trailing_slash(cls, v: str) -> str:
        return v.rstrip("/")


def get_settings() -> Settings:
    return Settings()
