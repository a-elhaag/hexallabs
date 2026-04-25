'use client'
import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { supabase } from '@/lib/supabase'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'

export default function ResetPasswordPage() {
  const router = useRouter()
  const [password, setPassword] = useState('')
  const [confirm, setConfirm]   = useState('')
  const [error, setError]       = useState('')
  const [loading, setLoading]   = useState(false)
  const [ready, setReady]       = useState(false)

  useEffect(() => {
    // Supabase sets session from hash fragment on this page
    supabase.auth.onAuthStateChange((event) => {
      if (event === 'PASSWORD_RECOVERY') setReady(true)
    })
  }, [])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    if (password !== confirm) { setError('Passwords do not match.'); return }
    if (password.length < 8)  { setError('Password must be at least 8 characters.'); return }
    setLoading(true)
    const { error: err } = await supabase.auth.updateUser({ password })
    setLoading(false)
    if (err) { setError(err.message); return }
    router.push('/auth/login?reset=1')
  }

  if (!ready) {
    return (
      <div className="min-h-screen bg-cream flex items-center justify-center px-4">
        <p className="text-warm-gray text-sm">Verifying reset link…</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-cream flex items-center justify-center px-4">
      <div className="w-full max-w-sm flex flex-col items-center gap-8">
        <div className="flex flex-col items-center gap-3">
          <div className="w-12 h-12 bg-black rounded-2xl flex items-center justify-center">
            <span className="text-cream font-black text-lg">H</span>
          </div>
          <h1 className="font-black text-2xl text-black tracking-tight">New password</h1>
          <p className="text-warm-gray text-sm">Choose a new password for your account.</p>
        </div>

        <form onSubmit={handleSubmit} className="w-full flex flex-col gap-6">
          <Input
            label="New password"
            type="password"
            placeholder="Min. 8 characters"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
            minLength={8}
            autoComplete="new-password"
          />
          <Input
            label="Confirm password"
            type="password"
            placeholder="••••••••"
            value={confirm}
            onChange={e => setConfirm(e.target.value)}
            error={error}
            required
            autoComplete="new-password"
          />
          <Button type="submit" loading={loading} className="w-full py-3 rounded-2xl">
            Set new password
          </Button>
        </form>
      </div>
    </div>
  )
}
