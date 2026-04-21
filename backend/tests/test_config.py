from app.config import Settings


def test_settings_loads_whitelabel_map(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("AZURE_FOUNDRY_ENDPOINT", "https://x.services.ai.azure.com")
    monkeypatch.setenv("MODEL_APEX", "claude-opus-4-7")
    monkeypatch.setenv("MODEL_APEX_PROVIDER", "anthropic")
    monkeypatch.setenv("MODEL_SWIFT", "gpt-4o-mini")
    monkeypatch.setenv("MODEL_SWIFT_PROVIDER", "azure")
    s = Settings()
    assert s.models["Apex"] == "claude-opus-4-7"
    assert s.providers["Apex"] == "anthropic"
    assert s.models["Swift"] == "gpt-4o-mini"
    assert s.providers["Swift"] == "azure"


def test_settings_rejects_unknown_provider(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("AZURE_FOUNDRY_ENDPOINT", "https://x.services.ai.azure.com")
    monkeypatch.setenv("MODEL_APEX", "x")
    monkeypatch.setenv("MODEL_APEX_PROVIDER", "bedrock")
    import pytest

    with pytest.raises(ValueError):
        Settings()
