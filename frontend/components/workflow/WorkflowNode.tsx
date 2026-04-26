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
