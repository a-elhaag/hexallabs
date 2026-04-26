'use client'
import { WorkflowNode, NODE_LABEL, NODE_COLOR } from '@/lib/workflow'
import { MODELS } from '@/lib/types'

interface Props {
  node: WorkflowNode
  allNodes: WorkflowNode[]
  onChange: (updated: WorkflowNode) => void
  onClose: () => void
}

export function WorkflowConfigPanel({ node, allNodes, onChange, onClose }: Props) {
  const color = NODE_COLOR[node.type]
  const inputNodes = allNodes.filter(n => node.inputs.includes(n.id))

  return (
    <div
      className="absolute right-4 top-4 w-56 bg-white border border-warm-gray/20 rounded-2xl p-4 shadow-xl"
      style={{ zIndex: 20, animation: 'configIn 220ms cubic-bezier(0.16,1,0.3,1) both' }}
    >
      <style>{`@keyframes configIn { from { opacity:0; transform:translateX(24px) } to { opacity:1; transform:translateX(0) } }`}</style>

      <div className="flex items-center justify-between mb-3">
        <p className="text-[10px] font-black uppercase tracking-widest" style={{ color }}>
          {NODE_LABEL[node.type]}
        </p>
        <button onClick={onClose} className="text-warm-gray hover:text-[#2c2c2c] text-xs leading-none">✕</button>
      </div>

      {node.type === 'model' && (
        <>
          <div className="mb-3">
            <p className="text-[10px] font-bold text-warm-gray uppercase tracking-wide mb-1">Model</p>
            <select
              value={node.model ?? ''}
              onChange={e => onChange({ ...node, model: e.target.value as typeof MODELS[number] })}
              className="w-full px-2 py-1.5 border border-warm-gray/30 rounded-lg text-xs font-semibold text-[#2c2c2c] bg-[#f5f1ed] focus:outline-none focus:border-denim"
            >
              <option value="" disabled>Select model…</option>
              {MODELS.map(m => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>
          <div className="mb-3">
            <p className="text-[10px] font-bold text-warm-gray uppercase tracking-wide mb-1">System prompt</p>
            <textarea
              value={node.systemPrompt ?? ''}
              onChange={e => onChange({ ...node, systemPrompt: e.target.value })}
              placeholder="Optional override…"
              rows={3}
              className="w-full px-2 py-1.5 border border-warm-gray/30 rounded-lg text-[11px] text-[#2c2c2c] bg-[#f5f1ed] resize-none focus:outline-none focus:border-warm-gray"
            />
          </div>
        </>
      )}

      {node.type === 'prompt_template' && (
        <div className="mb-3">
          <p className="text-[10px] font-bold text-warm-gray uppercase tracking-wide mb-1">Template text</p>
          <textarea
            value={node.template ?? ''}
            onChange={e => onChange({ ...node, template: e.target.value })}
            placeholder="System context injected before downstream node…"
            rows={5}
            className="w-full px-2 py-1.5 border border-warm-gray/30 rounded-lg text-[11px] text-[#2c2c2c] bg-[#f5f1ed] resize-none focus:outline-none focus:border-warm-gray"
          />
        </div>
      )}

      {node.type === 'scout' && (
        <div className="mb-3">
          <p className="text-[10px] font-bold text-warm-gray uppercase tracking-wide mb-1">Mode</p>
          {(['auto', 'force'] as const).map(m => (
            <label key={m} className="flex items-center gap-2 mb-1.5 cursor-pointer">
              <input
                type="radio"
                name={`scoutMode-${node.id}`}
                value={m}
                checked={(node.scoutMode ?? 'auto') === m}
                onChange={() => onChange({ ...node, scoutMode: m })}
                className="accent-denim"
              />
              <span className="text-xs font-semibold text-[#2c2c2c] capitalize">{m}</span>
            </label>
          ))}
        </div>
      )}

      {node.type === 'merge' && (
        <div className="mb-3">
          <p className="text-[10px] font-bold text-warm-gray uppercase tracking-wide mb-1">Separator</p>
          <input
            value={node.separator ?? '\n\n---\n\n'}
            onChange={e => onChange({ ...node, separator: e.target.value })}
            className="w-full px-2 py-1.5 border border-warm-gray/30 rounded-lg text-[11px] font-mono text-[#2c2c2c] bg-[#f5f1ed] focus:outline-none focus:border-warm-gray"
          />
        </div>
      )}

      {inputNodes.length > 0 && (
        <div>
          <p className="text-[10px] font-bold text-warm-gray uppercase tracking-wide mb-1">Inputs</p>
          <div className="flex flex-wrap gap-1">
            {inputNodes.map(n => (
              <span key={n.id} className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#2c2c2c]/8 text-warm-gray">
                ← {n.type === 'model' ? (n.model ?? n.id) : NODE_LABEL[n.type]}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
