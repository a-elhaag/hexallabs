# Hexal LM — CLAUDE.md

## Project Overview
Horizontal LLM council platform. User submits a query → multiple models run in parallel → models anonymously peer-review each other → Apex (chairman) synthesizes final answer. Supports Oracle (single model), Relay (mid-generation handoff), and Workflow (node pipeline) modes.

## Stack
- **Frontend:** Next.js 14 App Router, TypeScript strict, Tailwind CSS, `@supabase/ssr` for auth + light DB reads (no ORM on frontend)
- **Backend:** FastAPI, Python, async/await, SQLAlchemy async + asyncpg, Alembic for table DDL
- **Database:** Supabase Postgres (17). Backend connects direct via pooler and bypasses RLS. Frontend uses anon key, RLS enforced.
- **Auth:** Supabase Auth. Next.js API routes handle signup/login/profile. FastAPI verifies Supabase JWT (RS256) via JWKS with `pyjwt[crypto]`.
- **Models:** Apex/Pulse → Anthropic direct. Swift/Prism/Depth/Atlas/Horizon → Azure AI Foundry.
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
1. FastAPI backend — model calls + SSE streaming + council logic
2. Next.js frontend — hex grid UI, query input, streaming
3. Peer review + confidence scoring
4. Prompt Forge
5. Oracle + Relay
6. Scout
7. Workflow mode
8. Prompt Lens
9. Primal Protocol
10. Auth (Supabase Auth) — last

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

<!-- code-review-graph MCP tools -->
## MCP Tools: code-review-graph

**IMPORTANT: This project has a knowledge graph. ALWAYS use the
code-review-graph MCP tools BEFORE using Grep/Glob/Read to explore
the codebase.** The graph is faster, cheaper (fewer tokens), and gives
you structural context (callers, dependents, test coverage) that file
scanning cannot.

### When to use graph tools FIRST

- **Exploring code**: `semantic_search_nodes` or `query_graph` instead of Grep
- **Understanding impact**: `get_impact_radius` instead of manually tracing imports
- **Code review**: `detect_changes` + `get_review_context` instead of reading entire files
- **Finding relationships**: `query_graph` with callers_of/callees_of/imports_of/tests_for
- **Architecture questions**: `get_architecture_overview` + `list_communities`

Fall back to Grep/Glob/Read **only** when the graph doesn't cover what you need.

### Key Tools

| Tool | Use when |
|------|----------|
| `detect_changes` | Reviewing code changes — gives risk-scored analysis |
| `get_review_context` | Need source snippets for review — token-efficient |
| `get_impact_radius` | Understanding blast radius of a change |
| `get_affected_flows` | Finding which execution paths are impacted |
| `query_graph` | Tracing callers, callees, imports, tests, dependencies |
| `semantic_search_nodes` | Finding functions/classes by name or keyword |
| `get_architecture_overview` | Understanding high-level codebase structure |
| `refactor_tool` | Planning renames, finding dead code |

### Workflow

1. The graph auto-updates on file changes (via hooks).
2. Use `detect_changes` for code review.
3. Use `get_affected_flows` to understand impact.
4. Use `query_graph` pattern="tests_for" to check coverage.
