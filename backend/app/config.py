from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",   # single root .env for full monorepo
        env_file_encoding="utf-8",
        extra="ignore",       # ignore frontend-only vars
    )

    database_url: str

    @field_validator("database_url", mode="before")
    @classmethod
    def ensure_asyncpg(cls, v: str) -> str:
        """Prisma uses postgresql://, SQLAlchemy async needs postgresql+asyncpg://.
        Also: asyncpg uses ssl=require, not sslmode=require."""
        if v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        # asyncpg doesn't accept sslmode=require — use ssl=require
        v = v.replace("sslmode=require", "ssl=require")
        return v
    jwt_secret: str = ""

    # Azure AI Foundry — OpenAI-compatible endpoint
    azure_ai_foundry_endpoint: str = "https://hexallabs-ai.services.ai.azure.com/api/projects/hexallabs-project/openai/v1/"
    azure_ai_foundry_key: str = ""

    # Model deployment names
    model_gpt: str = "gpt-5.1-chat"
    model_gpt_mini: str = "gpt-5.4-mini"
    model_o4_mini: str = "o4-mini"
    model_deepseek: str = "DeepSeek-V3.2-Speciale"
    model_llama: str = "Llama-3.3-70B-Instruct"
    model_kimi: str = "Kimi-K2.5"
    model_grok: str = "grok-4-20-reasoning"

    # Tavily Search
    tavily_api_key: str = ""


settings = Settings()
