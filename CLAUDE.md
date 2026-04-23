# Hexal LM — CLAUDE.md

## Project Overview
Horizontal LLM council platform. User submits a query → multiple models run in parallel → models anonymously peer-review each other → Apex (chairman) synthesizes final answer. Supports Oracle (single model), Relay (mid-generation handoff), and Workflow (node pipeline) modes.

## Stack
- **Frontend:** Next.js 14 App Router, TypeScript strict, Tailwind CSS, `@supabase/ssr` for auth + light DB reads (no ORM on frontend)
- **Backend:** FastAPI, Python, async/await, SQLAlchemy async + asyncpg, Alembic for table DDL
- **Database:** Supabase Postgres (17). Backend connects direct via pooler and bypasses RLS. Frontend uses anon key, RLS enforced.
- **Auth:** Supabase Auth. Next.js API routes handle signup/login/profile. FastAPI verifies Supabase JWT (RS256) via JWKS with `pyjwt[crypto]`.
- **Models:** Apex/Pulse → Anthropic direct. Swift/Prism/Depth/Atlas/Horizon/Spark → Azure AI Foundry.
- **Monorepo:** `frontend/` + `backend/` + `supabase/` (RLS + triggers SQL) + root `.env`

## Models
| White-label | Role |
|---|---|
| Apex | Chairman / synthesizer |
| Swift | Fast organizer |
| Prism | Reasoning |
| Depth | Deep analysis |
| Atlas | Open-source |
| Horizon | Long context |
| Pulse | Latest reasoning |
| Spark | Cheap/fast utility (Prompt Forge, Prompt Lens) |

Always use white-label names in UI. Real model attribution only on `/about` page.

## Core Modes
- **The Council** — 2–7 models in parallel, anonymous peer-review, Apex synthesizes weighted by confidence
- **Oracle** — single model, direct response
- **The Relay** — model hands off mid-generation; detects handoff trigger, passes context + partial output to next model
- **Primal Protocol** — toggle on any mode; Apex rewrites final synthesis in brutally compressed caveman-style
- **Scout** — web search tool injected as context before models respond
- **Workflow** — node-based pipeline builder; each node is a model or tool, output feeds next node

## Council Execution Flow
1. User submits query → Prompt Forge rewrites/improves it, user accepts or overrides
2. User selects models (or auto-selection, user can override)
3. All models called in parallel, responses stream in real-time
4. Each model self-rates confidence 1–10
5. Peer review round: models see anonymized responses, critique, adjust confidence scores
6. Apex synthesizes weighted by final confidence scores
7. Prompt Lens shows post-run breakdown of how each model interpreted the prompt

## UI/UX

### Colors (4 only)
```
--color-bg:       #2c2c2c
--color-muted:    #a89080
--color-surface:  #f5f1ed
--color-accent:   #6290c3
```

### Typography
- Heading + Body: Inter
- Mono: JetBrains Mono

### Motion
- Easing: `cubic-bezier(0.16, 1, 0.3, 1)`, 300ms
- Button: hover `scale(1.02)` / active `scale(0.98)`
- Card: hover `translateY(-4px)` + shadow
- Input: accent bottom border on focus

### Hexagonal Model Grid
- Models in hexagonal cells (CSS clip-path or SVG)
- Each hex pulses and fills as model streams
- Confidence score inside hex, updates live
- Peer review shown as animated lines between hexes
- Apex hex center, larger, glows during synthesis

### Workflow Mode
- Node-based visual pipeline
- Drag-and-drop edges between model/tool nodes
- Council and Oracle are presets within this system
- Streams per node, top-to-bottom execution

### Feature Names
- Council mode → "The Council"
- Single model → "Oracle"
- Web search → "Scout"
- Model handoff → "The Relay"
- Caveman output → "Primal Protocol"
- Pre-send prompt improvement → "Prompt Forge"
- Post-run interpretation analysis → "Prompt Lens"

## Development Workflow
Always follow Explore → Plan → Code → Commit:
1. **Explore** — read relevant files, understand structure, never assume
2. **Plan** — outline approach before writing code, confirm if ambiguous
3. **Code** — implement one concern at a time, no scope creep
4. **Commit** — atomic commits, descriptive messages, never commit `.env` or secrets

## Code Rules
- Python: `async/await` everywhere, no sync DB calls
- TypeScript: strict mode, no `any`
- No hardcoded keys, model names, or endpoints — all via `.env`
- All timestamps UTC

## Build Order
**Backend:**
- ✅ Skeleton: LLMClient Protocol, Anthropic/Azure clients, factory
- ✅ Auth: Supabase JWT verification via JWKS
- ✅ DB: SQLAlchemy async models (User, Session, Query, Message, PeerReview, PromptLens, RelayHandoff, Workflow)
- ✅ Oracle SSE: `POST /api/query` with event schema
- ✅ Relay: mid-generation handoff, Apex verdict
- ✅ Council: parallel fan-out + peer review + Apex synthesis
- ✅ Workflow: node pipeline execution (model/passthrough/prompt_template nodes)
- ✅ Prompt Lens: interpretation analysis per model (via Spark)
- ✅ Prompt Forge: pre-send rewrite (via Spark)
- ✅ Scout: web search injection (Tavily, force/auto/off modes)
- ✅ Primal Protocol: caveman synthesis (Apex only)

**Frontend:**
- ⏳ Rebuild: Next.js 14, TypeScript, Tailwind, Bun

## Backend Patterns

### LLM Clients (`app/llm/`)
- `LLMClient` Protocol: `stream(messages, cache_key=None) -> AsyncIterator[StreamChunk]`
- `AnthropicClient` — Apex/Pulse. Honors `Message.cache=True` → `cache_control: {"type": "ephemeral"}`
- `AzureFoundryClient` — Swift/Prism/Depth/Atlas/Horizon. Routes `cache_key` → `extra_body.prompt_cache_key`
- `get_client(whitelabel)` factory — routes by env-configured provider (`MODEL_*_PROVIDER`)
- Dependency inject SDKs via optional constructor param for tests

### Auth (`app/auth/`)
- `verify_supabase_jwt(token)` — JWKS-based RS256, `PyJWKClient` cached
- `get_current_user` FastAPI dependency returns `AuthUser(id, email)`
- Frontend owns signup/login via `@supabase/ssr`. Backend only verifies JWTs.

### SSE (`app/sse/`)
- `SseEvent` is validated against `_ALLOWED_EVENTS` — any new event type must be added there AND follow `hexal-sse-contract` skill
- `format_event()` emits `event: <name>\ndata: <json>\n\n`
- Heartbeat: `: keep-alive\n\n` every 15s to keep connection warm
- All modes (Oracle, Council, Relay, Workflow) emit the same event vocabulary so frontend has one consumer

### Database (`app/db/`)
- SQLAlchemy 2.0 async + asyncpg via Supabase pooler
- Models split per-file under `app/db/models/` (no monolithic models.py)
- Alembic for DDL (tables); Supabase `supabase/` dir for RLS + triggers
- Backend bypasses RLS (service role); frontend uses anon key with RLS

### Testing
- pytest + pytest-asyncio, `conftest._default_env` seeds env creds
- Mock SDKs via DI (e.g. `AzureFoundryClient(sdk=mock)`) — never mock `get_client` unless testing factory routing
- Live API tests behind opt-in marker (`test_live.py`)

## Custom Skills (Hexal-specific)
Invoke via `Skill` tool. Auto-apply when editing relevant code:

| Skill | When |
|---|---|
| `hexal-caching-rules` | Writing Apex synthesis / peer review / Council / Prompt Forge prompts |
| `hexal-whitelabel-names` | Any user-facing string, API schema, frontend component |
| `hexal-stack-constraints` | Before adding a dependency or changing a core tool |
| `hexal-model-router` | Creating/editing any LLM client, factory, or model call site |
| `hexal-sse-contract` | Adding/modifying any SSE endpoint |

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
