# Hexallabs — Claude Code Instructions

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

### Test DB connection
```bash
cd backend && python test_db.py
```

## Azure AI Foundry
- Endpoint: `AZURE_AI_FOUNDRY_ENDPOINT` env var
- API Key: `AZURE_AI_FOUNDRY_KEY` env var
- Uses OpenAI-compatible SDK (`openai.AsyncOpenAI` with custom base_url)
- All 7 model deployment names set via `MODEL_*` env vars

## MCP / Graph tools
- Use `code-review-graph` MCP tools BEFORE Grep/Glob/Read for codebase exploration
- `semantic_search_nodes` for finding functions, `get_impact_radius` for blast radius
