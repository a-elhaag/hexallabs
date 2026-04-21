import os

import pytest


@pytest.fixture(autouse=True)
def _default_env(monkeypatch: pytest.MonkeyPatch) -> None:
    defaults = {
        "ANTHROPIC_API_KEY": "sk-test",
        "AZURE_FOUNDRY_ENDPOINT": "https://test.services.ai.azure.com",
        "SUPABASE_URL": "https://test.supabase.co",
        "DATABASE_URL": "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres",
        "MODEL_APEX": "claude-opus-4-7",
        "MODEL_APEX_PROVIDER": "anthropic",
        "MODEL_SWIFT": "gpt-4o-mini",
        "MODEL_SWIFT_PROVIDER": "azure",
    }
    for k, v in defaults.items():
        if not os.getenv(k):
            monkeypatch.setenv(k, v)
