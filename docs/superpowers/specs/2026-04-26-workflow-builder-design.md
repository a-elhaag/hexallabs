# Workflow Builder — Design Spec
_2026-04-26_

## Overview

Full-screen overlay canvas that lets users visually build a node pipeline before running it. Appears when Workflow mode is active and the user clicks "Build pipeline" (or sends their first message). Nodes are wired by dragging output → input ports. On "Run", the overlay closes and results stream into the chat window using the existing CouncilGrid renderer.

---

## Layout

**Trigger:** User selects Workflow in the slash menu. An inline banner replaces the chat placeholder with "No pipeline yet — Build one" button. Clicking opens the overlay.

**Overlay structure (full-screen, z-50):**
```
┌─────────────────────────────────────────────────────────┐
│ TOOLBAR: title | + Model  + Prompt  + Scout  + Merge | [Run ▶] [✕] │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   CANVAS (cream, dot-grid background, scrollable)       │
│   Nodes draggable. SVG overlay for connections.         │
│   Config panel slides in from right on node select.     │
│                                                         │
├─────────────────────────────────────────────────────────┤
│ FOOTER: N nodes · M connections · [validation status]   │
└─────────────────────────────────────────────────────────┘
```

---

## Node Types

| Type | Border color | Fields |
|------|-------------|--------|
| `model` | denim `#6290c3` | model selector (7 white-label models) + optional system prompt override |
| `prompt_template` | warm-gray `#a89080` | template text (static string injected before downstream node) |
| `scout` | green `#2c8c4a` | mode: auto / force |
| `merge` | rose `#c36290` | separator string (default `\n\n---\n\n`) |

Each node has:
- **Input port** (left, hollow circle) — receives text from upstream nodes
- **Output port** (right, filled circle, colored by type) — sends text downstream
- **Delete button** (top-right ✕, visible on hover)
- **Type badge** (9px uppercase, colored)
- **Label** (model name or template preview truncated to 24 chars)

Nodes with no inputs automatically receive the user's query text.

---

## Connections

- User drags from an **output port** → drops on an **input port**
- An SVG `<path>` cubic bezier renders between ports, colored by the source node's type
- Arrowhead marker at target end
- Dragging a new connection from a port that already has one **replaces** the existing connection
- Clicking an existing connection line selects + deletes it (press Delete / Backspace, or click the ✕ that appears at midpoint)
- Cycles detected client-side (Kahn's algorithm, same as backend); invalid connections show red and refuse to connect

---

## Config Panel

Slides in from the right (220px wide) when a node is clicked/selected. Fields:

- **Model node:** model dropdown (Apex/Swift/Prism/Depth/Atlas/Horizon/Pulse), system prompt textarea
- **Prompt node:** template textarea (full text)
- **Scout node:** mode radio (auto / force)
- **Merge node:** separator text input

Shows "Inputs: ← NodeA, NodeB" as read-only tags at the bottom.

---

## State Shape

```ts
interface WorkflowNode {
  id: string           // "node_0", "node_1", …
  type: 'model' | 'prompt_template' | 'scout' | 'merge'
  model?: ModelName    // model nodes only
  systemPrompt?: string
  template?: string    // prompt_template nodes
  scoutMode?: 'auto' | 'force'  // scout nodes
  separator?: string   // merge nodes
  inputs: string[]     // upstream node IDs
  // UI-only (not sent to backend):
  x: number
  y: number
}
```

The canvas holds `nodes: WorkflowNode[]` in local React state. On Run, UI-only fields are stripped and the array is serialized into `workflow_nodes` in the `QueryRequest`.

---

## Run Flow

1. User clicks **Run ▶** (or presses Enter in the chat input while overlay is open)
2. Client validates: ≥1 node, no cycles, all model nodes have a model selected
3. Overlay closes with a slide-down animation (300ms `cubic-bezier(0.16,1,0.3,1)`)
4. `workflow_nodes` passed to `buildQueryRequest` — backend receives them via existing `QueryRequest.workflow_nodes`
5. Results stream into chat using the existing `CouncilGrid` renderer (one card per model node in topo order)
6. Non-model nodes (prompt, scout, merge) have no card — they are invisible pipeline steps

---

## Components

| File | Purpose |
|------|---------|
| `frontend/components/workflow/WorkflowOverlay.tsx` | Full-screen overlay wrapper, open/close animation |
| `frontend/components/workflow/WorkflowCanvas.tsx` | Canvas: node rendering, drag-to-move, SVG connections |
| `frontend/components/workflow/WorkflowNode.tsx` | Individual node card with ports |
| `frontend/components/workflow/WorkflowConfigPanel.tsx` | Right-side config panel |
| `frontend/components/workflow/WorkflowToolbar.tsx` | Top toolbar with palette buttons + Run |
| `frontend/lib/workflow.ts` | State types, topo-sort validation, serialize-for-backend |

`ChatWindow.tsx` gets a `workflowOpen` boolean state + passes `workflowNodes` to `send()`. The existing auto-chain fallback in `send()` is replaced by the UI-built nodes.

---

## Animations

- Overlay open: `translateY(100%) → translateY(0)` slide up, 300ms ease
- Overlay close: reverse
- Node added: `scale(0.85) opacity(0) → scale(1) opacity(1)`, 200ms
- Config panel: `translateX(240px) → translateX(0)`, 220ms
- Connection draw: live bezier follows cursor while dragging
- Run button: `scale(0.97)` active press

---

## ChatInput changes

- Scout globe button hidden when `mode === 'workflow'` (Scout is a node type instead)
- Slash menu Workflow entry opens the overlay directly instead of just setting mode
- Bottom label bar already removed; no changes needed there

---

## Constraints / Non-goals

- No persistence of workflow pipelines (not saved to DB — each run is stateless)
- No undo/redo
- No zoom/pan on canvas (nodes scroll if overflow)
- No custom node icons beyond color coding
- Workflow mode does not support Primal Protocol or Scout at the top level (Scout is a node type instead)
