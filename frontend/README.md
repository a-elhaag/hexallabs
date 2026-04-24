# HexalLabs Frontend

Next.js 15 App Router + TypeScript + Tailwind CSS v4 + Supabase auth.

## Stack

- Next.js 15 (App Router)
- TypeScript (strict)
- Tailwind CSS v4
- `@supabase/ssr` for auth (cookie-based session)
- `@t3-oss/env-nextjs` + Zod for env validation
- `framer-motion`, `gsap` for animation

## Setup

```bash
bun install
cp .env.example .env   # fill in Supabase URL + anon key + backend URL
bun dev
```

## Env vars

See `.env.example`. All `NEXT_PUBLIC_*`.

- `NEXT_PUBLIC_SUPABASE_URL` — cloud Supabase project URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` — anon/public key from Supabase dashboard
- `NEXT_PUBLIC_BACKEND_URL` — FastAPI backend base URL (e.g. `http://localhost:8000`)

## Structure

- `src/app/` — App Router routes (`/login`, `/signup`, `/chat`, `/auth/callback`, `/auth/signout`)
- `src/lib/supabase/` — browser + server Supabase clients + middleware
- `src/lib/api/` — backend fetch wrapper + SSE stream hook
- `src/components/chat/` — chat UI (ChatShell, ModelGrid, MessageList, etc.)
- `src/middleware.ts` — Next.js middleware running session refresh + unauth redirect
