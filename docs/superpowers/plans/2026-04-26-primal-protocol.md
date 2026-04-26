# Primal Protocol (Caveman Mode) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a per-message "Primal Protocol" toggle that rewrites any completed Apex/Oracle answer in brutally compressed caveman style via a dedicated streaming SSE endpoint, with cross-fade animation on the message text and active-state button styling.

**Architecture:** A new `POST /api/primal` endpoint accepts `{ message_id, text }`, calls Apex with the existing `_PRIMAL_SYSTEM` prompt, and streams back `primal_chunk` / `primal_done` SSE events. The frontend adds two new SSE event types, a `PrimalButton` component on each completed assistant message, and a per-message `primalText` state tracked in `ChatWindow`. No new backend models or DB writes are needed — this is a stateless rewrite-on-demand endpoint. The existing `primal_protocol` flag on `QueryRequest` (which runs primal inline during the main stream) remains untouched.

**Tech Stack:** FastAPI + Python async, OpenAI-compatible `AzureFoundryClient`, SSE via `format_event`, Next.js App Router + TypeScript strict, Tailwind, `streamQuery` from `lib/sse.ts`.

---

### Task 1: Add new SSE event types to backend allowlist

**Files:**
- Modify: `backend/app/sse/events.py`

- [ ] Add `"primal_chunk"` and `"primal_done"` to `_ALLOWED_EVENTS` in `backend/app/sse/events.py`:

```python
_ALLOWED_EVENTS = {
    "session",
    "prompt_forge",
    "hex_start",
    "token",
    "confidence",
    "peer_review",
    "hex_done",
    "synth_start",
    "synth_token",
    "synth_done",
    "lens",
    "primal",
    "primal_chunk",   # streaming delta for /api/primal endpoint
    "primal_done",    # signals end of primal rewrite stream
    "relay_handoff",
    "tool_call",
    "tool_result",
    "quota_warning",
    "done",
    "error",
}
```

Also update the module docstring to document the two new events:
```
primal_chunk   {delta: str}
primal_done    {}
```

- [ ] Verify guard works:
```bash
cd /Users/anas/Projects/hexallabs/backend
python -c "from app.sse.events import SseEvent; SseEvent('primal_chunk', {'delta': 'x'}); SseEvent('primal_done', {}); print('OK')"
```
Expected: `OK`

- [ ] Commit:
```bash
git add backend/app/sse/events.py
git commit -m "feat(sse): add primal_chunk + primal_done event types for /api/primal"
```

---

### Task 2: Write failing test for `POST /api/primal`

**Files:**
- Create: `backend/tests/test_primal_endpoint.py`

- [ ] Create `backend/tests/test_primal_endpoint.py`:

```python
"""Tests for POST /api/primal — Primal Protocol streaming endpoint."""
from __future__ import annotations

import json
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.llm.base import StreamChunk


class _FakeSdkStream:
    def __init__(self, chunks: list[str]) -> None:
        self._chunks = chunks

    def __aiter__(self):
        return self._iter()

    async def _iter(self):
        from unittest.mock import MagicMock
        for text in self._chunks:
            choice = MagicMock()
            choice.delta.content = text
            choice.delta.tool_calls = None
            choice.finish_reason = None
            chunk = MagicMock()
            chunk.choices = [choice]
            yield chunk
        choice = MagicMock()
        choice.delta.content = None
        choice.delta.tool_calls = None
        choice.finish_reason = "stop"
        chunk = MagicMock()
        chunk.choices = [choice]
        yield chunk


class _FakeSdk:
    def __init__(self, chunks: list[str]) -> None:
        self._chunks = chunks

    @property
    def chat(self):
        return self

    @property
    def completions(self):
        return self

    async def create(self, **kwargs):
        return _FakeSdkStream(self._chunks)


@pytest.fixture()
def fake_apex_sdk():
    return _FakeSdk(["unga ", "bunga ", "code fast"])


@pytest.fixture()
def auth_headers():
    return {"Authorization": "Bearer test-token"}


@pytest.mark.asyncio
async def test_primal_endpoint_streams_primal_chunk_and_done(
    fake_apex_sdk, auth_headers, monkeypatch
):
    from app.llm.azure_client import AzureFoundryClient
    from app import auth

    async def _fake_user(_=None):
        from app.auth import AuthUser
        import uuid
        return AuthUser(id=uuid.uuid4(), email="test@test.com", tier="core")

    monkeypatch.setattr(auth, "get_current_user", _fake_user)

    from app.llm import factory
    real_get = factory.get_client

    def _fake_get_client(whitelabel: str):
        if whitelabel == "Apex":
            return AzureFoundryClient(
                whitelabel="Apex",
                endpoint="https://fake.endpoint",
                api_version="2024-02-01",
                deployment="gpt-5.1-chat",
                api_key="fake-key",
                sdk=fake_apex_sdk,
            )
        return real_get(whitelabel)

    monkeypatch.setattr(factory, "get_client", _fake_get_client)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        async with client.stream(
            "POST",
            "/api/primal",
            json={"message_id": "msg-abc-123", "text": "This is a long technical synthesis about async programming."},
            headers={**auth_headers, "Accept": "text/event-stream"},
        ) as resp:
            assert resp.status_code == 200
            assert "text/event-stream" in resp.headers["content-type"]

            events: list[tuple[str, dict]] = []
            buffer = ""
            async for raw_bytes in resp.aiter_bytes():
                buffer += raw_bytes.decode()
                while "\n\n" in buffer:
                    chunk, buffer = buffer.split("\n\n", 1)
                    if not chunk.strip() or chunk.startswith(":"):
                        continue
                    name, data_line = "", ""
                    for line in chunk.split("\n"):
                        if line.startswith("event:"):
                            name = line[6:].strip()
                        elif line.startswith("data:"):
                            data_line = line[5:].strip()
                    if name and data_line:
                        events.append((name, json.loads(data_line)))

    event_names = [e[0] for e in events]
    assert "primal_chunk" in event_names
    assert event_names[-1] == "primal_done"

    chunks = [e[1]["delta"] for e in events if e[0] == "primal_chunk"]
    full = "".join(chunks)
    assert full == "unga bunga code fast"


@pytest.mark.asyncio
async def test_primal_endpoint_rejects_empty_text(auth_headers, monkeypatch):
    from app import auth

    async def _fake_user(_=None):
        from app.auth import AuthUser
        import uuid
        return AuthUser(id=uuid.uuid4(), email="test@test.com", tier="core")

    monkeypatch.setattr(auth, "get_current_user", _fake_user)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/primal",
            json={"message_id": "msg-abc", "text": ""},
            headers=auth_headers,
        )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_primal_endpoint_rejects_missing_message_id(auth_headers, monkeypatch):
    from app import auth

    async def _fake_user(_=None):
        from app.auth import AuthUser
        import uuid
        return AuthUser(id=uuid.uuid4(), email="test@test.com", tier="core")

    monkeypatch.setattr(auth, "get_current_user", _fake_user)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/primal",
            json={"text": "some text"},
            headers=auth_headers,
        )
    assert resp.status_code == 422
```

- [ ] Run tests — they must fail (endpoint doesn't exist):
```bash
cd /Users/anas/Projects/hexallabs/backend
uv run pytest tests/test_primal_endpoint.py -v 2>&1 | head -40
```
Expected: FAILED — 404

- [ ] Commit failing tests:
```bash
git add tests/test_primal_endpoint.py
git commit -m "test(primal): add failing tests for POST /api/primal endpoint"
```

---

### Task 3: Implement `POST /api/primal` endpoint

**Files:**
- Create: `backend/app/api/primal.py`
- Modify: `backend/app/main.py`

- [ ] Create `backend/app/api/primal.py`:

```python
"""POST /api/primal — Primal Protocol on-demand rewrite endpoint.

Stateless rewrite pass: no DB writes. Exposed as standalone endpoint so
the frontend can trigger post-hoc on any completed Apex or Oracle message.
"""
from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.auth import AuthUser, get_current_user
from app.llm.base import Message
from app.llm.factory import get_client
from app.sse.events import SseEvent, format_event
from app.synthesis.apex import _PRIMAL_SYSTEM

router = APIRouter(prefix="/api", tags=["primal"])

_SSE_HEADERS = {
    "Cache-Control": "no-cache, no-transform",
    "X-Accel-Buffering": "no",
    "Connection": "keep-alive",
}


class PrimalRequest(BaseModel):
    message_id: str = Field(min_length=1)
    text: str = Field(min_length=1)


@router.post("/primal")
async def primal(
    req: PrimalRequest,
    user: AuthUser = Depends(get_current_user),  # noqa: B008
) -> StreamingResponse:
    apex_client = get_client("Apex")

    async def _stream() -> AsyncIterator[bytes]:
        messages: list[Message] = [
            Message(role="system", content=_PRIMAL_SYSTEM, cache=True),
            Message(role="user", content=req.text),
        ]
        async for chunk in apex_client.stream(messages):
            if chunk.delta:
                yield format_event(SseEvent("primal_chunk", {"delta": chunk.delta}))
        yield format_event(SseEvent("primal_done", {}))

    return StreamingResponse(
        _stream(),
        media_type="text/event-stream",
        headers=_SSE_HEADERS,
    )
```

- [ ] Check how `app/main.py` registers routers:
```bash
grep -n "router\|include_router\|from app" /Users/anas/Projects/hexallabs/backend/app/main.py | head -30
```

- [ ] Register the new router in `backend/app/main.py`:
```python
from app.api.primal import router as primal_router
app.include_router(primal_router)
```

- [ ] Run tests — they must now pass:
```bash
cd /Users/anas/Projects/hexallabs/backend
uv run pytest tests/test_primal_endpoint.py -v
```
Expected: 3 passed

- [ ] Full regression check:
```bash
uv run pytest --ignore=tests/test_live.py -q 2>&1 | tail -10
```

- [ ] Commit:
```bash
git add app/api/primal.py app/main.py
git commit -m "feat(api): add POST /api/primal streaming endpoint for Primal Protocol rewrites"
```

---

### Task 4: Add new SSE event types to frontend types

**Files:**
- Modify: `frontend/lib/types.ts`

- [ ] Add `primal_chunk` and `primal_done` to `SseEventMap`:

```typescript
  primal:         { text: string }
  primal_chunk:   { delta: string }
  primal_done:    Record<string, never>
```

- [ ] Add `primalText` and `primalStreaming` to `ChatMessage`:

```typescript
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  model?: ModelName
  isStreaming?: boolean
  primalText?: string
  primalStreaming?: boolean
}
```

- [ ] TypeScript check:
```bash
cd /Users/anas/Projects/hexallabs/frontend
bun run tsc --noEmit 2>&1 | head -20
```

- [ ] Commit:
```bash
git add frontend/lib/types.ts
git commit -m "feat(types): add primal_chunk/primal_done SSE events and primalText to ChatMessage"
```

---

### Task 5: Add `streamPrimal` utility

**Files:**
- Modify: `frontend/lib/sse.ts`

- [ ] Append `streamPrimal` to `frontend/lib/sse.ts`:

```typescript
export async function streamPrimal(
  apiBase: string,
  token: string,
  messageId: string,
  text: string,
  onChunk: (delta: string) => void,
  onDone: () => void,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(`${apiBase}/api/primal`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
    },
    body: JSON.stringify({ message_id: messageId, text }),
    signal,
  })

  if (!res.ok) {
    throw new Error(`Primal Protocol request failed: ${res.status}`)
  }

  const reader = res.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const parts = buffer.split('\n\n')
    buffer = parts.pop() ?? ''
    for (const chunk of parts) {
      if (!chunk.trim() || chunk.startsWith(':')) continue
      let eventName = ''
      let dataLine = ''
      for (const line of chunk.split('\n')) {
        if (line.startsWith('event:')) eventName = line.slice(6).trim()
        else if (line.startsWith('data:')) dataLine = line.slice(5).trim()
      }
      if (!eventName || !dataLine) continue
      try {
        const parsed = JSON.parse(dataLine) as Record<string, unknown>
        if (eventName === 'primal_chunk' && typeof parsed.delta === 'string') {
          onChunk(parsed.delta)
        } else if (eventName === 'primal_done') {
          onDone()
        }
      } catch {
        // malformed — skip
      }
    }
  }
}
```

- [ ] TypeScript check:
```bash
cd /Users/anas/Projects/hexallabs/frontend
bun run tsc --noEmit 2>&1 | head -20
```

- [ ] Commit:
```bash
git add frontend/lib/sse.ts
git commit -m "feat(sse): add streamPrimal utility for POST /api/primal streaming"
```

---

### Task 6: Build `PrimalButton` component

**Files:**
- Create: `frontend/components/chat/PrimalButton.tsx`

- [ ] Create `frontend/components/chat/PrimalButton.tsx`:

```tsx
'use client'

interface PrimalButtonProps {
  active: boolean
  loading: boolean
  onClick: () => void
}

export function PrimalButton({ active, loading, onClick }: PrimalButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      aria-pressed={active}
      aria-label={active ? 'Deactivate Primal Protocol' : 'Activate Primal Protocol'}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.3rem',
        padding: '0.2rem 0.6rem',
        borderRadius: '999px',
        border: `1.5px solid ${active ? '#6290c3' : 'rgba(168,144,128,0.35)'}`,
        backgroundColor: active ? 'rgba(98,144,195,0.12)' : 'transparent',
        color: active ? '#6290c3' : 'rgba(168,144,128,0.7)',
        fontSize: '10px',
        fontWeight: 700,
        letterSpacing: '0.06em',
        textTransform: 'uppercase',
        cursor: loading ? 'wait' : 'pointer',
        opacity: loading ? 0.6 : 1,
        transition: 'all 300ms cubic-bezier(0.16,1,0.3,1)',
        userSelect: 'none',
      }}
      onMouseEnter={e => { if (!loading) (e.currentTarget as HTMLButtonElement).style.transform = 'scale(1.02)' }}
      onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.transform = 'scale(1)' }}
      onMouseDown={e => { (e.currentTarget as HTMLButtonElement).style.transform = 'scale(0.98)' }}
      onMouseUp={e => { (e.currentTarget as HTMLButtonElement).style.transform = 'scale(1.02)' }}
    >
      {loading ? (
        <span style={{ display: 'inline-block', width: '8px', height: '8px', borderRadius: '50%', border: '1.5px solid currentColor', borderTopColor: 'transparent', animation: 'spin 0.7s linear infinite' }} />
      ) : (
        <span style={{ fontSize: '11px', lineHeight: 1 }}>⚡</span>
      )}
      Primal Protocol
    </button>
  )
}
```

- [ ] TypeScript check:
```bash
cd /Users/anas/Projects/hexallabs/frontend
bun run tsc --noEmit 2>&1 | head -20
```

- [ ] Commit:
```bash
git add frontend/components/chat/PrimalButton.tsx
git commit -m "feat(ui): add PrimalButton with denim active state and scale animations"
```

---

### Task 7: Wire primal state and cross-fade into `Message.tsx`

**Files:**
- Modify: `frontend/components/chat/Message.tsx`
- Modify: `frontend/app/globals.css`

- [ ] Add `primalFade` keyframe to `frontend/app/globals.css`:
```css
@keyframes primalFade {
  from { opacity: 0; filter: blur(2px); }
  to   { opacity: 1; filter: blur(0); }
}
```

- [ ] Update `Message.tsx` to accept `onPrimal` and `isPrimalEnabled` props, render `PrimalButton` below completed assistant messages, and cross-fade content on toggle:

```tsx
import { PrimalButton } from './PrimalButton'

interface MessageProps {
  msg: ChatMessage
  onPrimal?: () => void
  isPrimalEnabled?: boolean
}

export function Message({ msg, onPrimal, isPrimalEnabled }: MessageProps) {
  const isUser = msg.role === 'user'
  const ref = useRef<HTMLDivElement>(null)
  const contentRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    el.style.animation = 'msgIn 0.28s cubic-bezier(0.16,1,0.3,1) both'
  }, [])

  useEffect(() => {
    const el = contentRef.current
    if (!el) return
    el.style.animation = 'none'
    void el.offsetHeight
    el.style.animation = 'primalFade 300ms cubic-bezier(0.16,1,0.3,1) both'
  }, [isPrimalEnabled])

  const showPrimalButton = !isUser && !msg.isStreaming && msg.content.trim().length > 0 && typeof onPrimal === 'function'
  const displayContent = isPrimalEnabled && msg.primalText ? msg.primalText : msg.content
  const isDisplayStreaming = isPrimalEnabled && msg.primalStreaming ? true : (!isPrimalEnabled && msg.isStreaming)

  return (
    <div ref={ref} className="w-full max-w-4xl mx-auto px-6 py-1.5" style={{ opacity: 0 }}>
      {isUser ? (
        <div className="flex justify-end">
          <div className="max-w-[75%] px-4 py-3 text-sm leading-relaxed bg-[#6290c3] text-white rounded-3xl rounded-br-lg" style={{ wordBreak: 'break-word', whiteSpace: 'pre-wrap' }}>
            {msg.content}
          </div>
        </div>
      ) : (
        <div className="text-sm leading-relaxed text-[#2c2c2c]">
          {msg.model && (
            <p className="text-[10px] font-black text-[#a89080]/70 uppercase tracking-widest mb-2">
              {MODEL_DISPLAY[msg.model] ?? msg.model}
            </p>
          )}
          <div ref={contentRef}>
            <MarkdownBody content={displayContent} isStreaming={isDisplayStreaming} />
          </div>
          {showPrimalButton && (
            <div className="mt-2">
              <PrimalButton active={!!isPrimalEnabled} loading={!!msg.primalStreaming} onClick={onPrimal!} />
            </div>
          )}
        </div>
      )}
    </div>
  )
}
```

- [ ] TypeScript check:
```bash
cd /Users/anas/Projects/hexallabs/frontend
bun run tsc --noEmit 2>&1 | head -20
```

- [ ] Commit:
```bash
git add frontend/components/chat/Message.tsx frontend/app/globals.css
git commit -m "feat(ui): wire PrimalButton into Message with cross-fade animation on toggle"
```

---

### Task 8: Add per-message primal state management to `ChatWindow.tsx`

**Files:**
- Modify: `frontend/components/chat/ChatWindow.tsx`

- [ ] Add import:
```typescript
import { streamPrimal } from '@/lib/sse'
```

- [ ] Add state:
```typescript
const [primalState, setPrimalState] = useState<Record<string, 'off' | 'loading' | 'on'>>({})
```

- [ ] Add `handlePrimalToggle` callback:

```typescript
const handlePrimalToggle = useCallback(async (msgId: string, text: string, hasExistingRewrite: boolean) => {
  if (primalState[msgId] === 'on') {
    setPrimalState(prev => ({ ...prev, [msgId]: 'off' }))
    return
  }
  if (hasExistingRewrite) {
    setPrimalState(prev => ({ ...prev, [msgId]: 'on' }))
    return
  }
  setPrimalState(prev => ({ ...prev, [msgId]: 'loading' }))
  setTurns(prev => prev.map(turn => {
    if (turn.type !== 'single' || turn.msg.id !== msgId) return turn
    return { ...turn, msg: { ...turn.msg, primalStreaming: true } }
  }))

  const session = await getSession()
  const token = (session as { accessToken?: string })?.accessToken ?? ''
  const apiBase = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'
  const parts: string[] = []

  try {
    await streamPrimal(
      apiBase, token, msgId, text,
      (delta) => {
        parts.push(delta)
        const partial = parts.join('')
        setTurns(prev => prev.map(turn => {
          if (turn.type !== 'single' || turn.msg.id !== msgId) return turn
          return { ...turn, msg: { ...turn.msg, primalText: partial } }
        }))
      },
      () => {
        setPrimalState(prev => ({ ...prev, [msgId]: 'on' }))
        setTurns(prev => prev.map(turn => {
          if (turn.type !== 'single' || turn.msg.id !== msgId) return turn
          return { ...turn, msg: { ...turn.msg, primalStreaming: false } }
        }))
      },
    )
  } catch {
    setPrimalState(prev => ({ ...prev, [msgId]: 'off' }))
    setTurns(prev => prev.map(turn => {
      if (turn.type !== 'single' || turn.msg.id !== msgId) return turn
      return { ...turn, msg: { ...turn.msg, primalStreaming: false, primalText: undefined } }
    }))
  }
}, [primalState, setTurns])
```

- [ ] Update single turn render to pass `onPrimal` and `isPrimalEnabled`:

```tsx
<Message
  msg={turn.msg}
  onPrimal={
    turn.msg.role === 'assistant' && !turn.msg.isStreaming
      ? () => handlePrimalToggle(turn.msg.id, turn.msg.content, !!turn.msg.primalText)
      : undefined
  }
  isPrimalEnabled={primalState[turn.msg.id] === 'on' || primalState[turn.msg.id] === 'loading'}
/>
```

- [ ] Add `import { getSession } from 'next-auth/react'` at the top.

- [ ] TypeScript check:
```bash
cd /Users/anas/Projects/hexallabs/frontend
bun run tsc --noEmit 2>&1 | head -30
```

- [ ] Commit:
```bash
git add frontend/components/chat/ChatWindow.tsx
git commit -m "feat(chat): wire per-message Primal Protocol toggle with streaming rewrite"
```

---

### Task 9: End-to-end verification

- [ ] Full backend tests:
```bash
cd /Users/anas/Projects/hexallabs/backend
uv run pytest --ignore=tests/test_live.py -q 2>&1 | tail -15
```
Expected: all passing

- [ ] Verify endpoint reachable (expect 401/403, not 404):
```bash
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/primal \
  -H "Content-Type: application/json" \
  -d '{"message_id":"x","text":"test"}'
```
Expected: 401 or 403

- [ ] Frontend build:
```bash
cd /Users/anas/Projects/hexallabs/frontend
bun run build 2>&1 | tail -20
```
Expected: compiled successfully

---

### Implementation Notes

- **Token acquisition:** Use `getSession()` from NextAuth directly to get JWT — avoids triggering a network request via `buildQueryRequest`.
- **Council messages:** Primal Protocol button only on `turn.type === 'single'` (Oracle/Apex synthesis). Council model cards excluded by design.
- **Existing inline primal:** `primal_protocol: true` on `QueryRequest` still works (emits `primal` event, not `primal_chunk`/`primal_done`). New endpoint is complementary for post-hoc toggling.
