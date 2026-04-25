// components/landing/Navbar.tsx
import Link from 'next/link'
import { Button } from '@/components/ui/Button'

export function Navbar() {
  return (
    <nav className="fixed top-0 left-0 right-0 z-40 flex items-center justify-between px-6 md:px-12 h-16">
      <Link href="/" className="flex items-center gap-2">
        <div className="w-7 h-7 bg-denim rounded-md flex items-center justify-center">
          <span className="text-white font-black text-xs">H</span>
        </div>
        <span className="font-black text-cream tracking-wide text-sm">HEXALLABS</span>
      </Link>
      <div className="flex items-center gap-3">
        <Link href="/auth/login">
          <Button variant="ghost" className="text-cream hover:bg-white/10 hover:text-cream">Sign in</Button>
        </Link>
        <Link href="/auth/signup">
          <Button variant="primary">Get started</Button>
        </Link>
      </div>
    </nav>
  )
}
