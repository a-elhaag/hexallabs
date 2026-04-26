// app/settings/page.tsx
'use client'
import { useEffect, useState } from 'react'
import { AppShell } from '@/components/layout/AppShell'
import { getUser } from '@/lib/auth'
import { getQuota } from '@/lib/api'
import type { QuotaStatus } from '@/lib/types'

function formatCountdown(ms: number): string {
  if (ms <= 0) return 'now'
  const totalMinutes = Math.floor(ms / 60000)
  const days    = Math.floor(totalMinutes / 1440)
  const hours   = Math.floor((totalMinutes % 1440) / 60)
  const minutes = totalMinutes % 60
  const parts: string[] = []
  if (days)    parts.push(`${days}d`)
  if (hours)   parts.push(`${hours}h`)
  if (minutes || parts.length === 0) parts.push(`${minutes}m`)
  return parts.join(' ')
}

function ResetCountdown({ resetsAt }: { resetsAt: string }) {
  const target = new Date(resetsAt).getTime()
  const [remaining, setRemaining] = useState(() => target - Date.now())

  useEffect(() => {
    const id = setInterval(() => setRemaining(target - Date.now()), 60000)
    return () => clearInterval(id)
  }, [target])

  return <span>{formatCountdown(remaining)}</span>
}

export default function SettingsPage() {
  const [email, setEmail] = useState('')
  const [quota, setQuota] = useState<QuotaStatus | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    getUser().then(u => setEmail(u?.email ?? ''))
    const fetchQuota = () => getQuota().then(setQuota).catch(() => setError('Could not load quota'))
    fetchQuota()
    window.addEventListener('focus', fetchQuota)
    return () => window.removeEventListener('focus', fetchQuota)
  }, [])

  return (
    <AppShell>
      <div className="flex-1 overflow-y-auto px-8 py-10 max-w-2xl">
        <h1 className="font-black text-2xl text-black mb-8 tracking-tight">Settings</h1>

        <section className="mb-10">
          <h2 className="font-bold text-xs text-warm-gray uppercase tracking-widest mb-4">Account</h2>
          <div className="bg-white border border-warm-gray/20 rounded-xl p-5 flex flex-col gap-3">
            <div>
              <p className="text-xs text-warm-gray font-semibold mb-1">Email</p>
              <p className="text-sm font-semibold text-black">{email || '—'}</p>
            </div>
          </div>
        </section>

        <section className="mb-10">
          <h2 className="font-bold text-xs text-warm-gray uppercase tracking-widest mb-4">Usage</h2>
          {error && <p className="text-sm text-red-600 mb-3">{error}</p>}
          {quota && (
            <div className="bg-white border border-warm-gray/20 rounded-xl p-5 flex flex-col gap-4">
              <div>
                <div className="flex justify-between text-xs mb-2">
                  <span className="font-semibold text-warm-gray">Budget used</span>
                  <span className="font-bold text-black">{quota.percentage_used.toFixed(1)}%</span>
                </div>
                <div className="h-2 bg-warm-gray/20 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-denim rounded-full transition-all duration-500"
                    style={{ width: `${Math.min(quota.percentage_used, 100)}%` }}
                  />
                </div>
              </div>
              {quota.resets_at && (
                <p className="text-xs text-warm-gray">
                  Resets: <ResetCountdown resetsAt={quota.resets_at} />
                </p>
              )}
            </div>
          )}
        </section>

      </div>
    </AppShell>
  )
}
