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
export function newNodeId(): string {
  return `node_${Math.random().toString(36).slice(2, 10)}_${Date.now().toString(36)}`
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
