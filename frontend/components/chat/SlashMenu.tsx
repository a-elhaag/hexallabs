// components/chat/SlashMenu.tsx
'use client'
import { useEffect, useRef, useState } from 'react'
import { Zap, Users, GitBranch, Workflow, Flame } from 'lucide-react'
import { Mode, ModelName } from '@/lib/types'
import { ModelSelector } from './ModelSelector'

interface Props {
  onClose: () => void
  mode: Mode
  onMode: (m: Mode) => void
  models: ModelName[]
  onModels: (ms: ModelName[]) => void
  primal: boolean
  onPrimal: (v: boolean) => void
}

const MODES: { id: Mode; label: string; icon: React.ElementType; desc: string }[] = [
  { id: 'oracle',   label: 'Oracle',      icon: Zap,      desc: 'Single model, full focus' },
  { id: 'council',  label: 'The Council', icon: Users,    desc: '7 models, peer review, synthesis' },
  { id: 'relay',    label: 'The Relay',   icon: GitBranch,desc: 'Chain models mid-conversation' },
  { id: 'workflow', label: 'Workflow',    icon: Workflow,  desc: 'Custom multi-node pipeline' },
]

export function SlashMenu({ onClose, mode, onMode, models, onModels, primal, onPrimal }: Props) {
  const ref = useRef<HTMLDivElement>(null)
  const [focused, setFocused] = useState(0)

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') { onClose(); return }
      if (e.key === 'ArrowDown') setFocused(f => Math.min(f + 1, MODES.length - 1))
      if (e.key === 'ArrowUp')   setFocused(f => Math.max(f - 1, 0))
      if (e.key === 'Enter') { onMode(MODES[focused].id); onClose() }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [focused, onClose, onMode])

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose()
    }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [onClose])

  return (
    <div
      ref={ref}
      className="absolute bottom-full left-0 mb-2 w-72 max-h-96 bg-cream/95 backdrop-blur-md border border-black rounded-xl shadow-xl overflow-y-auto z-30"
    >
      <div className="p-2 flex flex-col gap-0.5">
        <p className="text-[10px] font-bold text-warm-gray uppercase tracking-widest px-2 py-1">Mode</p>
        {MODES.map((m, i) => {
          const Icon = m.icon
          const active = mode === m.id
          return (
            <button
              key={m.id}
              onClick={() => { onMode(m.id); if (m.id !== 'council') onClose() }}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-left transition-colors duration-100 ${
                active ? 'bg-denim text-white' : i === focused ? 'bg-black/5 text-black' : 'text-black hover:bg-black/5'
              }`}
            >
              <Icon size={16} className="flex-shrink-0" />
              <span className="font-semibold">{m.label}</span>
              <span className={`text-xs ml-auto ${active ? 'text-white/70' : 'text-warm-gray'}`}>{m.desc}</span>
            </button>
          )
        })}
      </div>

      {mode === 'council' && (
        <div className="border-t border-warm-gray/20 p-3">
          <ModelSelector selected={models} onChange={onModels} />
        </div>
      )}

      <div className="border-t border-warm-gray/20 p-2">
        <button
          onClick={() => onPrimal(!primal)}
          className={`flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm text-left transition-colors duration-100 ${
            primal ? 'bg-warm-gray/20 text-black' : 'text-black hover:bg-black/5'
          }`}
        >
          <Flame size={16} className={primal ? 'text-denim' : 'text-warm-gray'} />
          <span className="font-semibold">Primal Protocol</span>
          <span className="text-xs ml-auto text-warm-gray">Caveman rewrite</span>
        </button>
      </div>
    </div>
  )
}
