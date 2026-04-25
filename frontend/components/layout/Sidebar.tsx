// components/layout/Sidebar.tsx
'use client'
import { useState, useEffect } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { MessageSquare, Settings, PlusSquare, ChevronRight, LogOut } from 'lucide-react'
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

  const w = expanded ? 'w-[220px]' : 'w-[52px]'

  return (
    <aside
      className={`${w} flex-shrink-0 h-screen bg-black flex flex-col items-start py-4 transition-[width] duration-300 overflow-hidden`}
      style={{ transitionTimingFunction: 'cubic-bezier(0.16, 1, 0.3, 1)' }}
      onMouseEnter={() => setExpanded(true)}
      onMouseLeave={() => setExpanded(false)}
    >
      {/* Logo */}
      <div className="px-3 mb-6 flex items-center gap-3 h-8">
        <div className="w-7 h-7 bg-denim rounded-md flex items-center justify-center flex-shrink-0">
          <span className="text-white font-black text-xs">H</span>
        </div>
        {expanded && (
          <span className="text-cream font-black text-sm tracking-wide whitespace-nowrap">
            HEXALLABS
          </span>
        )}
      </div>

      {/* Nav items */}
      <nav className="flex flex-col gap-1 w-full px-2 flex-1">
        {NAV.map(({ icon: Icon, label, href }) => {
          const active = pathname === href.split('?')[0]
          return (
            <Link
              key={label}
              href={href}
              className={`flex items-center gap-3 px-2 py-2.5 rounded-lg transition-colors duration-150 whitespace-nowrap ${
                active
                  ? 'bg-denim text-white'
                  : 'text-warm-gray hover:text-cream hover:bg-white/10'
              }`}
            >
              <Icon size={20} className="flex-shrink-0" />
              {expanded && <span className="text-sm font-semibold">{label}</span>}
            </Link>
          )
        })}
      </nav>

      {/* Bottom: user + sign out */}
      <div className="w-full px-2 flex flex-col gap-1">
        {expanded ? (
          <div className="flex items-center gap-2 px-2 py-2">
            <Avatar email={email} size="sm" />
            <span className="text-cream text-xs truncate flex-1">{email}</span>
            <button onClick={handleSignOut} className="text-warm-gray hover:text-cream transition-colors" aria-label="Sign out">
              <LogOut size={15} />
            </button>
          </div>
        ) : (
          <button
            onClick={handleSignOut}
            className="flex items-center justify-center px-2 py-2.5 text-warm-gray hover:text-cream transition-colors"
            aria-label="Sign out"
          >
            <LogOut size={20} />
          </button>
        )}

        <button
          onClick={() => setExpanded(v => !v)}
          className="flex items-center justify-center px-2 py-1.5 text-warm-gray/40 hover:text-warm-gray transition-colors"
          aria-label={expanded ? 'Collapse sidebar' : 'Expand sidebar'}
        >
          <ChevronRight size={14} className={`transition-transform duration-300 ${expanded ? 'rotate-180' : ''}`} />
        </button>
      </div>
    </aside>
  )
}
