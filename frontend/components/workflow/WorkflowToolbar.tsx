'use client'
import { WFNodeType, NODE_COLOR, NODE_LABEL } from '@/lib/workflow'

const PALETTE: WFNodeType[] = ['model', 'prompt_template', 'scout', 'merge']

interface Props {
  onAddNode: (type: WFNodeType) => void
  onRun: () => void
  onClose: () => void
  validationError: string | null
  nodeCount: number
}

export function WorkflowToolbar({ onAddNode, onRun, onClose, validationError, nodeCount }: Props) {
  const canRun = !validationError && nodeCount > 0

  return (
    <div className="h-12 flex items-center gap-3 px-4 bg-[#f5f1ed] border-b border-warm-gray/20 shrink-0">
      <span className="font-black text-sm text-[#2c2c2c] tracking-tight">Workflow</span>
      <div className="w-px h-5 bg-warm-gray/20" />

      <div className="flex gap-1.5">
        {PALETTE.map(type => (
          <button
            key={type}
            onClick={() => onAddNode(type)}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-[11px] font-bold transition-all hover:-translate-y-0.5 hover:shadow-md active:scale-95"
            style={{
              borderColor: NODE_COLOR[type],
              color: NODE_COLOR[type],
              background: `${NODE_COLOR[type]}12`,
            }}
          >
            <span className="w-1.5 h-1.5 rounded-full" style={{ background: NODE_COLOR[type] }} />
            + {NODE_LABEL[type]}
          </button>
        ))}
      </div>

      <div className="flex-1" />

      {validationError && (
        <span className="text-[11px] text-red-500 font-semibold">{validationError}</span>
      )}

      <button
        onClick={onRun}
        disabled={!canRun}
        className={`flex items-center gap-1.5 px-4 py-1.5 rounded-xl text-sm font-black transition-all active:scale-[0.97] ${
          canRun
            ? 'bg-[#2c2c2c] text-[#f5f1ed] hover:bg-denim cursor-pointer'
            : 'bg-[#2c2c2c]/15 text-warm-gray cursor-not-allowed'
        }`}
      >
        ▶ Run
      </button>

      <div className="w-px h-5 bg-warm-gray/20" />

      <button
        onClick={onClose}
        className="text-warm-gray hover:text-[#2c2c2c] text-lg leading-none transition-colors"
        aria-label="Close workflow builder"
      >✕</button>
    </div>
  )
}
