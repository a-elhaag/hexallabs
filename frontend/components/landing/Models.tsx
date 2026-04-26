'use client'
import { useReveal } from '@/lib/useReveal'

const models = [
  { name: 'Apex', role: 'Chairman', by: 'Anthropic', model: 'claude-opus-4-7', desc: 'Synthesizes the final answer. Weighs every voice.' },
  { name: 'Pulse', role: 'Reasoning', by: 'Anthropic', model: 'claude-sonnet-4-6', desc: 'Cutting edge. Latest capabilities, pushed hard.' },
  { name: 'Swift', role: 'Organizer', by: 'Anthropic', model: 'claude-haiku-4-5', desc: 'Structures fast. Keeps the Council on track.' },
  { name: 'Prism', role: 'Reasoner', by: 'xAI', model: 'grok-4-20-reasoning', desc: 'Logic-first. No shortcuts. No assumptions.' },
  { name: 'Depth', role: 'Analyst', by: 'DeepSeek', model: 'DeepSeek-V3.2', desc: 'Slow and brutal. Catches what everyone else missed.' },
  { name: 'Atlas', role: 'Open-source', by: 'Meta', model: 'Llama-4-Maverick', desc: 'Different priors. Brings perspectives others can\'t.' },
  { name: 'Horizon', role: 'Long Context', by: 'Moonshot AI', model: 'Kimi-K2.5', desc: 'Holds the full picture. Nothing slips through.' },
]

function HexCard({ model, i }: { model: typeof models[0]; i: number }) {
  const ref = useReveal(0.1)
  return (
    <div
      ref={ref}
      style={{ opacity: 0, animationDelay: `${i * 0.06}s` }}
      className="group flex flex-col gap-2 p-5 rounded-3xl border border-warm-gray/20 bg-white hover:border-denim/40 hover:shadow-md transition-all duration-300 hover:-translate-y-1"
    >
      <div className="flex items-center gap-3">
        <div
          className="w-9 h-10 bg-denim/10 group-hover:bg-denim/20 transition-colors duration-300 flex items-center justify-center"
          style={{ clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)' }}
        >
          <span className="text-denim font-black text-xs">{model.name[0]}</span>
        </div>
        <div>
          <p className="font-black text-black text-sm leading-none">{model.name}</p>
          <p className="text-denim text-xs font-semibold tracking-widest uppercase mt-0.5">{model.role}</p>
        </div>
      </div>
      <p className="text-warm-gray text-sm leading-relaxed">{model.desc}</p>
      <div className="flex items-center justify-between mt-1 pt-2 border-t border-warm-gray/15">
        <span className="text-warm-gray/60 text-[11px] font-semibold">{model.by}</span>
        <span className="font-mono text-[10px] text-denim/60">{model.model}</span>
      </div>
    </div>
  )
}

export function Models() {
  const titleRef = useReveal(0.1)
  return (
    <section className="bg-black py-24 px-6 md:px-12">
      <div className="max-w-5xl mx-auto">
        <div ref={titleRef} style={{ opacity: 0 }} className="text-center mb-14 flex flex-col gap-3">
          <p className="text-denim text-xs font-bold tracking-widest uppercase">The Council</p>
          <h2 className="font-black text-4xl md:text-5xl text-cream leading-tight tracking-tight">
            Seven minds.<br />
            <span className="text-warm-gray">Each with a role.</span>
          </h2>
          <p className="text-warm-gray text-base max-w-md mx-auto leading-relaxed">
            No single model owns the answer. Every voice is heard. Apex decides.
          </p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {models.map((m, i) => (
            <HexCard key={m.name} model={m} i={i} />
          ))}
          <div className="flex flex-col items-center justify-center p-5 rounded-3xl border border-warm-gray/10 border-dashed">
            <p className="text-warm-gray/50 text-xs text-center font-semibold tracking-wider uppercase leading-relaxed">
              Mix any<br />combination.<br />You choose<br />the panel.
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}
