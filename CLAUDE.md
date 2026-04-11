# Hexallabs — Claude Code Instructions

## Project Overview
Horizontal LLM council platform. Multi-model consensus: queries answered by 4 LLMs in parallel, models anonymously peer-review each other, a chairman model synthesizes a final answer.

## Monorepo Structure
```
hexallabs/
  frontend/   # Next.js App Router (TypeScript, Tailwind, NextAuth, Prisma)
  backend/    # FastAPI (Python, SQLAlchemy, WebSocket, Azure AI Foundry)
```

## Stack
- **Frontend:** Next.js App Router + TypeScript + Tailwind + NextAuth.js + Prisma ORM
- **Backend:** FastAPI + SQLAlchemy (async) + WebSocket + psycopg2/asyncpg
- **Database:** PostgreSQL 17 on Azure Flexible Server (`hexallabs-db.postgres.database.azure.com`)
- **Models:** gpt-4o, o1, DeepSeek-R1, Mistral-Large-3 — all on **Azure AI Foundry** (NOT Azure OpenAI)
- **Auth:** NextAuth.js → JWT → FastAPI validates JWT on every request

## Key Rules

### Code style
- Python: use `async/await` throughout FastAPI; SQLAlchemy async sessions
- TypeScript: strict mode, no `any`
- Tailwind: B/W/G palette only — `#000000`, `#FFFFFF`, `#6B7280`; no accent colors

### Motion (frontend)
- Every state change animates — easing `cubic-bezier(0.16, 1, 0.3, 1)`, 300ms default
- Button: `scale(1.02)` hover / `scale(0.98)` active
- Card: `translateY(-4px)` hover + shadow
- Input: black bottom border on focus

### Database
- All timestamps UTC
- Use Prisma for frontend DB access; SQLAlchemy (async) for backend
- Azure PostgreSQL requires `sslmode=require` on all connections
- Run migrations via `prisma migrate deploy` (frontend) — backend reads same DB

### MCP / Graph tools
- Use `code-review-graph` MCP tools BEFORE Grep/Glob/Read for codebase exploration
- `semantic_search_nodes` for finding functions, `get_impact_radius` for blast radius

### Environment
- `backend/.env` — FastAPI secrets (DATABASE_URL, AZURE_AI_FOUNDRY_KEY, JWT_SECRET, etc.)
- `frontend/.env` — Next.js secrets (NEXTAUTH_*, DATABASE_URL, NEXT_PUBLIC_API_URL)
- DATABASE_URL is the same connection string in both — keep them in sync
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

### Test DB connection
```bash
cd backend
python test_db.py
```

## Azure AI Foundry
- Endpoint: set in `AZURE_AI_FOUNDRY_ENDPOINT` env var
- API Key: set in `AZURE_AI_FOUNDRY_KEY` env var
- Models are deployed as named deployments on the Foundry project
- Use the `azure-ai-inference` SDK (not `openai` SDK) for Foundry endpoints
