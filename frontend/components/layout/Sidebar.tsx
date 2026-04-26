// components/layout/Sidebar.tsx
'use client'
import { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { PlusSquare, Settings, LogOut, MessageSquare, PanelLeftOpen, PanelLeftClose } from 'lucide-react'
import { Avatar } from '@/components/ui/Avatar'
import { signOut, getUser } from '@/lib/auth'
import { getSessions, type SessionRow } from '@/lib/db'
import { supabase } from '@/lib/supabase'

const MODE_ICON: Record<string, string> = {
  oracle: 'O', council: 'C', relay: 'R', workflow: 'W',
}

function groupByDate(sessions: SessionRow[]): { label: string; items: SessionRow[] }[] {
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const yesterday = new Date(today.getTime() - 86_400_000)
  const weekAgo = new Date(today.getTime() - 7 * 86_400_000)

  const groups: Record<string, SessionRow[]> = {
    Today: [], Yesterday: [], 'This Week': [], Older: [],
  }

  for (const s of sessions) {
    const d = new Date(s.updated_at)
    const day = new Date(d.getFullYear(), d.getMonth(), d.getDate())
    if (day >= today) groups.Today.push(s)
    else if (day >= yesterday) groups.Yesterday.push(s)
    else if (day >= weekAgo) groups['This Week'].push(s)
    else groups.Older.push(s)
  }

  return Object.entries(groups)
    .filter(([, items]) => items.length > 0)
    .map(([label, items]) => ({ label, items }))
}

function truncate(s: string | null, n: number): string {
  if (!s) return 'Untitled'
  return s.length > n ? s.slice(0, n) + '…' : s
}

export function Sidebar({ onSessionSelect }: { onSessionSelect?: (id: string) => void }) {
  const pathname  = usePathname()
  const router    = useRouter()
  const [pinned, setPinned]       = useState(false)
  const [hovered, setHovered]     = useState(false)
  const [email, setEmail]         = useState<string | undefined>()
  const [sessions, setSessions]   = useState<SessionRow[]>([])
  const [activeId, setActiveId]   = useState<string | null>(null)

  const expanded = pinned || hovered

  useEffect(() => {
    getUser().then(u => setEmail(u?.email ?? undefined))
  }, [])

  const loadSessions = useCallback(() => {
    getSessions().then(setSessions).catch(() => {})
  }, [])

  useEffect(() => {
    loadSessions()
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event) => {
      if (event === 'SIGNED_IN' || event === 'TOKEN_REFRESHED') loadSessions()
    })
    return () => subscription.unsubscribe()
  }, [loadSessions])

  // Refresh when expanded so history is fresh
  useEffect(() => {
    if (expanded) loadSessions()
  }, [expanded, loadSessions])

  async function handleSignOut() {
    await signOut()
    router.push('/')
  }

  function handleSessionClick(id: string) {
    setActiveId(id)
    onSessionSelect?.(id)
  }

  const groups = groupByDate(sessions)

  return (
    <aside
      className={`${expanded ? 'w-60' : 'w-14'} shrink-0 h-screen flex flex-col transition-[width] duration-300 overflow-hidden relative`}
      style={{
        transitionTimingFunction: 'cubic-bezier(0.16, 1, 0.3, 1)',
        background: 'rgba(28, 28, 28, 0.75)',
        backdropFilter: 'blur(24px) saturate(1.5)',
        WebkitBackdropFilter: 'blur(24px) saturate(1.5)',
        borderRight: '1px solid rgba(255,255,255,0.07)',
        borderRadius: '0 20px 20px 0',
        boxShadow: '4px 0 40px rgba(0,0,0,0.22), inset -1px 0 0 rgba(255,255,255,0.04)',
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {/* Header */}
      <div className="px-2.5 pt-3 pb-2 flex items-center gap-2 shrink-0">
        {/* Pin/unpin toggle */}
        <button
          onClick={() => setPinned(p => !p)}
          className="w-9 h-9 flex items-center justify-center rounded-xl text-white/40 hover:text-white/80 hover:bg-white/8 transition-all shrink-0"
          aria-label={pinned ? 'Collapse sidebar' : 'Pin sidebar open'}
        >
          {pinned
            ? <PanelLeftClose size={18} />
            : <PanelLeftOpen size={18} />
          }
        </button>

        {expanded && (
          <>
            <span className="text-white font-black text-sm tracking-wide whitespace-nowrap opacity-90 flex-1">
              HEXALLABS
            </span>
            <Link
              href="/chat?new=1"
              className="w-8 h-8 flex items-center justify-center rounded-xl text-white/40 hover:text-white/80 hover:bg-white/8 transition-all shrink-0"
              aria-label="New chat"
            >
              <PlusSquare size={17} />
            </Link>
          </>
        )}
      </div>

      {/* Collapsed quick actions */}
      {!expanded && (
        <div className="flex flex-col items-center gap-0.5 px-2 mt-1">
          <Link
            href="/chat?new=1"
            className="w-9 h-9 flex items-center justify-center rounded-xl text-white/40 hover:text-white/80 hover:bg-white/8 transition-all"
            aria-label="New chat"
          >
            <PlusSquare size={18} />
          </Link>
          <Link
            href="/settings"
            className={`w-9 h-9 flex items-center justify-center rounded-xl transition-all ${
              pathname === '/settings' ? 'bg-white/15 text-white' : 'text-white/40 hover:text-white/80 hover:bg-white/8'
            }`}
            aria-label="Settings"
          >
            <Settings size={18} />
          </Link>
        </div>
      )}

      {/* History — only when expanded */}
      {expanded && (
        <div className="flex-1 overflow-y-auto px-2 mt-1 flex flex-col gap-3 pb-2" style={{ scrollbarWidth: 'none' }}>
          {groups.length === 0 && (
            <div className="flex flex-col items-center justify-center flex-1 gap-2 py-8">
              <MessageSquare size={24} className="text-white/15" />
              <span className="text-white/30 text-xs text-center">No chats yet</span>
            </div>
          )}
          {groups.map(({ label, items }) => (
            <div key={label}>
              <p className="text-[10px] font-bold text-white/25 uppercase tracking-widest px-2 py-1">{label}</p>
              <div className="flex flex-col gap-0.5">
                {items.map(s => {
                  const isActive = s.id === activeId
                  return (
                    <button
                      key={s.id}
                      onClick={() => handleSessionClick(s.id)}
                      className={`w-full text-left px-2.5 py-2 rounded-xl transition-all duration-150 group ${
                        isActive
                          ? 'bg-white/15 text-white'
                          : 'text-white/50 hover:text-white/85 hover:bg-white/8'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <span className={`text-[9px] font-black px-1 py-0.5 rounded shrink-0 ${
                          isActive ? 'bg-white/20 text-white/80' : 'bg-white/8 text-white/30'
                        }`}>
                          {MODE_ICON[s.mode] ?? 'O'}
                        </span>
                        <span className="text-xs font-medium truncate leading-snug">
                          {truncate(s.title, 28)}
                        </span>
                      </div>
                    </button>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Bottom nav */}
      <div className={`shrink-0 px-2 pb-3 flex flex-col gap-0.5 ${expanded ? '' : 'mt-auto'}`}>
        {expanded ? (
          <>
            <Link
              href="/settings"
              className={`flex items-center gap-3 px-2.5 py-2 rounded-xl transition-all whitespace-nowrap text-sm font-medium ${
                pathname === '/settings' ? 'bg-white/15 text-white' : 'text-white/50 hover:text-white/85 hover:bg-white/8'
              }`}
            >
              <Settings size={16} className="shrink-0" />
              Settings
            </Link>
            <div className="flex items-center gap-2 px-2.5 py-2 rounded-xl hover:bg-white/8 transition-colors cursor-default">
              <Avatar email={email} size="sm" />
              <span className="text-white/60 text-xs truncate flex-1">{email}</span>
              <button
                onClick={handleSignOut}
                className="text-white/30 hover:text-white/80 transition-colors"
                aria-label="Sign out"
              >
                <LogOut size={14} />
              </button>
            </div>
          </>
        ) : (
          <button
            onClick={handleSignOut}
            className="w-9 h-9 flex items-center justify-center text-white/30 hover:text-white/80 transition-colors rounded-xl hover:bg-white/8 mx-auto"
            aria-label="Sign out"
          >
            <LogOut size={18} />
          </button>
        )}
      </div>
    </aside>
  )
}
