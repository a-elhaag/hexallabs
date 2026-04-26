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
  const dragConnRef = useRef<DragConn | null>(null)
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
      const d = { fromId: nodeId, x1: p.x, y1: p.y, x2: ev.clientX - rect.left, y2: ev.clientY - rect.top }
      dragConnRef.current = d
      setDragConn(d)
    }
    function onUp() {
      // Use a small delay so React's synthetic onMouseUp on the target port fires first
      setTimeout(() => {
        dragConnRef.current = null
        setDragConn(null)
      }, 0)
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup', onUp)
    }
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
  }, [nodes])

  const onPortMouseUp = useCallback((e: React.MouseEvent, nodeId: string, port: 'in' | 'out') => {
    if (port !== 'in') return
    // Read from ref — state may already be null if window mouseup fired first
    const conn = dragConnRef.current
    if (!conn) return
    e.preventDefault()
    const { fromId } = conn
    const toId = nodeId
    dragConnRef.current = null
    setDragConn(null)
    if (fromId === toId || wouldCreateCycle(nodes, fromId, toId)) return
    // Append fromId to toId's inputs if not already present
    onChange(nodes.map(n => n.id === toId && !n.inputs.includes(fromId) ? { ...n, inputs: [...n.inputs, fromId] } : n))
  }, [nodes, onChange])

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
