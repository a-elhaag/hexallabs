// components/landing/Features.tsx

interface FeatureSection {
  tag: string
  headline: string
  accent: string
  body: string
  reverse?: boolean
}

const sections: FeatureSection[] = [
  {
    tag: 'The Council',
    headline: 'Every model has a',
    accent: 'voice.',
    body: 'Select up to 7 models. Each reasons independently, then anonymously critiques the others. Apex synthesizes a final answer weighed by confidence and review.',
  },
  {
    tag: 'Oracle',
    headline: 'One model.',
    accent: 'Full focus.',
    body: 'Pick a single model and chat directly. Clean, fast, no overhead. Switch to Council any time using the / menu.',
    reverse: true,
  },
  {
    tag: 'The Relay & Scout',
    headline: 'Chain models.',
    accent: 'Search the web.',
    body: 'Relay passes context between models mid-conversation. Scout grounds any response in live web results via Tavily.',
  },
]

function FeatureMockup({ tag }: { tag: string }) {
  return (
    <div className="w-full max-w-xs bg-white border border-warm-gray/30 rounded-xl p-5 shadow-sm flex flex-col gap-3">
      <div className="text-xs font-semibold text-warm-gray tracking-widest uppercase">{tag}</div>
      <div className="flex flex-col gap-2">
        <div className="self-end bg-denim rounded-lg px-3 py-2 max-w-[75%]">
          <div className="h-2.5 w-24 bg-white/60 rounded" />
        </div>
        <div className="self-start bg-cream border border-warm-gray/30 rounded-lg px-3 py-2 max-w-[85%]">
          <div className="h-2.5 w-32 bg-black/30 rounded mb-1.5" />
          <div className="h-2.5 w-20 bg-black/20 rounded" />
        </div>
      </div>
      <div className="flex gap-1.5 mt-1">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="w-6 h-6 rounded-full bg-denim/80" style={{ opacity: 1 - i * 0.2 }} />
        ))}
      </div>
    </div>
  )
}

export function Features() {
  return (
    <section id="features" className="bg-cream">
      {sections.map((s, i) => (
        <div
          key={s.tag}
          className={`max-w-5xl mx-auto px-6 md:px-12 py-24 flex flex-col ${s.reverse ? 'md:flex-row-reverse' : 'md:flex-row'} items-center gap-12 ${i < sections.length - 1 ? 'border-b border-warm-gray/20' : ''}`}
        >
          <div className="flex-1 flex flex-col gap-4">
            <p className="text-denim text-xs font-bold tracking-widest uppercase">{s.tag}</p>
            <h2 className="font-black text-4xl text-black leading-tight tracking-tight">
              {s.headline}<br />
              <span className="text-denim">{s.accent}</span>
            </h2>
            <p className="text-warm-gray text-base max-w-md leading-relaxed">{s.body}</p>
          </div>
          <div className="flex-1 flex justify-center">
            <FeatureMockup tag={s.tag} />
          </div>
        </div>
      ))}

      {/* Footer */}
      <footer className="bg-black text-cream py-12 px-6 md:px-12">
        <div className="max-w-5xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-denim rounded-md flex items-center justify-center">
              <span className="text-white font-black text-xs">H</span>
            </div>
            <span className="font-black text-sm tracking-wide">HEXALLABS</span>
          </div>
          <p className="text-warm-gray text-xs">© {new Date().getFullYear()} HexalLabs. All rights reserved.</p>
        </div>
      </footer>
    </section>
  )
}
