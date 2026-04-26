# Workflow Builder (Directed Model Graph) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a user-defined DAG workflow mode where each node is a model with an assigned role, edges define handoff paths, and the graph executes in topological order with parallel branches where possible.

**Architecture:** The backend executor (`workflow/executor.py`) already handles DAG execution via topological sort but runs nodes serially — extend it to run independent nodes concurrently using `asyncio.gather` via a shared queue. The frontend needs a new `WorkflowBuilder` canvas component (CSS absolute positioning + inline SVG, no graph library), a `WorkflowSelector` panel, a `workflow` mode wired into `SlashMenu` and `ChatWindow`, and localStorage persistence for saved workflows.

**Tech Stack:** Next.js App Router + TypeScript strict + Tailwind (4-color palette) + FastAPI async + SSE + `asyncio.Queue` for parallel node execution + localStorage.

---

### Task 1: Backend — Add parallel node execution and new SSE events

**Files:**
- Modify: `backend/app/sse/events.py`
- Modify: `backend/app/workflow/executor.py`
- Create: `backend/tests/test_workflow_parallel.py`

- [ ] Add `workflow_node_start` and `workflow_node_done` to `_ALLOWED_EVENTS` in `backend/app/sse/events.py`:

```python
_ALLOWED_EVENTS = {
    # ... existing events ...
    "workflow_node_start",   # {node_id: str, model: str, role: str}
    "workflow_node_done",    # {node_id: str, model: str, tokens: int}
}
```

Also update docstring:
```
workflow_node_start  {node_id: str, model: str, role: str}
workflow_node_done   {node_id: str, model: str, tokens: int}
```

- [ ] Write test `backend/tests/test_workflow_parallel.py`:

```python
import pytest
from app.workflow.executor import _topo_sort


def test_topo_sort_simple_chain():
    nodes = [
        {"id": "a", "inputs": []},
        {"id": "b", "inputs": ["a"]},
        {"id": "c", "inputs": ["b"]},
    ]
    result = _topo_sort(nodes)
    assert result is not None
    ids = [n["id"] for n in result]
    assert ids.index("a") < ids.index("b") < ids.index("c")


def test_topo_sort_detects_cycle():
    nodes = [
        {"id": "a", "inputs": ["b"]},
        {"id": "b", "inputs": ["a"]},
    ]
    assert _topo_sort(nodes) is None


def test_topo_sort_parallel_branches():
    nodes = [
        {"id": "root",  "inputs": []},
        {"id": "left",  "inputs": ["root"]},
        {"id": "right", "inputs": ["root"]},
        {"id": "merge", "inputs": ["left", "right"]},
    ]
    result = _topo_sort(nodes)
    assert result is not None
    ids = [n["id"] for n in result]
    assert ids.index("root") < ids.index("left")
    assert ids.index("root") < ids.index("right")
    assert ids.index("left") < ids.index("merge")
    assert ids.index("right") < ids.index("merge")
```

- [ ] Run test:
```bash
cd /Users/anas/Projects/hexallabs/backend && uv run pytest tests/test_workflow_parallel.py -v
```
Expected: 3 passed (if `_topo_sort` is exported) — fix export if needed.

- [ ] Refactor `_workflow_stream` in `backend/app/workflow/executor.py` to group topo-sorted nodes into levels and run each level concurrently via `asyncio.Queue`:

```python
import asyncio
from collections import defaultdict

# Group into levels after topo sort
levels: list[list[dict[str, object]]] = []
completed_ids: set[str] = set()
remaining = list(ordered)
while remaining:
    level = [n for n in remaining if all(uid in completed_ids for uid in (n.get("inputs") or []))]
    if not level:
        break
    levels.append(level)
    for n in level:
        completed_ids.add(str(n["id"]))
    remaining = [n for n in remaining if n not in level]

# Execute each level's nodes concurrently
for level in levels:
    queue: asyncio.Queue[bytes | None] = asyncio.Queue()

    async def run_one(node: dict[str, object]) -> None:
        node_id = str(node["id"])
        node_type = str(node.get("type", "model"))
        whitelabel = str(node.get("model", ""))
        node_role = str(node.get("role", ""))
        node_inputs: list[str] = list(node.get("inputs") or [])

        node_input = (
            prompt if not node_inputs
            else "\n\n---\n\n".join(node_outputs[uid] for uid in node_inputs if uid in node_outputs) or prompt
        )

        if node_type != "model":
            if node_type == "passthrough":
                node_outputs[node_id] = node_input
            elif node_type == "prompt_template":
                config: dict[str, object] = dict(node.get("config") or {})
                template = str(config.get("template", "{input}"))
                try:
                    node_outputs[node_id] = template.format(input=node_input)
                except (KeyError, ValueError) as exc:
                    await queue.put(format_event(SseEvent("error", {"hex": node_id, "code": "TemplateError", "message": str(exc)[:500]})))
                    node_outputs[node_id] = node_input
            return

        try:
            client = get_client(whitelabel)
        except KeyError as exc:
            await queue.put(format_event(SseEvent("error", {"hex": node_id, "code": "UnknownModel", "message": str(exc)[:500]})))
            node_outputs[node_id] = ""
            return

        await queue.put(format_event(SseEvent("workflow_node_start", {"node_id": node_id, "model": whitelabel, "role": node_role})))
        await queue.put(format_event(SseEvent("hex_start", {"hex": whitelabel})))

        messages = []
        if scout_context_text:
            messages.append(LLMMessage(role="system", content=scout_context_text, cache=True))
        messages.append(LLMMessage(role="user", content=node_input))

        collected: list[str] = []
        total_tokens: int | None = None
        cached_tokens: int | None = None
        node_failed = False

        try:
            async for chunk in client.stream(messages):
                if chunk.delta:
                    collected.append(chunk.delta)
                    await queue.put(format_event(SseEvent("token", {"hex": whitelabel, "delta": chunk.delta})))
                if chunk.total_tokens is not None:
                    total_tokens = chunk.total_tokens
                if chunk.cached_tokens is not None:
                    cached_tokens = chunk.cached_tokens
        except Exception as exc:
            logger.exception("workflow: node %r (%s) failed", node_id, whitelabel)
            await queue.put(format_event(SseEvent("error", {"hex": whitelabel, "code": type(exc).__name__, "message": str(exc)[:500]})))
            node_failed = True

        full_text = "".join(collected)
        node_outputs[node_id] = full_text

        if not node_failed:
            db.add(MessageRow(query_id=query_row.id, role="model", model=whitelabel, content=full_text, tokens_out=total_tokens, stage="workflow"))
            await queue.put(format_event(SseEvent("hex_done", {"hex": whitelabel, "tokens": total_tokens or 0, "cached_tokens": cached_tokens or 0})))
            await queue.put(format_event(SseEvent("workflow_node_done", {"node_id": node_id, "model": whitelabel, "tokens": total_tokens or 0})))
            if quota is not None and total_tokens:
                await QuotaService.deduct(db, quota, total_tokens, whitelabel)

    tasks = [asyncio.create_task(run_one(n)) for n in level]

    async def drain_level() -> None:
        await asyncio.gather(*tasks)
        await queue.put(None)

    asyncio.create_task(drain_level())

    while True:
        item = await queue.get()
        if item is None:
            break
        yield item
```

- [ ] Commit:
```bash
git add backend/app/sse/events.py backend/app/workflow/executor.py backend/tests/test_workflow_parallel.py
git commit -m "feat(workflow): add parallel level execution and workflow_node_start/done SSE events"
```

---

### Task 2: Frontend types — workflow mode and data model

**Files:**
- Modify: `frontend/lib/types.ts`

- [ ] Add `'workflow'` to `Mode` union:
```typescript
export type Mode = 'oracle' | 'council' | 'relay' | 'workflow'
```

- [ ] Add workflow interfaces:
```typescript
export interface WorkflowNode {
  id: string
  model: ModelName
  role: string
  dependsOn: string[]
}

export interface WorkflowDef {
  id: string
  name: string
  nodes: WorkflowNode[]
}

export interface SseWorkflowNodeStart { node_id: string; model: string; role: string }
export interface SseWorkflowNodeDone  { node_id: string; model: string; tokens: number }
```

- [ ] Add to `SseEventMap`:
```typescript
  workflow_node_start: SseWorkflowNodeStart
  workflow_node_done:  SseWorkflowNodeDone
```

- [ ] Add `workflow_def` to `QueryRequest`:
```typescript
export interface QueryRequest {
  // ...existing...
  workflow_def?: WorkflowDef
}
```

- [ ] TypeScript check:
```bash
cd /Users/anas/Projects/hexallabs/frontend && bun run tsc --noEmit 2>&1 | head -20
```

- [ ] Commit:
```bash
git add frontend/lib/types.ts
git commit -m "feat(workflow): add WorkflowNode/WorkflowDef types and workflow mode"
```

---

### Task 3: Workflow localStorage persistence

**Files:**
- Create: `frontend/lib/workflows.ts`

- [ ] Create `frontend/lib/workflows.ts`:

```typescript
import { WorkflowDef } from './types'

const KEY = 'hexal_workflows'

export function loadWorkflows(): WorkflowDef[] {
  if (typeof window === 'undefined') return []
  try {
    return JSON.parse(localStorage.getItem(KEY) ?? '[]') as WorkflowDef[]
  } catch {
    return []
  }
}

export function saveWorkflow(def: WorkflowDef): void {
  const all = loadWorkflows()
  const idx = all.findIndex(w => w.id === def.id)
  if (idx >= 0) { all[idx] = def } else { all.push(def) }
  localStorage.setItem(KEY, JSON.stringify(all))
}

export function deleteWorkflow(id: string): void {
  localStorage.setItem(KEY, JSON.stringify(loadWorkflows().filter(w => w.id !== id)))
}
```

- [ ] Commit:
```bash
git add frontend/lib/workflows.ts
git commit -m "feat(workflow): add workflow localStorage persistence helpers"
```

---

### Task 4: `WorkflowBuilder` canvas component

**Files:**
- Create: `frontend/components/chat/WorkflowBuilder.tsx`

- [ ] Create `frontend/components/chat/WorkflowBuilder.tsx`:

```tsx
'use client'
import { useState, useRef } from 'react'
import { v4 as uuidv4 } from 'uuid'
import { X, Play, Save } from 'lucide-react'
import { WorkflowDef, WorkflowNode, ModelName, MODELS, MODEL_DISPLAY } from '@/lib/types'

interface CanvasNode extends WorkflowNode {
  x: number
  y: number
}

const NODE_W = 160
const NODE_H = 72

function getEdgePath(from: CanvasNode, to: CanvasNode): string {
  const x1 = from.x + NODE_W
  const y1 = from.y + NODE_H / 2
  const x2 = to.x
  const y2 = to.y + NODE_H / 2
  const cx = (x1 + x2) / 2
  return `M ${x1} ${y1} C ${cx} ${y1}, ${cx} ${y2}, ${x2} ${y2}`
}

interface Props {
  initial?: WorkflowDef
  onRun: (def: WorkflowDef) => void
  onSave: (def: WorkflowDef) => void
  onClose: () => void
}

export function WorkflowBuilder({ initial, onRun, onSave, onClose }: Props) {
  const [name, setName] = useState(initial?.name ?? 'My Workflow')
  const [nodes, setNodes] = useState<CanvasNode[]>(() => {
    if (!initial) return []
    return initial.nodes.map((n, i) => ({ ...n, x: 60 + (i % 4) * 180, y: 60 + Math.floor(i / 4) * 120 }))
  })
  const [edgeFrom, setEdgeFrom] = useState<string | null>(null)
  const dragRef = useRef<{ id: string; offsetX: number; offsetY: number } | null>(null)

  function addNode(model: ModelName) {
    const id = uuidv4().slice(0, 8)
    setNodes(prev => [...prev, { id, model, role: '', dependsOn: [], x: 40 + (prev.length % 4) * 180, y: 40 + Math.floor(prev.length / 4) * 120 }])
  }

  function removeNode(id: string) {
    setNodes(prev => prev.filter(n => n.id !== id).map(n => ({ ...n, dependsOn: n.dependsOn.filter(d => d !== id) })))
    if (edgeFrom === id) setEdgeFrom(null)
  }

  function updateRole(id: string, role: string) {
    setNodes(prev => prev.map(n => n.id === id ? { ...n, role } : n))
  }

  function handleNodeClick(id: string) {
    if (!edgeFrom) { setEdgeFrom(id); return }
    if (edgeFrom === id) { setEdgeFrom(null); return }
    setNodes(prev => prev.map(n => n.id === id && !n.dependsOn.includes(edgeFrom!) ? { ...n, dependsOn: [...n.dependsOn, edgeFrom!] } : n))
    setEdgeFrom(null)
  }

  function removeEdge(fromId: string, toId: string) {
    setNodes(prev => prev.map(n => n.id === toId ? { ...n, dependsOn: n.dependsOn.filter(d => d !== fromId) } : n))
  }

  function onMouseDown(e: React.MouseEvent, id: string) {
    e.stopPropagation()
    const node = nodes.find(n => n.id === id)
    if (!node) return
    dragRef.current = { id, offsetX: e.clientX - node.x, offsetY: e.clientY - node.y }
  }

  function onMouseMove(e: React.MouseEvent) {
    if (!dragRef.current) return
    const { id, offsetX, offsetY } = dragRef.current
    setNodes(prev => prev.map(n => n.id === id ? { ...n, x: Math.max(0, e.clientX - offsetX), y: Math.max(0, e.clientY - offsetY) } : n))
  }

  function toDef(): WorkflowDef {
    return { id: initial?.id ?? uuidv4(), name, nodes: nodes.map(({ x: _x, y: _y, ...n }) => n) }
  }

  const hasNodes = nodes.length > 0

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#2c2c2c]/60 backdrop-blur-sm">
      <div className="bg-[#f5f1ed] rounded-3xl shadow-2xl flex flex-col overflow-hidden" style={{ width: 920, maxHeight: '90vh', animation: 'fadeUp 0.3s cubic-bezier(0.16,1,0.3,1) both' }}>
        {/* Header */}
        <div className="flex items-center gap-3 px-5 py-3.5 border-b border-[#a89080]/20 shrink-0">
          <input value={name} onChange={e => setName(e.target.value)} className="flex-1 bg-transparent text-sm font-black text-[#2c2c2c] outline-none border-b-2 border-transparent focus:border-[#2c2c2c] transition-colors duration-300 pb-0.5" placeholder="Workflow name…" />
          <button onClick={() => onSave(toDef())} disabled={!hasNodes} className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold rounded-full border border-[#a89080]/40 text-[#a89080] hover:text-[#2c2c2c] hover:border-[#2c2c2c] disabled:opacity-30 disabled:cursor-not-allowed transition-colors duration-200">
            <Save size={12} /> Save
          </button>
          <button onClick={() => onRun(toDef())} disabled={!hasNodes} className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold rounded-full bg-[#2c2c2c] text-[#f5f1ed] hover:scale-[1.02] active:scale-[0.98] disabled:opacity-30 disabled:cursor-not-allowed transition-transform duration-150">
            <Play size={12} /> Run
          </button>
          <button onClick={onClose} className="w-7 h-7 flex items-center justify-center rounded-full text-[#a89080] hover:text-[#2c2c2c] hover:bg-[#2c2c2c]/6 transition-colors">
            <X size={16} />
          </button>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Model palette */}
          <div className="w-44 border-r border-[#a89080]/20 p-3 flex flex-col gap-1 overflow-y-auto shrink-0">
            <p className="text-[10px] font-bold text-[#a89080] uppercase tracking-widest mb-1">Models</p>
            {MODELS.map(m => (
              <button key={m} onClick={() => addNode(m)} className="flex items-center gap-2 px-2.5 py-2 rounded-xl text-left text-sm font-semibold text-[#2c2c2c] hover:bg-[#2c2c2c]/6 active:bg-[#2c2c2c]/10 transition-colors duration-150">
                <span className="w-2 h-2 rounded-full bg-[#6290c3] shrink-0" />
                {MODEL_DISPLAY[m]}
              </button>
            ))}
            <div className="mt-3 pt-3 border-t border-[#a89080]/20">
              <p className="text-[10px] text-[#a89080] leading-tight">Click model to add. Click node then another to draw edge. Drag to reposition. Click edge to delete.</p>
              {edgeFrom && <div className="mt-2 px-2 py-1.5 rounded-lg bg-[#6290c3]/15 text-[10px] font-bold text-[#6290c3]">Click target node →</div>}
            </div>
          </div>

          {/* Canvas */}
          <div
            className="relative flex-1 overflow-hidden"
            style={{ cursor: edgeFrom ? 'crosshair' : 'default' }}
            onMouseMove={onMouseMove}
            onMouseUp={() => { dragRef.current = null }}
            onMouseLeave={() => { dragRef.current = null }}
          >
            <svg className="absolute inset-0 w-full h-full pointer-events-none" overflow="visible">
              <defs>
                <marker id="wf-arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
                  <path d="M0,0 L0,6 L8,3 z" fill="#a89080" />
                </marker>
              </defs>
              {nodes.flatMap(to =>
                to.dependsOn.map(fromId => {
                  const from = nodes.find(n => n.id === fromId)
                  if (!from) return null
                  return (
                    <g key={`${fromId}-${to.id}`} className="pointer-events-auto" onClick={() => removeEdge(fromId, to.id)} style={{ cursor: 'pointer' }}>
                      <path d={getEdgePath(from, to)} fill="none" stroke="#a89080" strokeWidth={2} markerEnd="url(#wf-arrow)" strokeDasharray="4 3" />
                    </g>
                  )
                })
              )}
            </svg>

            {nodes.map(node => (
              <div key={node.id} onMouseDown={e => onMouseDown(e, node.id)} style={{ position: 'absolute', left: node.x, top: node.y, width: NODE_W, userSelect: 'none' }}>
                <div
                  className={`rounded-2xl border-2 bg-[#f5f1ed] shadow-sm transition-all duration-200 ${
                    edgeFrom === node.id ? 'border-[#6290c3] shadow-[#6290c3]/20 shadow-md'
                    : edgeFrom ? 'border-[#a89080]/60 hover:border-[#6290c3] cursor-pointer'
                    : 'border-[#a89080]/30 hover:border-[#a89080]/60 hover:shadow-md hover:-translate-y-0.5'
                  }`}
                  onClick={() => handleNodeClick(node.id)}
                >
                  <div className="flex items-center justify-between px-3 pt-2.5 pb-1">
                    <span className="text-xs font-black text-[#2c2c2c]">{MODEL_DISPLAY[node.model]}</span>
                    <button onMouseDown={e => e.stopPropagation()} onClick={e => { e.stopPropagation(); removeNode(node.id) }} className="w-4 h-4 flex items-center justify-center rounded-full text-[#a89080] hover:text-[#2c2c2c] hover:bg-[#2c2c2c]/8 transition-colors">
                      <X size={10} />
                    </button>
                  </div>
                  <input
                    value={node.role}
                    onChange={e => updateRole(node.id, e.target.value)}
                    onMouseDown={e => e.stopPropagation()}
                    onClick={e => e.stopPropagation()}
                    placeholder="Role…"
                    className="w-full px-3 pb-2 text-[10px] bg-transparent outline-none text-[#a89080] placeholder:text-[#a89080]/40 focus:text-[#2c2c2c] transition-colors duration-200 truncate"
                  />
                </div>
              </div>
            ))}

            {nodes.length === 0 && (
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <p className="text-sm text-[#a89080]/60 font-semibold">Add models from the left panel</p>
              </div>
            )}
          </div>
        </div>
      </div>

      <style>{`
        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(16px) scale(0.98); }
          to   { opacity: 1; transform: translateY(0) scale(1); }
        }
      `}</style>
    </div>
  )
}
```

- [ ] TypeScript check:
```bash
cd /Users/anas/Projects/hexallabs/frontend && bun run tsc --noEmit 2>&1 | head -20
```

- [ ] Commit:
```bash
git add frontend/components/chat/WorkflowBuilder.tsx
git commit -m "feat(workflow): add WorkflowBuilder canvas component with CSS+SVG node editor"
```

---

### Task 5: `WorkflowSelector` panel

**Files:**
- Create: `frontend/components/chat/WorkflowSelector.tsx`

- [ ] Create `frontend/components/chat/WorkflowSelector.tsx`:

```tsx
'use client'
import { useEffect, useState } from 'react'
import { Plus, Play, Trash2, Pencil } from 'lucide-react'
import { WorkflowDef } from '@/lib/types'
import { loadWorkflows, deleteWorkflow } from '@/lib/workflows'

interface Props {
  onRun: (def: WorkflowDef) => void
  onEdit: (def: WorkflowDef | null) => void
}

export function WorkflowSelector({ onRun, onEdit }: Props) {
  const [workflows, setWorkflows] = useState<WorkflowDef[]>([])

  useEffect(() => { setWorkflows(loadWorkflows()) }, [])

  function handleDelete(id: string) {
    deleteWorkflow(id)
    setWorkflows(prev => prev.filter(w => w.id !== id))
  }

  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center justify-between px-1 mb-1">
        <p className="text-[10px] font-bold text-[#a89080] uppercase tracking-widest">Workflows</p>
        <button onClick={() => onEdit(null)} className="flex items-center gap-1 text-[10px] font-bold text-[#6290c3] hover:text-[#2c2c2c] transition-colors">
          <Plus size={11} /> New
        </button>
      </div>
      {workflows.length === 0 && <p className="text-xs text-[#a89080]/60 px-1 py-2">No saved workflows. Create one.</p>}
      {workflows.map(w => (
        <div key={w.id} className="flex items-center gap-2 px-2.5 py-2 rounded-xl hover:bg-[#2c2c2c]/5 group transition-colors duration-150">
          <span className="flex-1 text-sm font-semibold text-[#2c2c2c] truncate">{w.name}</span>
          <span className="text-[10px] text-[#a89080]">{w.nodes.length} nodes</span>
          <button onClick={() => onEdit(w)} className="opacity-0 group-hover:opacity-100 w-6 h-6 flex items-center justify-center rounded-full text-[#a89080] hover:text-[#2c2c2c] transition-all"><Pencil size={11} /></button>
          <button onClick={() => handleDelete(w.id)} className="opacity-0 group-hover:opacity-100 w-6 h-6 flex items-center justify-center rounded-full text-[#a89080] hover:text-[#2c2c2c] transition-all"><Trash2 size={11} /></button>
          <button onClick={() => onRun(w)} className="w-6 h-6 flex items-center justify-center rounded-full bg-[#2c2c2c] text-[#f5f1ed] hover:scale-[1.05] active:scale-[0.95] transition-transform duration-150"><Play size={10} /></button>
        </div>
      ))}
    </div>
  )
}
```

- [ ] Commit:
```bash
git add frontend/components/chat/WorkflowSelector.tsx
git commit -m "feat(workflow): add WorkflowSelector panel with save/edit/delete/run"
```

---

### Task 6: Wire `workflow` mode into `SlashMenu`

**Files:**
- Modify: `frontend/components/chat/SlashMenu.tsx`

- [ ] Add `Network` to lucide-react imports, add `WorkflowDef` and `WorkflowSelector` imports.

- [ ] Add `onOpenBuilder` and `onRunWorkflow` to `Props` interface:
```typescript
interface Props {
  // ...existing...
  onOpenBuilder: (def: WorkflowDef | null) => void
  onRunWorkflow: (def: WorkflowDef) => void
}
```

- [ ] Add workflow to `MODES`:
```typescript
{ id: 'workflow', label: 'Workflow', icon: Network, desc: 'User-defined model DAG' },
```

- [ ] Keep SlashMenu open for workflow mode (match council pattern):
```typescript
onClick={() => { onMode(m.id); if (m.id !== 'council' && m.id !== 'workflow') onClose() }}
```

- [ ] Add workflow panel after relay section:
```tsx
{mode === 'workflow' && (
  <div className="border-t border-[#a89080]/20 p-3">
    <WorkflowSelector
      onRun={(def) => { onRunWorkflow(def); onClose() }}
      onEdit={(def) => { onOpenBuilder(def); onClose() }}
    />
  </div>
)}
```

- [ ] Update `ChatInput.tsx` to pass `onOpenBuilder` and `onRunWorkflow` through to `SlashMenu`. Add to `ChatInput` props interface and destructure. Pass to `SlashMenu`.

- [ ] Add `workflow` to `MODE_LABEL` in `ChatInput.tsx`:
```typescript
const MODE_LABEL: Record<Mode, string> = {
  oracle: 'Oracle', council: 'Council', relay: 'Relay', workflow: 'Workflow',
}
```

- [ ] Commit:
```bash
git add frontend/components/chat/SlashMenu.tsx frontend/components/chat/ChatInput.tsx
git commit -m "feat(workflow): add Workflow mode to SlashMenu with WorkflowSelector"
```

---

### Task 7: Wire `WorkflowBuilder` modal and workflow send path into `ChatWindow`

**Files:**
- Modify: `frontend/components/chat/ChatWindow.tsx`
- Modify: `frontend/lib/api.ts`

- [ ] In `frontend/lib/api.ts`, convert `workflow_def` → `workflow_nodes` before sending:

```typescript
// In buildQueryRequest, before building body:
if (req.workflow_def) {
  req = {
    ...req,
    workflow_nodes: req.workflow_def.nodes.map(n => ({
      id: n.id,
      type: 'model',
      model: n.model,
      role: n.role,
      inputs: n.dependsOn,
    })),
  }
}
```

- [ ] In `ChatWindow.tsx`, add imports:
```typescript
import { WorkflowDef } from '@/lib/types'
import { WorkflowBuilder } from './WorkflowBuilder'
import { saveWorkflow } from '@/lib/workflows'
```

- [ ] Add state:
```typescript
const [builderOpen, setBuilderOpen]       = useState(false)
const [builderInitial, setBuilderInitial] = useState<WorkflowDef | null>(null)
const [activeWorkflow, setActiveWorkflow] = useState<WorkflowDef | null>(null)
const workflowNodeIdsRef = useRef<Record<string, string>>({})  // node_id → msg id
```

- [ ] Add `const isWorkflow = mode === 'workflow'`.

- [ ] In `assistantTurn` initialization, add workflow case — reuse council Turn type with one message per node:
```typescript
} else if (isWorkflow) {
  const wfNodes = activeWorkflow?.nodes ?? []
  workflowNodeIdsRef.current = {}
  assistantTurn = {
    type: 'council',
    msgs: wfNodes.map(n => {
      const msgId = uuidv4()
      workflowNodeIdsRef.current[n.id] = msgId
      return { id: msgId, role: 'assistant' as const, content: '', model: n.model, isStreaming: true }
    }),
  }
}
```

- [ ] Add `workflow_node_done` SSE handler:
```typescript
workflow_node_done: (d) => {
  const msgId = workflowNodeIdsRef.current[d.node_id]
  if (!msgId) return
  setTurns(prev => prev.map(turn => {
    if (turn.type !== 'council') return turn
    return { ...turn, msgs: turn.msgs.map(m => m.id === msgId ? { ...m, isStreaming: false } : m) }
  }))
},
```

- [ ] Update `token` handler to include `isWorkflow` alongside `isCouncil`:
```typescript
token: (d) => {
  if (isCouncil || isWorkflow) { appendDeltaByHex(d.hex, d.delta) }
  ...
}
```

- [ ] Update `buildQueryRequest` call to pass `workflow_def`:
```typescript
workflow_def: isWorkflow ? (activeWorkflow ?? undefined) : undefined,
```

- [ ] Add `MODE_LABEL` workflow entry in `ChatWindow.tsx`:
```typescript
const MODE_LABEL: Record<Mode, string> = {
  oracle: 'Oracle', council: 'The Council', relay: 'The Relay', workflow: 'Workflow',
}
```

- [ ] Render `WorkflowBuilder` modal conditionally:
```tsx
{builderOpen && (
  <WorkflowBuilder
    initial={builderInitial ?? undefined}
    onClose={() => setBuilderOpen(false)}
    onSave={(def) => { saveWorkflow(def); setBuilderOpen(false) }}
    onRun={(def) => { saveWorkflow(def); setBuilderOpen(false); setActiveWorkflow(def); setMode('workflow') }}
  />
)}
```

- [ ] Pass `onOpenBuilder` and `onRunWorkflow` to `ChatInput`:
```tsx
<ChatInput
  onOpenBuilder={(def) => { setBuilderInitial(def); setBuilderOpen(true) }}
  onRunWorkflow={(def) => { setActiveWorkflow(def); setMode('workflow') }}
  ...
/>
```

- [ ] TypeScript check:
```bash
cd /Users/anas/Projects/hexallabs/frontend && bun run tsc --noEmit 2>&1 | head -30
```

- [ ] Commit:
```bash
git add frontend/components/chat/ChatWindow.tsx frontend/lib/api.ts
git commit -m "feat(workflow): wire WorkflowBuilder modal and workflow send path into ChatWindow"
```

---

### Task 8: End-to-end build verification

- [ ] Full backend tests:
```bash
cd /Users/anas/Projects/hexallabs/backend && uv run pytest tests/ -v --tb=short 2>&1 | tail -30
```
Expected: all passing

- [ ] Frontend build:
```bash
cd /Users/anas/Projects/hexallabs/frontend && bun run build 2>&1 | tail -10
```
Expected: compiled successfully

- [ ] Manual verification:
  1. Open `/chat`, press `/`, confirm "Workflow" appears in mode list
  2. Select Workflow → WorkflowSelector shows "No saved workflows. Create one."
  3. Click "New" → WorkflowBuilder modal opens
  4. Click Apex and Prism from palette → 2 nodes appear on canvas
  5. Set roles on each node
  6. Click Apex → click Prism → dashed arrow appears Apex→Prism
  7. Click "Save" → modal closes, selector shows saved workflow
  8. Click "Run" on saved workflow → mode set to Workflow
  9. Type query, hit Enter → CouncilGrid lights up per node
  10. Both nodes stream and mark done

---

### Implementation Notes

- **Reuse council Turn type for workflow:** Workflow nodes stream in parallel like council models, so `type: 'council'` Turn reuse is intentional — avoids a duplicate rendering path. The `workflowNodeIdsRef` maps `node_id → message_id` for `workflow_node_done` SSE routing.
- **No new graph library:** Canvas uses `position: absolute` + inline SVG `<path>` with cubic bezier curves. Sufficient for 2–7 nodes.
- **Edge deletion:** Clicking an existing SVG path calls `removeEdge(fromId, toId)` — removes `fromId` from `to.dependsOn`.
- **Cycle detection:** Backend `_topo_sort` returns `None` on cycle; emits `error` event and returns early.
- **MODELS export:** Requires `MODELS` constant to be exported from `frontend/lib/types.ts` — verify it exists or add it as `export const MODELS: ModelName[] = ['Apex', 'Swift', 'Prism', 'Depth', 'Atlas', 'Horizon', 'Pulse']`.
- **lucide-react `Network` icon:** Available in lucide-react ≥ 0.263.0. Verify version: `grep lucide frontend/package.json`.
