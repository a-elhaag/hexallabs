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
      id: newNodeId(),
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
