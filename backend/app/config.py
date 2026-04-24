from __future__ import annotations

from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

WHITELABELS = (
    "Apex", "Pulse", "Swift", "Prism", "Depth", "Atlas", "Horizon",
    "Spark", "Craft", "Flux", "Bolt",
)
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
    azure_foundry_api_key: str | None = Field(default=None, alias="AZURE_FOUNDRY_API_KEY")

    tavily_api_key: str | None = Field(default=None, alias="TAVILY_API_KEY")
    scout_max_results: int = Field(default=5, alias="SCOUT_MAX_RESULTS")
    scout_max_turns: int = Field(default=4, alias="SCOUT_MAX_TURNS")

    supabase_url: str = Field(alias="SUPABASE_URL")
    supabase_jwt_audience: str = Field(default="authenticated", alias="SUPABASE_JWT_AUDIENCE")
    database_url: str = Field(alias="DATABASE_URL")
    database_pool_size: int = Field(default=10, alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=5, alias="DATABASE_MAX_OVERFLOW")

    cors_allow_origins: list[str] = Field(default_factory=list, alias="CORS_ALLOW_ORIGINS")

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def _split_origins(cls, v: object) -> list[str]:
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return list(v) if v else []

    models: dict[str, str] = Field(default_factory=dict)
    providers: dict[str, str] = Field(default_factory=dict)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        import os

        from dotenv import load_dotenv
        load_dotenv()

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

    @field_validator("azure_foundry_endpoint", "supabase_url")
    @classmethod
    def _strip_trailing_slash(cls, v: str) -> str:
        return v.rstrip("/")

    @property
    def supabase_jwt_issuer(self) -> str:
        return f"{self.supabase_url}/auth/v1"

    @property
    def supabase_jwks_url(self) -> str:
        return f"{self.supabase_url}/auth/v1/.well-known/jwks.json"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
