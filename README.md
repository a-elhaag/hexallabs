# HexalLabs

> *Seven minds. One answer.*

You've been asking AI the wrong way — one model, one shot, hoping it's right.

HexalLabs changes the game. Ask once. Seven specialized AI models reason independently, anonymously tear each other apart, and a chairman synthesizes the one answer worth trusting.

---

## The Idea

Every expert panel in history works the same way: diverse thinkers, independent judgment, structured debate, one recommendation. We built that for AI.

**The Council** runs up to 7 models in parallel. Each model has no idea which of its peers said what. Anonymous peer review removes sycophancy — models can't play to the crowd. Apex (the chairman) weighs confidence scores and critique depth, then synthesizes a final answer that's demonstrably better than any single model could produce alone.

This isn't prompt chaining. This isn't RAG. This is a governance layer on top of AI.

---

## The 7

| Name | Real model | Specialty |
|---|---|---|
| **Apex** | claude-opus-4-7 | Chairman. Synthesis. Final word. |
| **Pulse** | claude-sonnet-4-6 | Latest reasoning. Cutting edge. |
| **Swift** | claude-haiku-4-5 | Fast organizer. Structure and speed. |
| **Prism** | grok-4-20-reasoning | Reasoning. Logic-first, no shortcuts. |
| **Depth** | DeepSeek-V3.2-Speciale | Deep analysis. Slow, thorough, brutal. |
| **Atlas** | Llama-4-Maverick-17B | Open-source perspective. Different priors. |
| **Horizon** | Kimi-K2.5 | Long context. Holds the full picture. |

Mix and match. Use 2 for speed, 7 for decisions that matter.

---

## Modes

### The Council
Select your panel. They reason in parallel on a hex grid. Watch confidence build in real-time. Peer review animates across the grid — lines light up as models critique each other. Apex synthesizes last.

### Oracle
One model. No overhead. Direct, clean conversation. Switch to Council anytime via the `/` menu.

### The Relay
Mid-conversation model handoff. Start with Prism for a logic breakdown, hand off to Horizon for long-context synthesis. Context carries through.

### Scout
Any response, grounded in live web results. Tavily-powered. No hallucinated citations.

### Primal Protocol
Any Council or Oracle response, rewritten in compressed, caveman-style prose. Strips filler. Keeps signal.

---

## Stack

```
Frontend   Next.js App Router · TypeScript · Tailwind · NextAuth.js v5
Backend    FastAPI · SQLAlchemy async · WebSocket · asyncpg  
Database   PostgreSQL 17 on Azure Flexible Server
Models     Azure AI Foundry (OpenAI-compatible endpoint)
Auth       NextAuth.js → JWT → FastAPI validates every request
```

---

## Running Locally

**Backend**
```bash
cd backend
uv sync --python 3.12
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend**
```bash
cd frontend
bun install
bun dev
```

Copy `.env.example` → `backend/.env` and `frontend/.env`. Fill in Azure AI Foundry credentials and database URL.

---

## Why This Wins

Single-model AI is a single point of failure. One model's blind spots, biases, and training artifacts are your answer.

The Council has no single point of failure. Depth catches what Swift misses. Prism dismantles what Horizon over-fitted. Atlas brings a perspective none of the others trained on. Apex sees all of it.

The winning AI product isn't the one with the best model. It's the one with the best process.

---

*Built by HexalLabs.*
