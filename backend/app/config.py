from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str
    jwt_secret: str = ""

    # Azure AI Foundry — OpenAI-compatible endpoint
    azure_ai_foundry_endpoint: str = "https://hexallabs-ai.services.ai.azure.com/api/projects/hexallabs-project/openai/v1/"
    azure_ai_foundry_key: str = ""

    # Model deployment names
    model_gpt: str = "gpt-5.1-chat"
    model_deepseek: str = "DeepSeek-V3.2-Speciale"
    model_llama: str = "Llama-3.3-70B-Instruct"
    model_kimi: str = "Kimi-K2.5"
    model_grok: str = "grok-4-20-reasoning"

    # Tavily Search
    tavily_api_key: str = ""


settings = Settings()
