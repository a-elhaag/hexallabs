// lib/db.ts — Direct Supabase queries for sessions & messages
import { supabase } from './supabase'

export interface SessionRow {
  id: string
  title: string | null
  mode: string
  updated_at: string
}

export interface MessageRow {
  id: string
  query_id: string
  role: string
  model: string | null
  content: string
  stage: string | null
  created_at: string
}

export async function getSessions(): Promise<SessionRow[]> {
  const { data: { session } } = await supabase.auth.getSession()
  if (!session) return []

  const { data, error } = await supabase
    .from('sessions')
    .select('id, title, mode, updated_at')
    .order('updated_at', { ascending: false })
    .limit(100)

  if (error) throw error
  return data || []
}

export async function getSessionMessages(sessionId: string): Promise<MessageRow[]> {
  const { data: queries, error: queryError } = await supabase
    .from('queries')
    .select('id')
    .eq('session_id', sessionId)

  if (queryError) throw queryError
  if (!queries || queries.length === 0) return []

  const queryIds = queries.map(q => q.id)

  const { data, error } = await supabase
    .from('messages')
    .select('id, query_id, role, model, content, stage, created_at')
    .in('query_id', queryIds)
    .order('created_at', { ascending: true })

  if (error) throw error
  return data || []
}
