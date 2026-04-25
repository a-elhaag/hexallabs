// components/chat/ChatInput.tsx
'use client'
import { useRef, useState, useCallback } from 'react'
import { Plus, Send, X, Globe, Trash2 } from 'lucide-react'
import { Mode, ModelName, ScoutMode } from '@/lib/types'
import { SlashMenu } from './SlashMenu'

interface Props {
  onSend: (query: string) => void
  disabled?: boolean
  mode: Mode
  onMode: (m: Mode) => void
  models: ModelName[]
  onModels: (ms: ModelName[]) => void
  primal: boolean
  onPrimal: (v: boolean) => void
  scout: ScoutMode
  onScout: (s: ScoutMode) => void
  onClear: () => void
}

export function ChatInput({ onSend, disabled, mode, onMode, models, onModels, primal, onPrimal, scout, onScout, onClear }: Props) {
  const [value, setValue]         = useState('')
  const [slashOpen, setSlashOpen] = useState(false)
  const [plusOpen, setPlusOpen]   = useState(false)
  const [dragging, setDragging]   = useState(false)
  const textareaRef               = useRef<HTMLTextAreaElement>(null)

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === '/' && value === '' && !slashOpen) {
      e.preventDefault()
      setSlashOpen(true)
      return
    }
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  function handleSend() {
    const q = value.trim()
    if (!q || disabled) return
    onSend(q)
    setValue('')
  }

  const onDragOver = useCallback((e: React.DragEvent) => { e.preventDefault(); setDragging(true) }, [])
  const onDragLeave = useCallback(() => setDragging(false), [])
  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      setValue(v => v + (v ? '\n' : '') + `[Attached: ${files.map(f => f.name).join(', ')}]`)
    }
  }, [])

  return (
    <div
      className={`relative border-t border-warm-gray/30 bg-white transition-colors duration-150 ${dragging ? 'bg-denim/5 border-denim' : ''}`}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
    >
      {slashOpen && (
        <SlashMenu
          onClose={() => setSlashOpen(false)}
          mode={mode}
          onMode={onMode}
          models={models}
          onModels={onModels}
          primal={primal}
          onPrimal={onPrimal}
        />
      )}

      {plusOpen && (
        <div className="absolute bottom-full left-2 mb-2 bg-cream border border-black rounded-xl shadow-xl p-2 flex flex-col gap-1 z-30 min-w-[160px]">
          <button
            onClick={() => { onScout(scout === 'off' ? 'auto' : 'off'); setPlusOpen(false) }}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-semibold ${scout !== 'off' ? 'bg-denim/15 text-denim' : 'text-black hover:bg-black/5'}`}
          >
            <Globe size={15} />
            {scout !== 'off' ? 'Scout: on' : 'Web Search (Scout)'}
          </button>
          <button
            onClick={() => { onClear(); setPlusOpen(false) }}
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-semibold text-black hover:bg-black/5"
          >
            <Trash2 size={15} />
            Clear chat
          </button>
        </div>
      )}

      <div className="flex items-end gap-2 p-3">
        <button
          onClick={() => setPlusOpen(v => !v)}
          className="flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-xl text-warm-gray hover:text-black hover:bg-black/5 transition-colors"
          aria-label="More options"
        >
          {plusOpen ? <X size={18} /> : <Plus size={18} />}
        </button>

        <textarea
          ref={textareaRef}
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Message HexalLabs  ·  / for commands"
          rows={1}
          disabled={disabled}
          className="flex-1 resize-none bg-transparent border-b-2 border-warm-gray/40 focus:border-black outline-none text-sm text-black placeholder:text-warm-gray/50 py-1.5 transition-[border-color] duration-150 leading-relaxed max-h-40 overflow-y-auto"
        />

        <button
          onClick={handleSend}
          disabled={!value.trim() || disabled}
          className="flex-shrink-0 w-8 h-8 flex items-center justify-center bg-denim text-white rounded-xl disabled:opacity-30 transition-transform duration-150 hover:scale-[1.05] active:scale-95 cursor-pointer disabled:cursor-not-allowed"
          aria-label="Send"
        >
          <Send size={15} />
        </button>
      </div>

      <div className="flex items-center gap-2 px-4 pb-2">
        <button onClick={() => setSlashOpen(v => !v)} className="text-[10px] font-bold text-warm-gray hover:text-black uppercase tracking-widest transition-colors">
          {mode === 'oracle' ? 'Oracle' : mode === 'council' ? `Council · ${models.length} models` : mode === 'relay' ? 'Relay' : 'Workflow'}
        </button>
        {primal && <span className="text-[10px] font-bold text-denim tracking-widest">· Primal</span>}
        {scout !== 'off' && <span className="text-[10px] font-bold text-denim tracking-widest">· Scout</span>}
        {dragging && <span className="text-[10px] text-denim ml-auto">Drop file to attach</span>}
      </div>
    </div>
  )
}
