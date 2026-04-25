'use client'
import { useState } from 'react'
import Link from 'next/link'
import { supabase } from '@/lib/supabase'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'

export default function ForgotPasswordPage() {
  const [email, setEmail]     = useState('')
  const [sent, setSent]       = useState(false)
  const [error, setError]     = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    const { error: err } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/auth/reset-password`,
    })
    setLoading(false)
    if (err) { setError(err.message); return }
    setSent(true)
  }

  return (
    <div className="min-h-screen bg-cream flex items-center justify-center px-4">
      <div className="w-full max-w-sm flex flex-col items-center gap-8">
        <div className="flex flex-col items-center gap-3">
          <div className="w-12 h-12 bg-black rounded-2xl flex items-center justify-center">
            <span className="text-cream font-black text-lg">H</span>
          </div>
          <h1 className="font-black text-2xl text-black tracking-tight">Reset password</h1>
          <p className="text-warm-gray text-sm text-center max-w-xs">
            Enter your email and we'll send a reset link.
          </p>
        </div>

        {sent ? (
          <div className="w-full flex flex-col items-center gap-6">
            <div className="w-full bg-denim/10 border border-denim/30 rounded-2xl px-4 py-4 text-sm text-denim font-semibold text-center">
              Reset link sent — check your inbox.
            </div>
            <Link href="/auth/login" className="text-sm text-denim font-semibold hover:underline">
              Back to sign in
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="w-full flex flex-col gap-6">
            <Input
              label="Email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
              error={error}
              required
              autoComplete="email"
            />
            <Button type="submit" loading={loading} className="w-full py-3 rounded-2xl">
              Send reset link
            </Button>
            <Link href="/auth/login" className="text-sm text-warm-gray text-center hover:text-denim transition-colors">
              ← Back to sign in
            </Link>
          </form>
        )}
      </div>
    </div>
  )
}
