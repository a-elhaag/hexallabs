# Workflow Builder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a full-screen drag-and-drop node canvas overlay that lets users visually assemble a model pipeline, then run it with results streaming into the existing chat window.

**Architecture:** `WorkflowOverlay` is a full-screen modal mounted inside `ChatWindow`. It owns a `WorkflowCanvas` (SVG + draggable node cards), a `WorkflowToolbar` (palette + run), and a `WorkflowConfigPanel` (right-side config for selected node). All state lives in `WorkflowOverlay` as `nodes: WorkflowNode[]`. On Run, nodes are serialized via `frontend/lib/workflow.ts` and passed to the existing `send()` in `ChatWindow`. Results render via the existing `CouncilGrid` component.

**Tech Stack:** Next.js App Router, TypeScript strict, Tailwind CSS, React `useState`/`useRef`/`useCallback`, SVG for connections, no external drag library.

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `frontend/lib/workflow.ts` | **Create** | Types, topo-sort validation, serialize-for-backend |
| `frontend/components/workflow/WorkflowOverlay.tsx` | **Create** | Full-screen modal, open/close slide animation |
| `frontend/components/workflow/WorkflowToolbar.tsx` | **Create** | Top bar: palette buttons + Run + Close |
| `frontend/components/workflow/WorkflowCanvas.tsx` | **Create** | Canvas: node cards, drag-to-move, SVG connections |
| `frontend/components/workflow/WorkflowNode.tsx` | **Create** | Single node card with input/output ports |
| `frontend/components/workflow/WorkflowConfigPanel.tsx` | **Create** | Right-side config panel, slides in on node select |
| `frontend/components/chat/ChatWindow.tsx` | **Modify** | Add `workflowOpen` state, pass nodes to `send()`, show banner |
| `frontend/components/chat/SlashMenu.tsx` | **Modify** | Workflow entry calls `onWorkflowOpen()` instead of just `onMode` |
| `frontend/components/chat/ChatInput.tsx` | **Modify** | Hide Scout button when `mode === 'workflow'`, add `onQueryChange` |

---

### Task 1: Core types and utilities (`frontend/lib/workflow.ts`)

**Files:**
- Create: `frontend/lib/workflow.ts`

- [ ] **Step 1: Create the file with types and topo-sort**

```typescript
// frontend/lib/workflow.ts
import type { ModelName } from '@/lib/types'

export type WFNodeType = 'model' | 'prompt_template' | 'scout' | 'merge'

export interface WorkflowNode {
  id: string
  type: WFNodeType
  model?: ModelName
  systemPrompt?: string
  template?: string
  scoutMode?: 'auto' | 'force'
  separator?: string
  inputs: string[]
  // UI-only — stripped before sending to backend
  x: number
  y: number
}

/** Returns true if adding edge fromId→toId would create a cycle. */
export function wouldCreateCycle(
  nodes: WorkflowNode[],
  fromId: string,
  toId: string,
): boolean {
  // Build adjacency from existing inputs + proposed new edge
  const adj: Map<string, string[]> = new Map()
  for (const n of nodes) {
    adj.set(n.id, [...n.inputs])
  }
  // Add proposed edge: toId now has fromId as input
  adj.set(toId, [...(adj.get(toId) ?? []), fromId])

  // DFS from toId — if we can reach fromId, it's a cycle
  const visited = new Set<string>()
  function dfs(id: string): boolean {
    if (id === fromId) return true
    if (visited.has(id)) return false
    visited.add(id)
    for (const upstream of adj.get(id) ?? []) {
      if (dfs(upstream)) return true
    }
    return false
  }
  return dfs(toId)
}

/** Validate the node graph before running. Returns error string or null. */
export function validateGraph(nodes: WorkflowNode[]): string | null {
  if (nodes.length === 0) return 'Add at least one node'
  for (const n of nodes) {
    if (n.type === 'model' && !n.model) return `Node "${n.id}" has no model selected`
  }
  return null
}

/** Strip UI-only fields and format for QueryRequest.workflow_nodes */
export function serializeNodes(nodes: WorkflowNode[]): Record<string, unknown>[] {
  return nodes.map(n => {
    const base: Record<string, unknown> = { id: n.id, type: n.type, inputs: n.inputs }
    if (n.type === 'model') {
      base.model = n.model
      if (n.systemPrompt) base.system_prompt = n.systemPrompt
    }
    if (n.type === 'prompt_template') base.template = n.template ?? ''
    if (n.type === 'scout') base.scout_mode = n.scoutMode ?? 'auto'
    if (n.type === 'merge') base.separator = n.separator ?? '\n\n---\n\n'
    return base
  })
}

/** Generate a unique node id */
export function newNodeId(nodes: WorkflowNode[]): string {
  return `node_${nodes.length}_${Math.random().toString(36).slice(2, 6)}`
}

/** Node border/accent color by type */
export const NODE_COLOR: Record<WFNodeType, string> = {
  model:           '#6290c3',
  prompt_template: '#a89080',
  scout:           '#2c8c4a',
  merge:           '#c36290',
}

/** Node type display label */
export const NODE_LABEL: Record<WFNodeType, string> = {
  model:           'Model',
  prompt_template: 'Prompt',
  scout:           'Scout',
  merge:           'Merge',
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && bun run tsc --noEmit 2>&1
```
Expected: no output (no errors).

- [ ] **Step 3: Commit**

```bash
git add frontend/lib/workflow.ts
git commit -m "feat(workflow): add types, validation, serialization utilities"
```

---

### Task 2: `WorkflowNode` card component

**Files:**
- Create: `frontend/components/workflow/WorkflowNode.tsx`

- [ ] **Step 1: Create the component**

```tsx
// frontend/components/workflow/WorkflowNode.tsx
'use client'
import { useRef, useEffect } from 'react'
import { WorkflowNode as WFNode, NODE_COLOR, NODE_LABEL } from '@/lib/workflow'

interface Props {
  node: WFNode
  selected: boolean
  onSelect: (id: string) => void
  onDelete: (id: string) => void
  onDragEnd: (id: string, x: number, y: number) => void
  onPortMouseDown: (e: React.MouseEvent, nodeId: string, port: 'in' | 'out') => void
  onPortMouseUp: (e: React.MouseEvent, nodeId: string, port: 'in' | 'out') => void
}

export function WorkflowNodeCard({
  node, selected, onSelect, onDelete, onDragEnd, onPortMouseDown, onPortMouseUp,
}: Props) {
  const color = NODE_COLOR[node.type]
  const dragStart = useRef<{ mx: number; my: number; nx: number; ny: number } | null>(null)
  const divRef = useRef<HTMLDivElement>(null)

  // Animate in on mount
  useEffect(() => {
    const el = divRef.current
    if (!el) return
    el.style.transition = 'none'
    el.style.transform = 'scale(0.85)'
    el.style.opacity = '0'
    requestAnimationFrame(() => {
      el.style.transition = 'transform 200ms cubic-bezier(0.16,1,0.3,1), opacity 200ms ease'
      el.style.transform = 'scale(1)'
      el.style.opacity = '1'
    })
  }, [])

  function onMouseDown(e: React.MouseEvent) {
    // Don't drag when clicking ports or delete button
    if ((e.target as HTMLElement).dataset.port || (e.target as HTMLElement).dataset.del) return
    e.preventDefault()
    dragStart.current = { mx: e.clientX, my: e.clientY, nx: node.x, ny: node.y }
    onSelect(node.id)

    function onMove(ev: MouseEvent) {
      if (!dragStart.current) return
      const dx = ev.clientX - dragStart.current.mx
      const dy = ev.clientY - dragStart.current.my
      onDragEnd(node.id, dragStart.current.nx + dx, dragStart.current.ny + dy)
    }
    function onUp(ev: MouseEvent) {
      if (!dragStart.current) return
      const dx = ev.clientX - dragStart.current.mx
      const dy = ev.clientY - dragStart.current.my
      onDragEnd(node.id, dragStart.current.nx + dx, dragStart.current.ny + dy)
      dragStart.current = null
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup', onUp)
    }
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
  }

  const label = node.type === 'model'
    ? (node.model ?? 'No model')
    : node.type === 'prompt_template'
      ? (node.template
          ? node.template.slice(0, 22) + (node.template.length > 22 ? '…' : '')
          : 'Empty prompt')
      : node.type === 'scout'
        ? `Scout · ${node.scoutMode ?? 'auto'}`
        : 'Merge'

  return (
    <div
      ref={divRef}
      onMouseDown={onMouseDown}
      style={{
        position: 'absolute',
        left: node.x,
        top: node.y,
        borderColor: color,
        boxShadow: selected
          ? `0 0 0 3px ${color}40, 0 4px 16px rgba(0,0,0,0.12)`
          : '0 2px 10px rgba(0,0,0,0.08)',
        minWidth: 140,
        zIndex: selected ? 15 : 12,
      }}
      className="bg-white border-[1.5px] rounded-2xl p-3 cursor-grab active:cursor-grabbing select-none"
    >
      {/* Delete button */}
      <button
        data-del="1"
        onClick={e => { e.stopPropagation(); onDelete(node.id) }}
        className="absolute top-1.5 right-2 text-warm-gray hover:text-red-500 text-xs transition-opacity"
        style={{ opacity: selected ? 1 : 0 }}
        onMouseOver={e => (e.currentTarget.style.opacity = '1')}
        onMouseOut={e => (e.currentTarget.style.opacity = selected ? '1' : '0')}
      >✕</button>

      <p className="text-[9px] font-black uppercase tracking-widest mb-1" style={{ color }}>
        {NODE_LABEL[node.type]}
      </p>
      <p className="text-[13px] font-bold text-[#2c2c2c] leading-tight">{label}</p>

      {/* Ports row */}
      <div className="flex items-center justify-between mt-2.5">
        {/* Input port */}
        <div className="flex items-center gap-1">
          <div
            data-port="in"
            onMouseDown={e => { e.stopPropagation(); onPortMouseDown(e, node.id, 'in') }}
            onMouseUp={e => { e.stopPropagation(); onPortMouseUp(e, node.id, 'in') }}
            className="w-2.5 h-2.5 rounded-full border-2 bg-white cursor-crosshair hover:scale-150 transition-transform"
            style={{ borderColor: '#a89080' }}
          />
          <span className="text-[9px] text-warm-gray font-semibold">in</span>
        </div>
        {/* Output port */}
        <div className="flex items-center gap-1">
          <span className="text-[9px] text-warm-gray font-semibold">out</span>
          <div
            data-port="out"
            onMouseDown={e => { e.stopPropagation(); onPortMouseDown(e, node.id, 'out') }}
            onMouseUp={e => { e.stopPropagation(); onPortMouseUp(e, node.id, 'out') }}
            className="w-2.5 h-2.5 rounded-full cursor-crosshair hover:scale-150 transition-transform"
            style={{ background: color, border: `2px solid ${color}` }}
          />
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Verify TypeScript**

```bash
cd frontend && bun run tsc --noEmit 2>&1
```
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/components/workflow/WorkflowNode.tsx
git commit -m "feat(workflow): add WorkflowNodeCard component"
```

---

### Task 3: `WorkflowConfigPanel` component

**Files:**
- Create: `frontend/components/workflow/WorkflowConfigPanel.tsx`

- [ ] **Step 1: Create the component**

```tsx
// frontend/components/workflow/WorkflowConfigPanel.tsx
'use client'
import { WorkflowNode, NODE_LABEL, NODE_COLOR } from '@/lib/workflow'
import { MODELS } from '@/lib/types'

interface Props {
  node: WorkflowNode
  allNodes: WorkflowNode[]
  onChange: (updated: WorkflowNode) => void
  onClose: () => void
}

export function WorkflowConfigPanel({ node, allNodes, onChange, onClose }: Props) {
  const color = NODE_COLOR[node.type]
  const inputNodes = allNodes.filter(n => node.inputs.includes(n.id))

  return (
    <div
      className="absolute right-4 top-4 w-56 bg-white border border-warm-gray/20 rounded-2xl p-4 shadow-xl"
      style={{ zIndex: 20, animation: 'configIn 220ms cubic-bezier(0.16,1,0.3,1) both' }}
    >
      <style>{`@keyframes configIn { from { opacity:0; transform:translateX(24px) } to { opacity:1; transform:translateX(0) } }`}</style>

      <div className="flex items-center justify-between mb-3">
        <p className="text-[10px] font-black uppercase tracking-widest" style={{ color }}>
          {NODE_LABEL[node.type]}
        </p>
        <button onClick={onClose} className="text-warm-gray hover:text-[#2c2c2c] text-xs leading-none">✕</button>
      </div>

      {node.type === 'model' && (
        <>
          <div className="mb-3">
            <p className="text-[10px] font-bold text-warm-gray uppercase tracking-wide mb-1">Model</p>
            <select
              value={node.model ?? ''}
              onChange={e => onChange({ ...node, model: e.target.value as typeof MODELS[number] })}
              className="w-full px-2 py-1.5 border border-warm-gray/30 rounded-lg text-xs font-semibold text-[#2c2c2c] bg-[#f5f1ed] focus:outline-none focus:border-denim"
            >
              <option value="" disabled>Select model…</option>
              {MODELS.map(m => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>
          <div className="mb-3">
            <p className="text-[10px] font-bold text-warm-gray uppercase tracking-wide mb-1">System prompt</p>
            <textarea
              value={node.systemPrompt ?? ''}
              onChange={e => onChange({ ...node, systemPrompt: e.target.value })}
              placeholder="Optional override…"
              rows={3}
              className="w-full px-2 py-1.5 border border-warm-gray/30 rounded-lg text-[11px] text-[#2c2c2c] bg-[#f5f1ed] resize-none focus:outline-none focus:border-warm-gray"
            />
          </div>
        </>
      )}

      {node.type === 'prompt_template' && (
        <div className="mb-3">
          <p className="text-[10px] font-bold text-warm-gray uppercase tracking-wide mb-1">Template text</p>
          <textarea
            value={node.template ?? ''}
            onChange={e => onChange({ ...node, template: e.target.value })}
            placeholder="System context injected before downstream node…"
            rows={5}
            className="w-full px-2 py-1.5 border border-warm-gray/30 rounded-lg text-[11px] text-[#2c2c2c] bg-[#f5f1ed] resize-none focus:outline-none focus:border-warm-gray"
          />
        </div>
      )}

      {node.type === 'scout' && (
        <div className="mb-3">
          <p className="text-[10px] font-bold text-warm-gray uppercase tracking-wide mb-1">Mode</p>
          {(['auto', 'force'] as const).map(m => (
            <label key={m} className="flex items-center gap-2 mb-1.5 cursor-pointer">
              <input
                type="radio"
                name={`scoutMode-${node.id}`}
                value={m}
                checked={(node.scoutMode ?? 'auto') === m}
                onChange={() => onChange({ ...node, scoutMode: m })}
                className="accent-denim"
              />
              <span className="text-xs font-semibold text-[#2c2c2c] capitalize">{m}</span>
            </label>
          ))}
        </div>
      )}

      {node.type === 'merge' && (
        <div className="mb-3">
          <p className="text-[10px] font-bold text-warm-gray uppercase tracking-wide mb-1">Separator</p>
          <input
            value={node.separator ?? '\n\n---\n\n'}
            onChange={e => onChange({ ...node, separator: e.target.value })}
            className="w-full px-2 py-1.5 border border-warm-gray/30 rounded-lg text-[11px] font-mono text-[#2c2c2c] bg-[#f5f1ed] focus:outline-none focus:border-warm-gray"
          />
        </div>
      )}

      {inputNodes.length > 0 && (
        <div>
          <p className="text-[10px] font-bold text-warm-gray uppercase tracking-wide mb-1">Inputs</p>
          <div className="flex flex-wrap gap-1">
            {inputNodes.map(n => (
              <span key={n.id} className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#2c2c2c]/8 text-warm-gray">
                ← {n.type === 'model' ? (n.model ?? n.id) : NODE_LABEL[n.type]}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Verify TypeScript**

```bash
cd frontend && bun run tsc --noEmit 2>&1
```
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/components/workflow/WorkflowConfigPanel.tsx
git commit -m "feat(workflow): add WorkflowConfigPanel component"
```

---

### Task 4: `WorkflowToolbar` component

**Files:**
- Create: `frontend/components/workflow/WorkflowToolbar.tsx`

- [ ] **Step 1: Create the component**

```tsx
// frontend/components/workflow/WorkflowToolbar.tsx
'use client'
import { WFNodeType, NODE_COLOR, NODE_LABEL } from '@/lib/workflow'

const PALETTE: WFNodeType[] = ['model', 'prompt_template', 'scout', 'merge']

interface Props {
  onAddNode: (type: WFNodeType) => void
  onRun: () => void
  onClose: () => void
  validationError: string | null
  nodeCount: number
}

export function WorkflowToolbar({ onAddNode, onRun, onClose, validationError, nodeCount }: Props) {
  const canRun = !validationError && nodeCount > 0

  return (
    <div className="h-12 flex items-center gap-3 px-4 bg-[#f5f1ed] border-b border-warm-gray/20 shrink-0">
      <span className="font-black text-sm text-[#2c2c2c] tracking-tight">Workflow</span>
      <div className="w-px h-5 bg-warm-gray/20" />

      <div className="flex gap-1.5">
        {PALETTE.map(type => (
          <button
            key={type}
            onClick={() => onAddNode(type)}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-[11px] font-bold transition-all hover:-translate-y-0.5 hover:shadow-md active:scale-95"
            style={{
              borderColor: NODE_COLOR[type],
              color: NODE_COLOR[type],
              background: `${NODE_COLOR[type]}12`,
            }}
          >
            <span className="w-1.5 h-1.5 rounded-full" style={{ background: NODE_COLOR[type] }} />
            + {NODE_LABEL[type]}
          </button>
        ))}
      </div>

      <div className="flex-1" />

      {validationError && (
        <span className="text-[11px] text-red-500 font-semibold">{validationError}</span>
      )}

      <button
        onClick={onRun}
        disabled={!canRun}
        className={`flex items-center gap-1.5 px-4 py-1.5 rounded-xl text-sm font-black transition-all active:scale-[0.97] ${
          canRun
            ? 'bg-[#2c2c2c] text-[#f5f1ed] hover:bg-denim cursor-pointer'
            : 'bg-[#2c2c2c]/15 text-warm-gray cursor-not-allowed'
        }`}
      >
        ▶ Run
      </button>

      <div className="w-px h-5 bg-warm-gray/20" />

      <button
        onClick={onClose}
        className="text-warm-gray hover:text-[#2c2c2c] text-lg leading-none transition-colors"
        aria-label="Close workflow builder"
      >✕</button>
    </div>
  )
}
```

- [ ] **Step 2: Verify TypeScript**

```bash
cd frontend && bun run tsc --noEmit 2>&1
```
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/components/workflow/WorkflowToolbar.tsx
git commit -m "feat(workflow): add WorkflowToolbar component"
```

---

### Task 5: `WorkflowCanvas` component

**Files:**
- Create: `frontend/components/workflow/WorkflowCanvas.tsx`

- [ ] **Step 1: Create the component**

```tsx
// frontend/components/workflow/WorkflowCanvas.tsx
'use client'
import { useRef, useState, useCallback } from 'react'
import { WorkflowNode, NODE_COLOR, wouldCreateCycle } from '@/lib/workflow'
import { WorkflowNodeCard } from './WorkflowNode'
import { WorkflowConfigPanel } from './WorkflowConfigPanel'

interface Props {
  nodes: WorkflowNode[]
  onChange: (nodes: WorkflowNode[]) => void
  selectedId: string | null
  onSelect: (id: string | null) => void
}

interface DragConn {
  fromId: string
  x1: number; y1: number
  x2: number; y2: number
}

// Approximate node dimensions for port position calculation
const NODE_W = 140
const NODE_H = 80

function portPos(node: WorkflowNode, port: 'in' | 'out') {
  return {
    x: port === 'in' ? node.x : node.x + NODE_W,
    y: node.y + NODE_H / 2,
  }
}

function bezier(x1: number, y1: number, x2: number, y2: number) {
  const cx = (x1 + x2) / 2
  return `M ${x1} ${y1} C ${cx} ${y1} ${cx} ${y2} ${x2} ${y2}`
}

export function WorkflowCanvas({ nodes, onChange, selectedId, onSelect }: Props) {
  const canvasRef = useRef<HTMLDivElement>(null)
  const [dragConn, setDragConn] = useState<DragConn | null>(null)
  const [hoveredConn, setHoveredConn] = useState<string | null>(null)

  const selectedNode = nodes.find(n => n.id === selectedId) ?? null

  const connections = nodes.flatMap(n => n.inputs.map(inputId => ({ fromId: inputId, toId: n.id })))

  function updateNode(updated: WorkflowNode) {
    onChange(nodes.map(n => n.id === updated.id ? updated : n))
  }

  function deleteNode(id: string) {
    onChange(
      nodes
        .filter(n => n.id !== id)
        .map(n => ({ ...n, inputs: n.inputs.filter(i => i !== id) }))
    )
    if (selectedId === id) onSelect(null)
  }

  function moveNode(id: string, x: number, y: number) {
    onChange(nodes.map(n => n.id === id ? { ...n, x: Math.max(0, x), y: Math.max(0, y) } : n))
  }

  function deleteConnection(fromId: string, toId: string) {
    onChange(nodes.map(n => n.id === toId ? { ...n, inputs: n.inputs.filter(i => i !== fromId) } : n))
    setHoveredConn(null)
  }

  const onPortMouseDown = useCallback((e: React.MouseEvent, nodeId: string, port: 'in' | 'out') => {
    if (port !== 'out') return
    e.preventDefault()
    const canvas = canvasRef.current
    if (!canvas) return
    const rect = canvas.getBoundingClientRect()
    const node = nodes.find(n => n.id === nodeId)
    if (!node) return
    const p = portPos(node, 'out')

    function onMove(ev: MouseEvent) {
      setDragConn({ fromId: nodeId, x1: p.x, y1: p.y, x2: ev.clientX - rect.left, y2: ev.clientY - rect.top })
    }
    function onUp() {
      setDragConn(null)
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup', onUp)
    }
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
  }, [nodes])

  const onPortMouseUp = useCallback((e: React.MouseEvent, nodeId: string, port: 'in' | 'out') => {
    if (port !== 'in' || !dragConn) return
    e.preventDefault()
    const { fromId } = dragConn
    const toId = nodeId
    if (fromId === toId || wouldCreateCycle(nodes, fromId, toId)) { setDragConn(null); return }
    // Append fromId to toId's inputs if not already present
    onChange(nodes.map(n => n.id === toId && !n.inputs.includes(fromId) ? { ...n, inputs: [...n.inputs, fromId] } : n))
    setDragConn(null)
  }, [dragConn, nodes, onChange])

  return (
    <div
      ref={canvasRef}
      className="flex-1 relative overflow-auto"
      style={{
        background: '#f5f1ed',
        backgroundImage: 'radial-gradient(circle, #a8908028 1px, transparent 1px)',
        backgroundSize: '22px 22px',
        minHeight: 0,
      }}
      onClick={e => { if (e.target === canvasRef.current) onSelect(null) }}
    >
      {/* SVG layer */}
      <svg className="absolute inset-0 w-full h-full" style={{ pointerEvents: 'none', zIndex: 10 }}>
        <defs>
          {(['model', 'prompt_template', 'scout', 'merge'] as const).map(type => (
            <marker key={type} id={`arr-${type}`} markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
              <path d="M0,0 L0,6 L8,3 z" fill={NODE_COLOR[type]} />
            </marker>
          ))}
          <marker id="arr-delete" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L0,6 L8,3 z" fill="#ef4444" />
          </marker>
          <marker id="arr-drag" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L0,6 L8,3 z" fill="#a89080" />
          </marker>
        </defs>

        {connections.map(({ fromId, toId }) => {
          const fn = nodes.find(n => n.id === fromId)
          const tn = nodes.find(n => n.id === toId)
          if (!fn || !tn) return null
          const p1 = portPos(fn, 'out')
          const p2 = portPos(tn, 'in')
          const key = `${fromId}->${toId}`
          const hovered = hoveredConn === key
          const midX = (p1.x + p2.x) / 2
          const midY = (p1.y + p2.y) / 2
          return (
            <g key={key} style={{ pointerEvents: 'all' }}>
              {/* Wide invisible hit area */}
              <path
                d={bezier(p1.x, p1.y, p2.x, p2.y)}
                stroke="transparent" strokeWidth="16" fill="none"
                style={{ cursor: 'pointer' }}
                onMouseEnter={() => setHoveredConn(key)}
                onMouseLeave={() => setHoveredConn(null)}
                onClick={() => deleteConnection(fromId, toId)}
              />
              {/* Visible connection */}
              <path
                d={bezier(p1.x, p1.y, p2.x, p2.y)}
                stroke={hovered ? '#ef4444' : NODE_COLOR[fn.type]}
                strokeWidth={hovered ? 2.5 : 2}
                fill="none"
                markerEnd={`url(#arr-${hovered ? 'delete' : fn.type})`}
                style={{ pointerEvents: 'none' }}
              />
              {hovered && (
                <text x={midX} y={midY - 6} textAnchor="middle" fontSize="11" fill="#ef4444" fontWeight="bold" style={{ pointerEvents: 'none' }}>✕</text>
              )}
            </g>
          )
        })}

        {/* In-progress drag line */}
        {dragConn && (
          <path
            d={bezier(dragConn.x1, dragConn.y1, dragConn.x2, dragConn.y2)}
            stroke="#a89080" strokeWidth="2" strokeDasharray="6 3" fill="none"
            markerEnd="url(#arr-drag)"
            style={{ pointerEvents: 'none' }}
          />
        )}
      </svg>

      {/* Empty state */}
      {nodes.length === 0 && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 pointer-events-none opacity-40">
          <p className="text-3xl">⬡</p>
          <p className="text-sm font-bold text-warm-gray">Add nodes from the toolbar</p>
          <p className="text-xs text-warm-gray">Drag output → input port to connect</p>
        </div>
      )}

      {/* Node cards */}
      {nodes.map(node => (
        <WorkflowNodeCard
          key={node.id}
          node={node}
          selected={selectedId === node.id}
          onSelect={onSelect}
          onDelete={deleteNode}
          onDragEnd={moveNode}
          onPortMouseDown={onPortMouseDown}
          onPortMouseUp={onPortMouseUp}
        />
      ))}

      {/* Config panel */}
      {selectedNode && (
        <WorkflowConfigPanel
          node={selectedNode}
          allNodes={nodes}
          onChange={updateNode}
          onClose={() => onSelect(null)}
        />
      )}
    </div>
  )
}
```

- [ ] **Step 2: Verify TypeScript**

```bash
cd frontend && bun run tsc --noEmit 2>&1
```
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/components/workflow/WorkflowCanvas.tsx
git commit -m "feat(workflow): add WorkflowCanvas with drag-connect and SVG connections"
```

---

### Task 6: `WorkflowOverlay` component

**Files:**
- Create: `frontend/components/workflow/WorkflowOverlay.tsx`

- [ ] **Step 1: Create the component**

```tsx
// frontend/components/workflow/WorkflowOverlay.tsx
'use client'
import { useState, useEffect } from 'react'
import { WorkflowNode, WFNodeType, newNodeId, validateGraph, serializeNodes } from '@/lib/workflow'
import { WorkflowToolbar } from './WorkflowToolbar'
import { WorkflowCanvas } from './WorkflowCanvas'

interface Props {
  open: boolean
  onClose: () => void
  onRun: (nodes: Record<string, unknown>[]) => void
}

const STAGGER_POSITIONS = [
  { x: 80,  y: 120 },
  { x: 300, y: 120 },
  { x: 520, y: 120 },
  { x: 740, y: 120 },
]

export function WorkflowOverlay({ open, onClose, onRun }: Props) {
  const [nodes, setNodes] = useState<WorkflowNode[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [mounted, setMounted] = useState(false)
  const [closing, setClosing] = useState(false)

  useEffect(() => {
    if (open) {
      setMounted(true)
      setClosing(false)
    } else if (mounted) {
      setClosing(true)
      const t = setTimeout(() => { setMounted(false); setClosing(false) }, 320)
      return () => clearTimeout(t)
    }
  }, [open]) // eslint-disable-line react-hooks/exhaustive-deps

  if (!mounted) return null

  function addNode(type: WFNodeType) {
    const pos = STAGGER_POSITIONS[nodes.length % STAGGER_POSITIONS.length]
    const wave = Math.floor(nodes.length / STAGGER_POSITIONS.length) * 40
    const newNode: WorkflowNode = {
      id: newNodeId(nodes),
      type,
      inputs: [],
      x: pos.x + wave,
      y: pos.y + wave,
      ...(type === 'scout'           ? { scoutMode: 'auto' as const }      : {}),
      ...(type === 'merge'           ? { separator: '\n\n---\n\n' }        : {}),
      ...(type === 'prompt_template' ? { template: '' }                    : {}),
    }
    setNodes(prev => [...prev, newNode])
  }

  const validationError = validateGraph(nodes)

  function handleRun() {
    if (validationError) return
    onRun(serializeNodes(nodes))
  }

  function handleClose() {
    setClosing(true)
    setTimeout(onClose, 320)
  }

  const connectionCount = nodes.reduce((acc, n) => acc + n.inputs.length, 0)

  return (
    <div
      className="fixed inset-0 z-50 flex flex-col"
      style={{
        animation: closing
          ? 'wfOut 280ms cubic-bezier(0.16,1,0.3,1) both'
          : 'wfIn 300ms cubic-bezier(0.16,1,0.3,1) both',
      }}
    >
      <style>{`
        @keyframes wfIn  { from { transform:translateY(100%); opacity:0 } to { transform:translateY(0); opacity:1 } }
        @keyframes wfOut { from { transform:translateY(0);    opacity:1 } to { transform:translateY(100%); opacity:0 } }
      `}</style>

      <WorkflowToolbar
        onAddNode={addNode}
        onRun={handleRun}
        onClose={handleClose}
        validationError={validationError}
        nodeCount={nodes.length}
      />

      <WorkflowCanvas
        nodes={nodes}
        onChange={setNodes}
        selectedId={selectedId}
        onSelect={setSelectedId}
      />

      {/* Footer */}
      <div className="h-8 flex items-center px-4 gap-2 bg-[#f5f1ed] border-t border-warm-gray/20 text-[11px] text-warm-gray font-semibold shrink-0">
        <span
          className="w-1.5 h-1.5 rounded-full shrink-0"
          style={{ background: validationError ? '#ef4444' : '#2c8c4a' }}
        />
        {nodes.length} node{nodes.length !== 1 ? 's' : ''}
        {' · '}
        {connectionCount} connection{connectionCount !== 1 ? 's' : ''}
        {' · '}
        {validationError ?? 'ready'}
        <span className="ml-auto opacity-50 hidden sm:block">
          Drag out-port → in-port to connect · Hover connection to delete · Click node to configure
        </span>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Verify TypeScript**

```bash
cd frontend && bun run tsc --noEmit 2>&1
```
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/components/workflow/WorkflowOverlay.tsx
git commit -m "feat(workflow): add WorkflowOverlay with slide animation, toolbar, footer"
```

---

### Task 7: Wire `ChatWindow`

**Files:**
- Modify: `frontend/components/chat/ChatWindow.tsx`

- [ ] **Step 1: Add imports and state**

Add at the top of `ChatWindow.tsx` after existing imports:
```typescript
import { WorkflowOverlay } from '../workflow/WorkflowOverlay'
```

Inside `ChatWindow()`, after the existing `useState` declarations, add:
```typescript
const [workflowOpen, setWorkflowOpen]   = useState(false)
const pendingQueryRef                    = useRef<string>('')
```

- [ ] **Step 2: Update `send()` signature to accept serialized workflow nodes**

Change:
```typescript
async function send(query: string) {
```
To:
```typescript
async function send(query: string, wfNodes?: Record<string, unknown>[]) {
```

Find the auto-chain block in `send()`:
```typescript
// Workflow: build nodes from selected models (or default Swift→Apex chain)
const workflowModels = effectiveModels.length >= 2
  ? effectiveModels
  : ['Swift', 'Apex'] as ModelName[]
const workflowNodes = isWorkflow
  ? workflowModels.map((m, i) => ({
      id: `node_${i}`,
      type: 'model',
      model: m,
      inputs: i === 0 ? [] : [`node_${i - 1}`],
    }))
  : undefined
```

Replace with:
```typescript
// Workflow: nodes come from the visual builder passed into send()
const workflowNodes = isWorkflow ? (wfNodes ?? []) : undefined
```

Also update the `buildQueryRequest` call — find `workflow_nodes: workflowNodes` and confirm it's already there (it should be from the earlier session). If it's missing, add it:
```typescript
workflow_nodes: workflowNodes,
```

- [ ] **Step 3: Add `handleWorkflowRun`**

Inside `ChatWindow()`, add after `stopGeneration`:
```typescript
function handleWorkflowRun(serialized: Record<string, unknown>[]) {
  setWorkflowOpen(false)
  setTimeout(() => {
    send(pendingQueryRef.current || 'Run workflow', serialized)
  }, 320)
}
```

- [ ] **Step 4: Update the empty-state JSX**

Find the empty-state div (the one with "Ask anything") and replace it with:
```tsx
<div className={`absolute inset-0 flex flex-col items-center justify-center gap-4 text-center px-6 ${hasSent || loadingSession ? 'hidden' : ''}`}>
  <div className="w-12 h-12 bg-[#2c2c2c] rounded-3xl flex items-center justify-center shadow-lg pointer-events-none">
    <span className="text-cream font-black text-lg">H</span>
  </div>
  {mode === 'workflow' ? (
    <div className="flex flex-col gap-2 items-center">
      <p className="font-black text-xl text-[#2c2c2c] pointer-events-none">No pipeline yet</p>
      <button
        onClick={() => setWorkflowOpen(true)}
        className="px-5 py-2 bg-[#2c2c2c] text-cream rounded-xl font-bold text-sm hover:bg-denim transition-colors active:scale-95"
      >
        Build pipeline →
      </button>
    </div>
  ) : (
    <div className="flex flex-col gap-1 pointer-events-none">
      <p className="font-black text-xl text-[#2c2c2c]">Ask anything</p>
      <p className="text-sm text-warm-gray">Press <kbd className="px-1.5 py-0.5 bg-[#2c2c2c]/8 rounded-md text-xs font-mono">/</kbd> to switch modes</p>
    </div>
  )}
</div>
```

- [ ] **Step 5: Mount the overlay and update ChatInput**

Add just before the closing `</div>` of the root element:
```tsx
<WorkflowOverlay
  open={workflowOpen}
  onClose={() => setWorkflowOpen(false)}
  onRun={handleWorkflowRun}
/>
```

Update `<ChatInput>` to add two new props:
```tsx
onWorkflowOpen={() => setWorkflowOpen(true)}
onQueryChange={(q: string) => { pendingQueryRef.current = q }}
```

- [ ] **Step 6: Verify TypeScript**

```bash
cd frontend && bun run tsc --noEmit 2>&1
```
Expected: likely errors about `onWorkflowOpen` and `onQueryChange` not existing on ChatInput Props yet — fix in next task.

- [ ] **Step 7: Commit**

```bash
git add frontend/components/chat/ChatWindow.tsx
git commit -m "feat(workflow): wire WorkflowOverlay into ChatWindow"
```

---

### Task 8: Update `ChatInput` and `SlashMenu`

**Files:**
- Modify: `frontend/components/chat/ChatInput.tsx`
- Modify: `frontend/components/chat/SlashMenu.tsx`

- [ ] **Step 1: Update `ChatInput` Props and implementation**

In `ChatInput.tsx`, add to the `Props` interface:
```typescript
onWorkflowOpen?: () => void
onQueryChange?: (q: string) => void
```

Add both to the function destructuring:
```typescript
export function ChatInput({ onSend, onStop, streaming, mode, onMode, models, onModels, primal, onPrimal, scout, onScout, onWorkflowOpen, onQueryChange }: Props) {
```

Update the textarea `onChange` to call `onQueryChange`:
```tsx
onChange={e => { setValue(e.target.value); onQueryChange?.(e.target.value) }}
```

Wrap the Scout Globe button in a conditional so it hides in workflow mode:
```tsx
{mode !== 'workflow' && (
  <button
    onClick={() => {
      const next: ScoutMode = scout === 'off' ? 'auto' : scout === 'auto' ? 'force' : 'off'
      onScout(next)
    }}
    title={scout === 'auto' ? 'Scout · Auto (click for Force)' : scout === 'force' ? 'Scout · Force (click to disable)' : 'Enable Scout web search'}
    className={`shrink-0 w-7 h-7 flex items-center justify-center rounded-full transition-colors mb-0.5 ${
      scout === 'force'
        ? 'bg-denim text-white'
        : scout === 'auto'
          ? 'text-denim bg-denim/12 hover:bg-denim/20'
          : 'text-warm-gray hover:text-[#2c2c2c] hover:bg-[#2c2c2c]/6'
    }`}
    aria-label="Toggle Scout web search"
  >
    <Globe size={15} />
  </button>
)}
```

Pass `onWorkflowOpen` to `SlashMenu`:
```tsx
<SlashMenu
  onClose={() => setSlashOpen(false)}
  mode={mode}
  onMode={onMode}
  models={models}
  onModels={onModels}
  primal={primal}
  onPrimal={onPrimal}
  onWorkflowOpen={onWorkflowOpen}
/>
```

- [ ] **Step 2: Update `SlashMenu` Props and Workflow entry**

In `SlashMenu.tsx`, add to Props interface:
```typescript
onWorkflowOpen?: () => void
```

Add to function destructuring:
```typescript
export function SlashMenu({ onClose, mode, onMode, models, onModels, primal, onPrimal, onWorkflowOpen }: Props) {
```

Update the MODES map `onClick` for Workflow:
```tsx
onClick={() => {
  onMode(m.id)
  if (m.id === 'workflow') {
    onWorkflowOpen?.()
    onClose()
  } else if (m.id !== 'council') {
    onClose()
  }
}}
```

- [ ] **Step 3: Verify TypeScript (full clean)**

```bash
cd frontend && bun run tsc --noEmit 2>&1
```
Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/components/chat/ChatInput.tsx frontend/components/chat/SlashMenu.tsx
git commit -m "feat(workflow): hide scout button in workflow mode, wire slash menu to open overlay"
```

---

### Task 9: Manual smoke test

- [ ] **Step 1: Start dev servers**

```bash
# Terminal 1 — backend
cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — frontend
cd frontend && bun dev
```

- [ ] **Step 2: Golden path test**

1. Open `http://localhost:3000` and sign in
2. Press `/` → select **Workflow** — overlay should slide up from bottom
3. Click **+ Model** → card appears at position 1, animates in
4. Click **+ Model** again → second card at position 2
5. Click card 1 → config panel slides in from right → select "Swift" from dropdown
6. Click card 2 → config panel → select "Apex"
7. Drag card 2's output port → card 1's input port — nothing (would be cycle). Drag card 1's output → card 2's input → denim bezier line appears with arrowhead
8. Hover the connection line → turns red with ✕ at midpoint → click → line disappears
9. Re-create the Swift → Apex connection
10. Type "Explain quantum entanglement" in the chat input (overlay is still open — typing should work)
11. Click **Run ▶** → overlay slides down → CouncilGrid appears with 2 cards streaming

- [ ] **Step 3: Validation tests**

1. Open overlay, don't add nodes → Run is disabled, footer says "Add at least one node"
2. Add a Model node, don't select a model → footer says `Node "node_0_xxxx" has no model selected`, Run disabled
3. Try to create A→B→A cycle: add A, add B, connect A→B, then try B→A → second connection silently rejected (no line, no error)

- [ ] **Step 4: Node type tests**

1. Add **+ Prompt** node → config panel shows template textarea
2. Add **+ Scout** node → config panel shows auto/force radio
3. Add **+ Merge** node → config panel shows separator input
4. Connect Prompt → Model → run and verify backend doesn't 422 (check network tab — POST /api/query should return 200)

- [ ] **Step 5: Commit any fixes**

```bash
git add -p
git commit -m "fix(workflow): address smoke test issues"
```
