# Prompt Lens UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Surface per-model prompt interpretation data (angle, divergence score) in a collapsible panel below the CouncilGrid after a Council run completes.

**Architecture:** The backend already emits per-model `lens` SSE events (hex + interpretation) and persists `PromptLensEntry` rows. This plan extends those events with `divergence_score`, adds a `lens_ready` SSE event to signal completion, and wires a new `PromptLens.tsx` component into `ChatWindow` that accumulates the arriving events and reveals itself on `lens_ready`. The `Turn` type gains a `lensData` field so lens state lives beside the council turn that produced it.

**Tech Stack:** FastAPI + Python async (backend), Next.js App Router + TypeScript strict + Tailwind (frontend), SSE streaming, no new dependencies.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `backend/app/sse/events.py` | Modify | Add `lens_ready` to `_ALLOWED_EVENTS` |
| `backend/app/council/stream.py` | Modify | Pass `divergence_score` in `lens` events; emit `lens_ready` after all lens events |
| `backend/tests/test_prompt_lens.py` | Modify | Add tests for `divergence_score` in SSE payload and `lens_ready` event |
| `frontend/lib/types.ts` | Modify | Extend `SseEventMap.lens` with `divergence_score`; add `lens_ready` type; add `LensEntry` interface; add `lensData` to `Turn` |
| `frontend/lib/sse.ts` | No change | Already handles arbitrary event names generically |
| `frontend/components/chat/PromptLens.tsx` | Create | Collapsible panel showing per-model interpretations |
| `frontend/components/chat/ChatWindow.tsx` | Modify | Accumulate `lens` events into `Turn.lensData`; handle `lens_ready`; render `PromptLens` |

---

### Task 1: Extend `lens` SSE event with `divergence_score` and add `lens_ready` event (backend)

**Files:**
- Modify: `backend/app/sse/events.py`
- Modify: `backend/app/council/stream.py`
- Modify: `backend/tests/test_prompt_lens.py`

- [ ] **Step 1: Write failing tests**

Add to `backend/tests/test_prompt_lens.py` after the last existing test:

```python
def test_council_stream_lens_event_has_divergence_score(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.main import app
    clients = {
        "Swift": FakeClient(["swift [[CONF:8]]"], whitelabel="Swift"),
        "Prism": FakeClient(["prism [[CONF:7]]"], whitelabel="Prism"),
    }
    apex = _SimpleApexClient()
    spark = _make_spark_client("The model focused on brevity.\nDIVERGENCE:4")
    tc = _setup_council_with_lens(monkeypatch, clients, apex, spark)
    try:
        with tc:
            r = tc.post(
                "/api/query",
                json={"mode": "council", "query": "what is a monad?", "models": ["Swift", "Prism"]},
            )
    finally:
        app.dependency_overrides.clear()
    assert r.status_code == 200
    events = parse_sse(r.text)
    lens_events = [(e, d) for e, d in events if e == "lens"]
    assert len(lens_events) == 2
    for _, d in lens_events:
        assert "divergence_score" in d
        assert isinstance(d["divergence_score"], int)
        assert 1 <= d["divergence_score"] <= 10


def test_council_stream_emits_lens_ready_after_all_lens_events(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.main import app
    clients = {
        "Swift": FakeClient(["swift [[CONF:8]]"], whitelabel="Swift"),
        "Prism": FakeClient(["prism [[CONF:7]]"], whitelabel="Prism"),
    }
    apex = _SimpleApexClient()
    spark = _make_spark_client("Practical angle.\nDIVERGENCE:5")
    tc = _setup_council_with_lens(monkeypatch, clients, apex, spark)
    try:
        with tc:
            r = tc.post(
                "/api/query",
                json={"mode": "council", "query": "explain TLS", "models": ["Swift", "Prism"]},
            )
    finally:
        app.dependency_overrides.clear()
    assert r.status_code == 200
    events = parse_sse(r.text)
    names = [e for e, _ in events]
    assert "lens_ready" in names
    lens_ready_idx = names.index("lens_ready")
    done_idx = names.index("done")
    lens_indices = [i for i, n in enumerate(names) if n == "lens"]
    assert all(i < lens_ready_idx for i in lens_indices)
    assert lens_ready_idx < done_idx


def test_council_stream_lens_ready_payload_contains_all_models(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.main import app
    clients = {
        "Swift": FakeClient(["swift [[CONF:8]]"], whitelabel="Swift"),
        "Prism": FakeClient(["prism [[CONF:7]]"], whitelabel="Prism"),
    }
    apex = _SimpleApexClient()
    spark = _make_spark_client("First-principles focus.\nDIVERGENCE:6")
    tc = _setup_council_with_lens(monkeypatch, clients, apex, spark)
    try:
        with tc:
            r = tc.post(
                "/api/query",
                json={"mode": "council", "query": "explain hashing", "models": ["Swift", "Prism"]},
            )
    finally:
        app.dependency_overrides.clear()
    assert r.status_code == 200
    events = parse_sse(r.text)
    lens_ready_events = [(e, d) for e, d in events if e == "lens_ready"]
    assert len(lens_ready_events) == 1
    _, payload = lens_ready_events[0]
    assert "results" in payload
    assert isinstance(payload["results"], list)
    assert len(payload["results"]) == 2
    models_in_payload = {item["hex"] for item in payload["results"]}
    assert models_in_payload == {"Swift", "Prism"}
    for item in payload["results"]:
        assert "interpretation" in item
        assert "divergence_score" in item


def test_council_stream_lens_ready_not_emitted_when_lens_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.main import app
    clients = {
        "Swift": FakeClient(["swift [[CONF:8]]"], whitelabel="Swift"),
        "Prism": FakeClient(["prism [[CONF:7]]"], whitelabel="Prism"),
    }
    apex = _SimpleApexClient()
    error_spark = _ErrorClient()
    tc = _setup_council_with_lens(monkeypatch, clients, apex, error_spark)
    try:
        with tc:
            r = tc.post(
                "/api/query",
                json={"mode": "council", "query": "question", "models": ["Swift", "Prism"]},
            )
    finally:
        app.dependency_overrides.clear()
    assert r.status_code == 200
    events = parse_sse(r.text)
    names = [e for e, _ in events]
    assert "done" in names
    assert "lens_ready" not in names
```

- [ ] **Step 2: Run to confirm failures**

```bash
cd /Users/anas/Projects/hexallabs/backend
uv run pytest tests/test_prompt_lens.py::test_council_stream_lens_event_has_divergence_score tests/test_prompt_lens.py::test_council_stream_emits_lens_ready_after_all_lens_events tests/test_prompt_lens.py::test_council_stream_lens_ready_payload_contains_all_models tests/test_prompt_lens.py::test_council_stream_lens_ready_not_emitted_when_lens_fails -v
```

Expected: 4 FAILED

- [ ] **Step 3: Add `lens_ready` to `_ALLOWED_EVENTS`**

In `backend/app/sse/events.py`, add `"lens_ready"` to the `_ALLOWED_EVENTS` set. Also update the docstring to add: `lens_ready {results: [{hex: str, interpretation: str, divergence_score: int}]}`

- [ ] **Step 4: Extend Phase 4 in `backend/app/council/stream.py`**

Find the Phase 4 lens block. Replace the yield loop to:
1. Pass `divergence_score=lr.divergence_score` in the `lens` SSE event payload
2. After all lens events, emit `lens_ready` with all results:

```python
    ready_payload: list[dict[str, object]] = []
    for lr in lens_results:
        db.add(PromptLensEntry(..., divergence_score=lr.divergence_score))
        yield format_event(SseEvent("lens", {"hex": lr.whitelabel, "interpretation": lr.interpretation, "divergence_score": lr.divergence_score}))
        ready_payload.append({"hex": lr.whitelabel, "interpretation": lr.interpretation, "divergence_score": lr.divergence_score})
    if ready_payload:
        yield format_event(SseEvent("lens_ready", {"results": ready_payload}))
```

- [ ] **Step 5: Run tests to confirm pass**

```bash
cd /Users/anas/Projects/hexallabs/backend
uv run pytest tests/test_prompt_lens.py::test_council_stream_lens_event_has_divergence_score tests/test_prompt_lens.py::test_council_stream_emits_lens_ready_after_all_lens_events tests/test_prompt_lens.py::test_council_stream_lens_ready_payload_contains_all_models tests/test_prompt_lens.py::test_council_stream_lens_ready_not_emitted_when_lens_fails -v
```

Expected: 4 PASSED

- [ ] **Step 6: Full regression check**

```bash
cd /Users/anas/Projects/hexallabs/backend
uv run pytest --tb=short -q
```

- [ ] **Step 7: Commit**

```bash
git add backend/app/sse/events.py backend/app/council/stream.py backend/tests/test_prompt_lens.py
git commit -m "feat: add divergence_score to lens SSE event and emit lens_ready after all lens events"
```

---

### Task 2: Extend frontend types for lens data

**Files:**
- Modify: `frontend/lib/types.ts`

- [ ] **Step 1: Add `LensEntry` interface, update `SseEventMap`**

Add after `SseToolResult`:

```typescript
export interface LensEntry {
  hex: string
  interpretation: string
  divergence_score: number
}
```

Update `SseEventMap`:
```typescript
  lens:           { hex: string; interpretation: string; divergence_score: number }
  lens_ready:     { results: LensEntry[] }
```

- [ ] **Step 2: TypeScript check**

```bash
cd /Users/anas/Projects/hexallabs/frontend
bun run tsc --noEmit 2>&1 | head -40
```

Expected: no new errors

- [ ] **Step 3: Commit**

```bash
git add frontend/lib/types.ts
git commit -m "feat: add LensEntry type, extend lens SSE with divergence_score, add lens_ready"
```

---

### Task 3: Build `PromptLens.tsx` component

**Files:**
- Create: `frontend/components/chat/PromptLens.tsx`

- [ ] **Step 1: Create the component**

```typescript
'use client'
import { useState, useRef, useEffect } from 'react'
import { LensEntry } from '@/lib/types'

function DivergenceBar({ score }: { score: number }) {
  const pct = ((score - 1) / 9) * 100
  return (
    <div className="flex items-center gap-2 mt-1.5">
      <div className="flex-1 h-1 rounded-full bg-[#2c2c2c]/10 overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{
            width: `${pct}%`,
            backgroundColor: score <= 4 ? '#a89080' : score <= 7 ? '#6290c3' : '#2c2c2c',
            transitionTimingFunction: 'cubic-bezier(0.16, 1, 0.3, 1)',
          }}
        />
      </div>
      <span className="text-[9px] font-black text-[#a89080]/60 uppercase tracking-widest shrink-0 w-14 text-right">
        {score <= 3 ? 'literal' : score <= 6 ? 'moderate' : 'creative'}
      </span>
    </div>
  )
}

function LensCard({ entry, index }: { entry: LensEntry; index: number }) {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const el = ref.current
    if (!el) return
    el.style.opacity = '0'
    el.style.transform = 'translateY(6px)'
    const timer = setTimeout(() => {
      el.style.transition = 'opacity 300ms cubic-bezier(0.16, 1, 0.3, 1), transform 300ms cubic-bezier(0.16, 1, 0.3, 1)'
      el.style.opacity = '1'
      el.style.transform = 'translateY(0)'
    }, index * 60)
    return () => clearTimeout(timer)
  }, [index])
  return (
    <div ref={ref} className="bg-[#f5f1ed] border border-[#a89080]/20 rounded-xl p-3 flex flex-col gap-1">
      <p className="text-[10px] font-black text-[#a89080]/70 uppercase tracking-widest">{entry.hex}</p>
      <p className="text-xs leading-relaxed text-[#2c2c2c]">{entry.interpretation}</p>
      <DivergenceBar score={entry.divergence_score} />
    </div>
  )
}

interface PromptLensProps {
  entries: LensEntry[]
  visible: boolean
}

export function PromptLens({ entries, visible }: PromptLensProps) {
  const [open, setOpen] = useState(true)
  const bodyRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const el = bodyRef.current
    if (!el) return
    if (visible && open) el.style.maxHeight = `${el.scrollHeight}px`
  }, [visible, open, entries.length])
  if (!visible || entries.length === 0) return null
  function toggleOpen() {
    const el = bodyRef.current
    if (!el) return
    el.style.maxHeight = open ? '0' : `${el.scrollHeight}px`
    setOpen(prev => !prev)
  }
  const cols = entries.length === 1 ? 'grid-cols-1' : entries.length >= 4 ? 'grid-cols-3' : 'grid-cols-2'
  return (
    <div className="w-full max-w-4xl mx-auto px-6 pt-1 pb-2" style={{ animation: 'msgIn 0.28s cubic-bezier(0.16,1,0.3,1) both' }}>
      <div className="border border-[#a89080]/20 rounded-2xl overflow-hidden">
        <button
          onClick={toggleOpen}
          className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-[#2c2c2c]/5 transition-colors duration-150"
        >
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-black text-[#6290c3] uppercase tracking-widest">Prompt Lens</span>
            <span className="text-[9px] text-[#a89080]/60">{entries.length} model{entries.length !== 1 ? 's' : ''}</span>
          </div>
          <span style={{ display: 'inline-block', transform: open ? 'rotate(0deg)' : 'rotate(-90deg)', transition: 'transform 300ms cubic-bezier(0.16, 1, 0.3, 1)' }}>▾</span>
        </button>
        <div ref={bodyRef} style={{ maxHeight: open ? '600px' : '0', overflow: 'hidden', transition: 'max-height 300ms cubic-bezier(0.16, 1, 0.3, 1)' }}>
          <div className={`grid ${cols} gap-2 px-3 pb-3`}>
            {entries.map((entry, i) => <LensCard key={entry.hex} entry={entry} index={i} />)}
          </div>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: TypeScript check**

```bash
cd /Users/anas/Projects/hexallabs/frontend
bun run tsc --noEmit 2>&1 | head -40
```

- [ ] **Step 3: Commit**

```bash
git add frontend/components/chat/PromptLens.tsx
git commit -m "feat: add PromptLens collapsible panel component"
```

---

### Task 4: Wire `PromptLens` into `ChatWindow`

**Files:**
- Modify: `frontend/components/chat/ChatWindow.tsx`

- [ ] **Step 1: Import and extend Turn type**

Add imports:
```typescript
import { LensEntry } from '@/lib/types'
import { PromptLens } from './PromptLens'
```

Extend `Turn` type — add `lensData?: LensEntry[]; lensReady?: boolean` to the council variant.

- [ ] **Step 2: Add SSE handlers for `lens` and `lens_ready`**

Inside `streamQuery` handlers:

```typescript
lens: (d) => {
  if (isCouncil) {
    setTurns(prev => prev.map(turn => {
      if (turn.type !== 'council') return turn
      const existing = turn.lensData ?? []
      if (existing.some(e => e.hex === d.hex)) return turn
      return { ...turn, lensData: [...existing, { hex: d.hex, interpretation: d.interpretation, divergence_score: d.divergence_score }] }
    }))
  }
},
lens_ready: () => {
  if (isCouncil) {
    setTurns(prev => prev.map(turn => {
      if (turn.type !== 'council') return turn
      return { ...turn, lensReady: true }
    }))
  }
},
```

- [ ] **Step 3: Render `PromptLens` below `CouncilGrid`**

```typescript
// Replace:
<CouncilGrid messages={turn.msgs} />
// With:
<CouncilGrid messages={turn.msgs} />
<PromptLens entries={turn.lensData ?? []} visible={turn.lensReady ?? false} />
```

- [ ] **Step 4: TypeScript check**

```bash
cd /Users/anas/Projects/hexallabs/frontend
bun run tsc --noEmit 2>&1 | head -60
```

- [ ] **Step 5: Dev server smoke test**

```bash
cd /Users/anas/Projects/hexallabs/frontend
bun dev
```

Open http://localhost:3000/chat, run council query, verify Prompt Lens panel appears.

- [ ] **Step 6: Commit**

```bash
git add frontend/components/chat/ChatWindow.tsx
git commit -m "feat: wire PromptLens into ChatWindow — show panel on lens_ready"
```
