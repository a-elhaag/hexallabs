# Hexal-LM Backend

FastAPI + uv. Python 3.13.

## Setup

1. Copy env template:
   ```bash
   cp .env.example .env
   ```
   Fill: `ANTHROPIC_API_KEY`, `AZURE_FOUNDRY_ENDPOINT`, `AZURE_FOUNDRY_API_KEY`, `MODEL_*` deployment names, and the Supabase section (`SUPABASE_URL`, `DATABASE_URL`).

2. Install:
   ```bash
   uv sync
   ```

## Database (Supabase)

Schema lives in two places — table DDL is owned by Alembic, policies/triggers/extensions are owned by the Supabase CLI.

**Local dev loop:**

```bash
# from repo root
supabase start                     # boots a local Postgres + Studio
supabase db reset                  # applies supabase/migrations/*.sql (pgcrypto, trigger, RLS)

# then from backend/
uv run alembic upgrade head        # applies alembic/versions/*.py (tables + indexes)
```

Order matters: the pgcrypto extension from `supabase/migrations/20260421000000_extensions.sql` must be present before Alembic runs, because table DDL calls `gen_random_uuid()`.

**Generate a new Alembic migration:**

```bash
uv run alembic revision --autogenerate -m "short description"
```

Review the generated file before committing — autogenerate misses server-side defaults and check constraints.

**Remote Supabase:**

Point `DATABASE_URL` at the **pooler** connection string from the Supabase dashboard (`postgresql+asyncpg://postgres.<ref>:<pw>@<region>.pooler.supabase.com:6543/postgres`). The pooler is required for serverless/async workloads; the direct `db.*.supabase.co` host is only for migrations from a stable host.

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

- `app/config.py` — env loader, whitelabel -> model + provider map, Supabase + DB settings
- `app/llm/base.py` — `LLMClient` Protocol, `Message`, `StreamChunk`
- `app/llm/anthropic_client.py` — Apex, Pulse (direct Anthropic Console)
- `app/llm/azure_client.py` — Swift/Prism/Depth/Atlas/Horizon (Azure AI Foundry)
- `app/llm/factory.py` — `get_client(whitelabel)` routes by provider
- `app/api/debug.py` — `POST /api/debug/invoke` for sanity testing
- `app/db/` — SQLAlchemy async engine, session dep, ORM models (`users`, `sessions`, `queries`, `messages`, `peer_reviews`, `relay_handoffs`, `workflows`, `workflow_runs`, `workflow_node_runs`, `prompt_lens_entries`)
- `app/auth/` — JWKS-based Supabase JWT verification (`verify_supabase_jwt`) + FastAPI `get_current_user` dependency

## Auth

Next.js owns signup/login/profile via `@supabase/ssr`. FastAPI only verifies JWTs:

```python
from fastapi import APIRouter, Depends
from app.auth import AuthUser, get_current_user

router = APIRouter()

@router.get("/api/me")
async def me(user: AuthUser = Depends(get_current_user)) -> dict[str, str]:
    return {"id": str(user.id), "email": user.email}
```

Client calls hit FastAPI directly with `Authorization: Bearer <supabase_access_token>`. Tokens are RS256, verified against the Supabase JWKS endpoint, cached by `PyJWKClient`.
