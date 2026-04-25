'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { supabase } from '@/lib/supabase'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'

export default function SignupPage() {
  const router = useRouter()
  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const [error, setError]       = useState('')
  const [loading, setLoading]   = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    const { data, error: err } = await supabase.auth.signUp({ email, password })
    setLoading(false)

    if (err) {
      if (err.message.toLowerCase().includes('already registered') || err.message.toLowerCase().includes('user already')) {
        setError('Account already exists.')
      } else {
        setError(err.message)
      }
      return
    }

    // If email confirmation is required, session will be null
    if (!data.session) {
      router.push('/auth/login?confirmed=1')
      return
    }

    // Email confirmation disabled — logged in immediately
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
          <h1 className="font-black text-2xl text-black tracking-tight">Create account</h1>
          <p className="text-warm-gray text-sm">Join HexalLabs</p>
        </div>

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
          <Input
            label="Password"
            type="password"
            placeholder="Min. 8 characters"
            value={password}
            onChange={e => setPassword(e.target.value)}
            error={error}
            required
            minLength={8}
            autoComplete="new-password"
          />
          {error === 'Account already exists.' && (
            <p className="text-sm text-warm-gray -mt-2">
              <Link href="/auth/login" className="text-denim font-semibold hover:underline">Sign in instead →</Link>
            </p>
          )}
          <Button type="submit" loading={loading} className="w-full py-3 mt-2 rounded-2xl">
            Create account
          </Button>
        </form>

        <p className="text-sm text-warm-gray">
          Already have an account?{' '}
          <Link href="/auth/login" className="text-denim font-semibold hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
