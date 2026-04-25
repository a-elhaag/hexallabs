'use client'
import { useRef, useState, useCallback } from 'react'
import { Plus, Globe, Trash2, ArrowUp } from 'lucide-react'
import { Mode, ModelName, ScoutMode } from '@/lib/types'
import { SlashMenu } from './SlashMenu'

interface Props {
  onSend: (query: string) => void
  onStop: () => void
  streaming: boolean
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

const MODE_LABEL: Record<Mode, string> = {
  oracle:   'Oracle',
  council:  'Council',
  relay:    'Relay',
  workflow: 'Workflow',
}

export function ChatInput({ onSend, onStop, streaming, mode, onMode, models, onModels, primal, onPrimal, scout, onScout, onClear }: Props) {
  const [value, setValue]         = useState('')
  const [slashOpen, setSlashOpen] = useState(false)
  const [plusOpen, setPlusOpen]   = useState(false)
  const [dragging, setDragging]   = useState(false)
  const textareaRef               = useRef<HTMLTextAreaElement>(null)

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === '/' && value === '' && !slashOpen) {
      e.preventDefault()
      setSlashOpen(true)
      setPlusOpen(false)
      return
    }
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  function handleSend() {
    const q = value.trim()
    if (!q || streaming) return
    onSend(q)
    setValue('')
    textareaRef.current?.focus()
  }

  const onDragOver  = useCallback((e: React.DragEvent) => { e.preventDefault(); setDragging(true) }, [])
  const onDragLeave = useCallback(() => setDragging(false), [])
  const onDrop      = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      setValue(v => v + (v ? '\n' : '') + `[Attached: ${files.map(f => f.name).join(', ')}]`)
    }
  }, [])

  const hasValue = value.trim().length > 0

  return (
    <div
      className="px-4 pb-4 pt-2 bg-cream"
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
    >
      <div className="relative">
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
          <div className="absolute bottom-full left-0 mb-2 bg-white border border-warm-gray/20 rounded-2xl shadow-lg p-1.5 flex flex-col gap-0.5 z-30 min-w-45">
            <button
              onClick={() => { onScout(scout === 'off' ? 'auto' : 'off'); setPlusOpen(false) }}
              className={`flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm font-semibold transition-colors ${scout !== 'off' ? 'bg-denim/10 text-denim' : 'text-[#2c2c2c] hover:bg-[#2c2c2c]/5'}`}
            >
              <Globe size={15} />
              {scout !== 'off' ? 'Scout on' : 'Web Search (Scout)'}
            </button>
            <button
              onClick={() => { onClear(); setPlusOpen(false) }}
              className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm font-semibold text-[#2c2c2c] hover:bg-[#2c2c2c]/5 transition-colors"
            >
              <Trash2 size={15} />
              Clear chat
            </button>
          </div>
        )}

        <div
          className={`flex flex-col bg-white rounded-3xl border transition-all duration-200 shadow-sm ${
            dragging ? 'border-denim shadow-denim/20 shadow-md' : 'border-warm-gray/25 hover:border-warm-gray/50'
          }`}
        >
          <div className="flex items-end gap-2 px-3 pt-3 pb-2">
            {/* + button */}
            <button
              onClick={() => { setPlusOpen(v => !v); setSlashOpen(false) }}
              className="shrink-0 w-7 h-7 flex items-center justify-center rounded-full text-warm-gray hover:text-[#2c2c2c] hover:bg-[#2c2c2c]/6 transition-colors mb-0.5"
              aria-label="More options"
            >
              <Plus size={16} />
            </button>

            {/* / button */}
            <button
              onClick={() => { setSlashOpen(v => !v); setPlusOpen(false) }}
              className={`shrink-0 w-7 h-7 flex items-center justify-center rounded-full font-black text-sm transition-colors mb-0.5 ${
                slashOpen ? 'bg-denim text-white' : 'text-warm-gray hover:text-[#2c2c2c] hover:bg-[#2c2c2c]/6'
              }`}
              aria-label="Open slash menu"
            >
              /
            </button>

            <textarea
              ref={textareaRef}
              value={value}
              onChange={e => setValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything…"
              rows={1}
              className="flex-1 resize-none bg-transparent outline-none text-sm text-[#2c2c2c] placeholder:text-warm-gray/50 py-0.5 leading-relaxed max-h-36 overflow-y-auto"
              style={{ fieldSizing: 'content' } as React.CSSProperties}
            />

            {/* Send / Stop button */}
            <button
              onClick={streaming ? onStop : handleSend}
              disabled={!streaming && !hasValue}
              className={`shrink-0 w-7 h-7 flex items-center justify-center rounded-full transition-all duration-150 mb-0.5 ${
                streaming
                  ? 'bg-[#2c2c2c] text-cream hover:scale-105 active:scale-95 cursor-pointer'
                  : hasValue
                    ? 'bg-[#2c2c2c] text-cream hover:scale-105 active:scale-95 cursor-pointer'
                    : 'bg-[#2c2c2c]/10 text-warm-gray cursor-not-allowed'
              }`}
              aria-label={streaming ? 'Stop generation' : 'Send'}
            >
              {streaming ? (
                <div className="w-2 h-2 bg-cream rounded-sm" />
              ) : (
                <ArrowUp size={15} />
              )}
            </button>
          </div>

          <div className="flex items-center gap-1.5 px-3 pb-2.5">
            <button
              onClick={() => { setSlashOpen(v => !v); setPlusOpen(false) }}
              className={`text-[11px] font-bold px-2.5 py-1 rounded-full transition-colors ${
                slashOpen ? 'bg-denim text-white' : 'text-warm-gray hover:text-[#2c2c2c] hover:bg-[#2c2c2c]/6'
              }`}
            >
              {mode === 'council' ? `Council · ${models.length}` : MODE_LABEL[mode]}
            </button>
            {primal && (
              <span className="text-[11px] font-bold px-2.5 py-1 rounded-full bg-warm-gray/15 text-warm-gray">
                Primal
              </span>
            )}
            {scout !== 'off' && (
              <span className="text-[11px] font-bold px-2.5 py-1 rounded-full bg-denim/10 text-denim">
                Scout
              </span>
            )}
            {dragging && (
              <span className="text-[11px] text-denim ml-auto">Drop to attach</span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
