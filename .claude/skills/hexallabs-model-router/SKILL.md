---
name: hexallabs-model-router
description: Enforce HexalLabs provider split — Apex/Pulse via direct Anthropic Console API, all others via Azure AI Foundry. Invoke when creating or editing any LLM client, factory, or model call site. Prevents mixing vendors or using wrong endpoint.
---

# HexalLabs Model Router

## Rule

HexalLabs uses **two providers**, no others:

| White-label | Provider | SDK | Endpoint |
|---|---|---|---|
| **Apex** | Anthropic Console (direct) | `anthropic` | default `api.anthropic.com` |
| **Pulse** | Anthropic Console (direct) | `anthropic` | default `api.anthropic.com` |
| **Swift** | Azure AI Foundry | `openai` (OpenAI-compatible) | `https://<resource>.services.ai.azure.com/models` |
| **Prism** | Azure AI Foundry | `openai` | same |
| **Depth** | Azure AI Foundry | `openai` | same |
| **Atlas** | Azure AI Foundry | `azure-ai-inference` | same |
| **Horizon** | Azure AI Foundry | `openai` | same |

## Never

- Never call Anthropic-hosted Claude via Azure Foundry `/anthropic/v1/messages` path. Decision: direct Anthropic Console.
- Never call Azure models via Anthropic SDK.
- Never hardcode model names. Always read from `MODEL_<WHITELABEL>` env vars.
- Never add a third provider (OpenAI direct, Bedrock, Vertex, Groq) without updating this skill + CLAUDE.md.

## Factory contract

```python
# app/llm/factory.py
def get_client(whitelabel: str) -> LLMClient:
    provider = settings.providers[whitelabel]  # "anthropic" | "azure"
    if provider == "anthropic":
        return AnthropicClient(settings.anthropic_api_key, settings.models[whitelabel])
    return AzureFoundryClient(settings.azure_endpoint, settings.models[whitelabel], credential=DefaultAzureCredential())
```

All clients implement `async def stream(messages) -> AsyncIterator[str]`. Caller never knows which provider.

## Auth

- Anthropic: `ANTHROPIC_API_KEY` env
- Azure: `DefaultAzureCredential` (Entra ID) — `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_CLIENT_SECRET`. No API keys in prod.

## Why this split

User decision 2026-04-21: Apex/Pulse quality = Claude. Other 5 white-labels span Azure Foundry catalog for cost + diversity + open-source rep (Atlas). Two bills, one codebase abstraction.
