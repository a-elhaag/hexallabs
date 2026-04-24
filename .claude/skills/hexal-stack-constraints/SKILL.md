---
name: hexal-stack-constraints
description: Locked tech stack for Hexal-LM. Invoke before adding ANY new dependency, changing package manager, or swapping a core tool. Prevents stack drift.
---

# Hexal Stack Constraints

## Backend (`fastapi/` or `backend/`)

| Concern | Choice | Reason |
|---|---|---|
| Language | Python **3.13** | latest stable |
| Pkg mgr | **uv** | fast, lockfile, modern |
| Framework | **FastAPI** | async, SSE friendly |
| Server | **uvicorn** | standard FastAPI pair |
| Config | **pydantic-settings** | typed env loading |
| Lint | **ruff** | replaces black+isort+flake8 |
| Types | **mypy** (strict) | static guarantees |
| Test | **pytest** + **pytest-asyncio** + **httpx.AsyncClient** | async native |
| DB ORM | **SQLAlchemy async** | single source of truth for schema |
| DB driver | **asyncpg** | fastest async PG |
| Migrations (tables) | **alembic** (async env) | owns DDL, indexes, FKs |
| Migrations (policies) | **Supabase CLI** (SQL files in `supabase/migrations/`) | owns RLS, triggers, extensions |
| Auth JWT verify | **pyjwt[crypto]** + JWKS | verify Supabase access tokens (RS256/ES256) |
| LLM (Anthropic) | **anthropic** SDK | Apex, Pulse |
| LLM (Azure) | **openai** SDK w/ Azure endpoint + **azure-identity** | Swift/Prism/Depth/Horizon |
| LLM (Azure inference) | **azure-ai-inference** | Atlas (DeepSeek/Llama) |

## Frontend (`nextjs/` or `frontend/`)

| Concern | Choice | Reason |
|---|---|---|
| Framework | **Next.js 14 App Router** | per CLAUDE.md |
| Language | **TypeScript strict** | no `any` |
| Styling | **Tailwind CSS** | per CLAUDE.md |
| Auth + DB client | **@supabase/ssr** + **@supabase/supabase-js** | signup/login/profile in Next.js API routes, RLS-scoped reads |
| ORM on frontend | none — no Prisma, DB owned by backend | single schema authority |
| Auth (now + future) | **Supabase Auth** | JWT (RS256) via JWKS, verified by FastAPI |
| State | React Server Components + minimal client | default |
| Animation | CSS + Framer Motion if needed | follow CLAUDE.md motion rules |

## DB / Infra

| Concern | Choice |
|---|---|
| Postgres host | **Supabase** (no per-op billing) |
| Vector | **pgvector** (Supabase built-in) — Prompt Lens later |
| Storage | **Supabase Storage** (when needed) |
| Realtime | **SSE** primary. Supabase Realtime reserved for collaboration features later. |

## Forbidden without explicit user approval

- Adding a third LLM provider
- Swapping Supabase → Neon/RDS/etc.
- Adding Redis/queue (unless Relay mode needs it — evaluate then)
- NextAuth (Supabase Auth owns identity)
- Prisma or any ORM on the frontend (backend owns schema)
- Clerk or other auth providers (Supabase Auth stays)
- poetry / pipenv / pip-tools (use uv)
- pnpm swap for npm/yarn — use pnpm consistently in Next.js side
- Docker in dev (run processes directly; Docker only for prod deploy)

## Monorepo layout

```
hexal-lm/
  backend/          # FastAPI
  frontend/         # Next.js
  .env              # single shared (or per-side .env + .env.shared)
  docs/superpowers/plans/
  .claude/skills/
  CLAUDE.md
```

## Build order (per CLAUDE.md)

1. FastAPI skeleton + LLM clients ← plan #1
2. Oracle SSE
3. Council parallel + peer review + confidence
4. Prompt Forge
5. Relay
6. Scout
7. Workflow
8. Prompt Lens
9. Primal Protocol
10. Auth (Supabase now, Clerk later)
