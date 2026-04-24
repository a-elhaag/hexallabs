# HexalLabs — CLAUDE.md

## Project Overview
Horizontal LLM council platform. Queries answered by 1–7 models in parallel, models anonymously peer-review each other, a chairman model synthesizes a final answer. Also supports single-model "Oracle" mode.

## Monorepo Structure
```
hexallabs/
  frontend/   # Next.js App Router (TypeScript, Tailwind, NextAuth, Prisma)
  backend/    # FastAPI (Python, SQLAlchemy, WebSocket, Azure AI Foundry)
  .env        # single root .env — both frontend and backend load from here
```

## Stack
- **Frontend:** Next.js App Router + TypeScript + Tailwind + NextAuth.js v5 + Prisma ORM
- **Backend:** FastAPI + SQLAlchemy (async) + WebSocket + asyncpg
- **Database:** PostgreSQL 17 on Azure Flexible Server (`hexallabs-db.postgres.database.azure.com`)
- **Models:** 7 models on **Azure AI Foundry** (OpenAI-compatible endpoint, NOT Azure OpenAI SDK)
- **Auth:** NextAuth.js → JWT → FastAPI validates JWT on every request

## Models (Azure AI Foundry deployments)

| Deployment name | White-label name | Role |
|---|---|---|
| `gpt-5.1-chat` | Apex | Chairman / default |
| `gpt-5.4-mini` | Swift | Organizer (fast) |
| `o4-mini` | Prism | Reasoning |
| `DeepSeek-V3.2-Speciale` | Depth | Deep analysis |
| `Llama-3.3-70B-Instruct` | Atlas | Open-source |
| `Kimi-K2.5` | Horizon | Long context |
| `grok-4-20-reasoning` | Pulse | Latest reasoning |

## Billing Model

| Tier | Price | Usage Budget | Weekly Budget | Max Models |
|---|---|---|---|---|
| Core | $0 | $5/month | $1.25/week | 2 |
| Elite | $15/month | $10/month | $2.50/week | 7 |
| Arch | $29/month | $20/month | $5.00/week | 7 |

**Rate formula:** `cost = (input_tokens + output_tokens) / 1000 × (azure_output_price × 0.60)`

**Rollover:** 50% of unused weekly budget carries to next week.

**Tiers are DB-driven** (`pricing_tiers` table) — add new tiers without code changes.

## Key Rules

### Code style
- Python: use `async/await` throughout FastAPI; SQLAlchemy async sessions
- TypeScript: strict mode, no `any`
- Tailwind palette — 4 colors only, no others:
  - Black `#2c2c2c`
  - Warm gray `#a89080`
  - Cream `#f5f1ed`
  - Dusty denim `#6290c3`

### Motion (frontend)
- Every state change animates — easing `cubic-bezier(0.16, 1, 0.3, 1)`, 300ms default
- Button: `scale(1.02)` hover / `scale(0.98)` active
- Card: `translateY(-4px)` hover + shadow
- Input: black bottom border on focus

### UX naming (no generic AI names)
- Council mode → **The Council**
- Single model chat → **Oracle**
- Web search grounding → **Scout**
- Model handoff mid-chat → **The Relay**
- Caveman response style → **Primal Protocol**
- Model names shown in UI: white-label names only (Apex, Swift, etc.)
- Real attribution lives on /about page only

### Database
- All timestamps UTC
- Use Prisma for frontend DB access; SQLAlchemy (async) for backend
- `DATABASE_URL` in root `.env` uses `postgresql://` (Prisma format)
- Backend config auto-converts to `postgresql+asyncpg://` + `ssl=require`
- Run schema changes: `pnpm db:push` (dev) or `pnpm db:migrate` (prod)

### Environment
- Single root `.env` — both frontend and backend load from it
- `backend/app/config.py` uses `env_file="../.env"` with `extra="ignore"`
- `frontend/package.json` scripts use `dotenv -e ../.env --` prefix
- Never commit `.env` files

## Running Locally

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
pnpm install
pnpm dev
```

### DB scripts (run from frontend/)
```bash
pnpm db:push      # push schema changes (dev)
pnpm db:seed      # seed pricing tiers
pnpm db:studio    # open Prisma Studio
```

### SSE (`app/sse/`)
- `SseEvent` is validated against `_ALLOWED_EVENTS` — any new event type must be added there AND follow `hexallabs-sse-contract` skill
- `format_event()` emits `event: <name>\ndata: <json>\n\n`
- Heartbeat: `: keep-alive\n\n` every 15s to keep connection warm
- All modes (Oracle, Council, Relay, Workflow) emit the same event vocabulary so frontend has one consumer

## Azure AI Foundry
- Endpoint: `AZURE_AI_FOUNDRY_ENDPOINT` env var
- API Key: `AZURE_AI_FOUNDRY_KEY` env var
- Uses OpenAI-compatible SDK (`openai.AsyncOpenAI` with custom base_url)
- All 7 model deployment names set via `MODEL_*` env vars

### Testing
- pytest + pytest-asyncio, `conftest._default_env` seeds env creds
- Mock SDKs via DI (e.g. `AzureFoundryClient(sdk=mock)`) — never mock `get_client` unless testing factory routing
- Live API tests behind opt-in marker (`test_live.py`)

## Custom Skills (HexalLabs-specific)
Invoke via `Skill` tool. Auto-apply when editing relevant code:

| Skill | When |
|---|---|
| `hexallabs-caching-rules` | Writing Apex synthesis / peer review / Council / Prompt Forge prompts |
| `hexallabs-whitelabel-names` | Any user-facing string, API schema, frontend component |
| `hexallabs-stack-constraints` | Before adding a dependency or changing a core tool |
| `hexallabs-model-router` | Creating/editing any LLM client, factory, or model call site |
| `hexallabs-sse-contract` | Adding/modifying any SSE endpoint |

## What NOT to Build
- Billing / tiers
- Usage tracking
- Admin dashboard
- Rate limiting
- Multi-tenant

## Demo Flow (3 minutes)
1. Type complex query → Prompt Forge improves it, accept
2. Select 4–5 models, Council runs
3. Hex grid lights up, streams in real-time
4. Confidence scores update live per hex
5. Peer review — connecting lines animate
6. Apex synthesizes — center hex glows
7. Toggle Primal Protocol — caveman rewrite
8. Switch to Workflow — show 3-node pipeline
9. Prompt Lens — show how models interpreted differently
