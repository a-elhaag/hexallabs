// components/layout/Sidebar.tsx
'use client'
import { useState, useEffect } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { MessageSquare, Settings, PlusSquare, LogOut } from 'lucide-react'
import { Avatar } from '@/components/ui/Avatar'
import { signOut, getUser } from '@/lib/auth'

const NAV = [
  { icon: PlusSquare,    label: 'New Chat', href: '/chat?new=1' },
  { icon: MessageSquare, label: 'History',  href: '/chat' },
  { icon: Settings,      label: 'Settings', href: '/settings' },
]

export function Sidebar() {
  const pathname   = usePathname()
  const router     = useRouter()
  const [expanded, setExpanded] = useState(false)
  const [email, setEmail]       = useState<string | undefined>()

  useEffect(() => {
    getUser().then(u => setEmail(u?.email ?? undefined))
  }, [])

  async function handleSignOut() {
    await signOut()
    router.push('/')
  }

  return (
    <aside
      className={`${expanded ? 'w-55' : 'w-14'} shrink-0 h-screen bg-[#1e1e1e] flex flex-col py-3 transition-[width] duration-300 overflow-hidden`}
      style={{ transitionTimingFunction: 'cubic-bezier(0.16, 1, 0.3, 1)' }}
      onMouseEnter={() => setExpanded(true)}
      onMouseLeave={() => setExpanded(false)}
    >
      {/* Logo */}
      <div className="px-3 mb-4 flex items-center gap-2.5 h-9">
        <div className="w-8 h-8 bg-denim rounded-2xl flex items-center justify-center shrink-0">
          <span className="text-white font-black text-sm">H</span>
        </div>
        {expanded && (
          <span className="text-white font-black text-sm tracking-wide whitespace-nowrap opacity-90">
            HEXALLABS
          </span>
        )}
      </div>

      {/* Nav */}
      <nav className="flex flex-col gap-0.5 w-full px-2 flex-1">
        {NAV.map(({ icon: Icon, label, href }) => {
          const active = pathname === href.split('?')[0]
          return (
            <Link
              key={label}
              href={href}
              className={`flex items-center gap-3 px-2.5 py-2.5 rounded-2xl transition-all duration-150 whitespace-nowrap group ${
                active
                  ? 'bg-white/15 text-white'
                  : 'text-white/40 hover:text-white/80 hover:bg-white/8'
              }`}
            >
              <Icon size={18} className="shrink-0" />
              {expanded && <span className="text-sm font-semibold">{label}</span>}
            </Link>
          )
        })}
      </nav>

      {/* Bottom */}
      <div className="w-full px-2 flex flex-col gap-0.5">
        {expanded ? (
          <div className="flex items-center gap-2 px-2.5 py-2 rounded-2xl hover:bg-white/8 transition-colors cursor-default">
            <Avatar email={email} size="sm" />
            <span className="text-white/70 text-xs truncate flex-1">{email}</span>
            <button onClick={handleSignOut} className="text-white/30 hover:text-white/80 transition-colors" aria-label="Sign out">
              <LogOut size={14} />
            </button>
          </div>
        ) : (
          <button
            onClick={handleSignOut}
            className="flex items-center justify-center py-2.5 text-white/30 hover:text-white/80 transition-colors rounded-2xl hover:bg-white/8"
            aria-label="Sign out"
          >
            <LogOut size={18} />
          </button>
        )}
      </div>
    </aside>
  )
}
