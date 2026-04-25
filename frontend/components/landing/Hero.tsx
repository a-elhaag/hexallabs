// components/landing/Hero.tsx
import Link from 'next/link'
import { Button } from '@/components/ui/Button'

function HexGrid() {
  const hexes = Array.from({ length: 15 }, (_, i) => i)
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none" aria-hidden>
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 flex flex-wrap w-[420px] gap-3 opacity-10">
        {hexes.map(i => (
          <div
            key={i}
            className="w-14 h-16 bg-denim animate-pulse"
            style={{
              clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)',
              animationDelay: `${(i * 0.15) % 2}s`,
              animationDuration: '3s',
              opacity: 0.4 + (i % 4) * 0.15,
            }}
          />
        ))}
      </div>
    </div>
  )
}

export function Hero() {
  return (
    <section className="relative min-h-screen bg-black flex flex-col items-center justify-center text-center px-6 overflow-hidden">
      <HexGrid />
      <div className="relative z-10 max-w-2xl mx-auto flex flex-col items-center gap-6">
        <p className="text-warm-gray text-sm font-semibold tracking-widest uppercase">
          Multi-model AI Council
        </p>
        <h1 className="text-cream font-black text-5xl md:text-7xl leading-none tracking-tight">
          Seven minds.<br />One answer.
        </h1>
        <p className="text-warm-gray text-lg max-w-md leading-relaxed">
          Ask once. Seven AI models reason in parallel, peer-review each other,
          and synthesize one confident response.
        </p>
        <div className="flex items-center gap-4 mt-2">
          <Link href="/auth/signup">
            <Button variant="primary" className="px-8 py-3 text-base">
              Start for free
            </Button>
          </Link>
          <Link href="#features">
            <Button variant="outline" className="px-8 py-3 text-base border-warm-gray text-warm-gray hover:border-cream hover:text-cream">
              See how it works
            </Button>
          </Link>
        </div>
      </div>
    </section>
  )
}
