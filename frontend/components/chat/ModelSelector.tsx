// components/chat/ModelSelector.tsx
'use client'
import { MODELS, MODEL_DISPLAY, MODEL_SUBTITLE, ModelName } from '@/lib/types'

interface Props {
  selected: ModelName[]
  onChange: (models: ModelName[]) => void
  max?: number
  label?: string
}

export function ModelSelector({ selected, onChange, max, label }: Props) {
  function toggle(m: ModelName) {
    if (max === 1) {
      onChange([m])
      return
    }
    if (selected.includes(m)) {
      onChange(selected.filter(x => x !== m))
    } else if (max === undefined || selected.length < max) {
      onChange([...selected, m])
    }
  }

  const heading = label ?? (max !== undefined ? `Pick ${max}` : 'Council')

  return (
    <div className="flex flex-col gap-0.5">
      <p className="text-[10px] font-bold text-warm-gray uppercase tracking-widest px-1 mb-1">
        Models — {heading}
      </p>
      {MODELS.map(m => {
        const on = selected.includes(m)
        const atMax = max !== undefined && max > 1 && selected.length >= max && !on
        return (
          <button
            key={m}
            onClick={() => toggle(m)}
            disabled={atMax}
            className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-left transition-colors duration-150 ${
              on
                ? 'bg-denim/15 text-denim'
                : atMax
                  ? 'text-warm-gray/40 cursor-not-allowed'
                  : 'text-black hover:bg-black/5'
            }`}
          >
            <span className={`w-3 h-3 rounded-full border-2 flex-shrink-0 ${on ? 'bg-denim border-denim' : atMax ? 'border-warm-gray/30' : 'border-warm-gray'}`} />
            <span className="flex flex-col min-w-0">
              <span className="text-sm font-semibold leading-tight">{MODEL_DISPLAY[m]}</span>
              <span className={`text-[10px] leading-tight ${on ? 'text-denim/70' : 'text-warm-gray'}`}>{MODEL_SUBTITLE[m]}</span>
            </span>
          </button>
        )
      })}
    </div>
  )
}
