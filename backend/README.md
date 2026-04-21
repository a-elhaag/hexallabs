# Hexal-LM Backend

FastAPI + uv. Python 3.13.

## Setup

1. Copy env template:
   ```bash
   cp .env.example .env
   ```
   Fill: `ANTHROPIC_API_KEY`, `AZURE_FOUNDRY_ENDPOINT`, `AZURE_FOUNDRY_API_KEY`, and `MODEL_*` deployment names.

2. Install:
   ```bash
   uv sync
   ```

## Run

```bash
uv run uvicorn app.main:app --reload --port 8000
```

- Health: `GET http://localhost:8000/health`
- Debug invoke (streams plain text):
  ```bash
  curl -N -X POST http://localhost:8000/api/debug/invoke \
    -H "Content-Type: application/json" \
    -d '{"model":"Apex","query":"Say hi in 5 words."}'
  ```

## Test / lint / types

```bash
uv run pytest
uv run ruff check .
uv run mypy
```

## Architecture

- `app/config.py` — env loader, whitelabel -> model + provider map
- `app/llm/base.py` — `LLMClient` Protocol, `Message`, `StreamChunk`
- `app/llm/anthropic_client.py` — Apex, Pulse (direct Anthropic Console)
- `app/llm/azure_client.py` — Swift/Prism/Depth/Atlas/Horizon (Azure AI Foundry)
- `app/llm/factory.py` — `get_client(whitelabel)` routes by provider
- `app/api/debug.py` — `POST /api/debug/invoke` for sanity testing
