'use client'
import { useState, useEffect, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { supabase } from '@/lib/supabase'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'

function LoginForm() {
  const router       = useRouter()
  const params       = useSearchParams()
  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const [error, setError]       = useState('')
  const [success, setSuccess]   = useState('')
  const [loading, setLoading]   = useState(false)

  useEffect(() => {
    if (params.get('confirmed')) setSuccess('Account created! Check your email to confirm, then sign in.')
    if (params.get('reset'))     setSuccess('Password reset email sent — check your inbox.')
  }, [params])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setSuccess('')
    setLoading(true)
    const { error: err } = await supabase.auth.signInWithPassword({ email, password })
    setLoading(false)
    if (err) {
      if (err.message.toLowerCase().includes('invalid login')) {
        setError('Wrong email or password.')
      } else if (err.message.toLowerCase().includes('email not confirmed')) {
        setError('Please confirm your email first — check your inbox.')
      } else {
        setError(err.message)
      }
      return
    }
    router.refresh()
    router.push('/chat')
  }

  return (
    <div className="min-h-screen bg-cream flex items-center justify-center px-4">
      <div className="w-full max-w-sm flex flex-col items-center gap-8">
        <div className="flex flex-col items-center gap-3">
          <div className="w-12 h-12 bg-black rounded-2xl flex items-center justify-center">
            <span className="text-cream font-black text-lg">H</span>
          </div>
          <h1 className="font-black text-2xl text-black tracking-tight">Welcome back</h1>
          <p className="text-warm-gray text-sm">Sign in to HexalLabs</p>
        </div>

        {success && (
          <div className="w-full bg-denim/10 border border-denim/30 rounded-2xl px-4 py-3 text-sm text-denim font-semibold text-center">
            {success}
          </div>
        )}

        <form onSubmit={handleSubmit} className="w-full flex flex-col gap-6">
          <Input
            label="Email"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={e => setEmail(e.target.value)}
            required
            autoComplete="email"
          />
          <div className="flex flex-col gap-1">
            <Input
              label="Password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={e => setPassword(e.target.value)}
              error={error}
              required
              autoComplete="current-password"
            />
            <div className="flex justify-end mt-1">
              <Link href="/auth/forgot-password" className="text-xs text-warm-gray hover:text-denim transition-colors">
                Forgot password?
              </Link>
            </div>
          </div>
          <Button type="submit" loading={loading} className="w-full py-3 mt-2 rounded-2xl">
            Sign in
          </Button>
        </form>

        <p className="text-sm text-warm-gray">
          No account?{' '}
          <Link href="/auth/signup" className="text-denim font-semibold hover:underline">
            Sign up
          </Link>
        </p>
      </div>
    </div>
  )
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  )
}
