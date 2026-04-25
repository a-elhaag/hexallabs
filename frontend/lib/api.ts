// lib/api.ts
import { getToken } from './auth'
import type { ForgeResponse, QueryRequest, QuotaStatus } from './types'

const BASE = process.env.NEXT_PUBLIC_API_URL!

async function authHeaders(): Promise<HeadersInit> {
  const token = await getToken()
  if (!token) throw new Error('Not authenticated')
  return { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }
}

export async function improveQuery(query: string): Promise<ForgeResponse> {
  const res = await fetch(`${BASE}/api/prompt-forge`, {
    method: 'POST',
    headers: await authHeaders(),
    body: JSON.stringify({ query }),
  })
  if (!res.ok) throw new Error(`Prompt Forge failed: ${res.status}`)
  return res.json()
}

export async function getQuota(): Promise<QuotaStatus> {
  const res = await fetch(`${BASE}/api/quota`, {
    headers: await authHeaders(),
  })
  if (!res.ok) throw new Error(`Quota fetch failed: ${res.status}`)
  return res.json()
}

export async function buildQueryRequest(req: QueryRequest): Promise<{ url: string; token: string; body: string }> {
  const token = await getToken()
  if (!token) throw new Error('Not authenticated')
  return {
    url: `${BASE}/api/query`,
    token,
    body: JSON.stringify(req),
  }
}
