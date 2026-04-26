// components/layout/Navbar.tsx
'use client'
import { useState, useEffect, useRef } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { PenSquare, Settings, LogOut } from 'lucide-react'
import { Avatar } from '@/components/ui/Avatar'
import { signOut, getUser } from '@/lib/auth'

export function Navbar() {
  const pathname = usePathname()
  const router   = useRouter()
  const [email, setEmail]       = useState<string | undefined>()
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef                 = useRef<HTMLDivElement>(null)

  useEffect(() => {
    getUser().then(u => setEmail(u?.email ?? undefined))
  }, [])

  useEffect(() => {
    if (!menuOpen) return
    function onClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [menuOpen])

  async function handleSignOut() {
    setMenuOpen(false)
    await signOut()
    router.push('/')
  }

  return (
    <header
      className="h-12 shrink-0 flex items-center px-4 gap-3 relative z-40"
      style={{
        background: 'rgba(28, 28, 28, 0.88)',
        backdropFilter: 'blur(24px) saturate(1.5)',
        WebkitBackdropFilter: 'blur(24px) saturate(1.5)',
        borderBottom: '1px solid rgba(255,255,255,0.07)',
        boxShadow: '0 4px 24px rgba(0,0,0,0.18)',
      }}
    >
      {/* Logo */}
      <Link href="/chat" className="text-white font-black text-sm tracking-wide opacity-90 mr-1">
        HEXALLABS
      </Link>

      {/* New chat */}
      <Link
        href="/chat?new=1"
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-white/50 hover:text-white hover:bg-white/8 transition-all text-xs font-medium"
        style={{ transition: 'all 200ms cubic-bezier(0.16, 1, 0.3, 1)' }}
        aria-label="New chat"
      >
        <PenSquare size={14} />
        New chat
      </Link>

      <div className="flex-1" />

      {/* Avatar → dropdown */}
      <div className="relative flex items-center" ref={menuRef}>
        <button
          onClick={() => setMenuOpen(o => !o)}
          className="flex items-center justify-center rounded-full ring-2 ring-transparent hover:ring-white/20 transition-all"
          aria-label="Account menu"
          aria-expanded={menuOpen}
        >
          <Avatar email={email} size="sm" />
        </button>

        {menuOpen && (
          <div
            className="absolute right-0 top-full mt-2 w-52 rounded-2xl z-50"
            style={{
              background: 'rgba(32, 32, 32, 0.95)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255,255,255,0.10)',
              boxShadow: '0 8px 32px rgba(0,0,0,0.40)',
            }}
          >
            <div className="px-4 py-3 border-b border-white/8 rounded-t-2xl">
              <p className="text-white/40 text-[11px] truncate">{email}</p>
            </div>
            <div className="p-1.5 flex flex-col gap-0.5 rounded-b-2xl">
              <Link
                href="/settings"
                onClick={() => setMenuOpen(false)}
                className={`flex items-center gap-3 px-3 py-2 rounded-xl text-sm transition-all ${
                  pathname === '/settings'
                    ? 'bg-white/15 text-white'
                    : 'text-white/60 hover:text-white hover:bg-white/8'
                }`}
              >
                <Settings size={15} className="shrink-0" />
                Settings
              </Link>
              <button
                onClick={handleSignOut}
                className="flex items-center gap-3 px-3 py-2 rounded-xl text-sm text-white/60 hover:text-white hover:bg-white/8 transition-all w-full text-left"
              >
                <LogOut size={15} className="shrink-0" />
                Sign out
              </button>
            </div>
          </div>
        )}
      </div>
    </header>
  )
}
