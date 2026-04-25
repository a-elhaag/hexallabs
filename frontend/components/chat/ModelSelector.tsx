// components/chat/ModelSelector.tsx
'use client'
import { MODELS, MODEL_DISPLAY, ModelName } from '@/lib/types'

interface Props {
  selected: ModelName[]
  onChange: (models: ModelName[]) => void
}

export function ModelSelector({ selected, onChange }: Props) {
  function toggle(m: ModelName) {
    onChange(
      selected.includes(m) ? selected.filter(x => x !== m) : [...selected, m]
    )
  }

  return (
    <div className="flex flex-col gap-1">
      <p className="text-[10px] font-bold text-warm-gray uppercase tracking-widest px-1 mb-1">
        Models — Council
      </p>
      {MODELS.map(m => {
        const on = selected.includes(m)
        return (
          <button
            key={m}
            onClick={() => toggle(m)}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-semibold text-left transition-colors duration-150 ${
              on ? 'bg-denim/15 text-denim' : 'text-black hover:bg-black/5'
            }`}
          >
            <span className={`w-3 h-3 rounded-full border-2 flex-shrink-0 ${on ? 'bg-denim border-denim' : 'border-warm-gray'}`} />
            {MODEL_DISPLAY[m]}
          </button>
        )
      })}
    </div>
  )
}
