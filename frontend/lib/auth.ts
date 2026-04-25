// lib/auth.ts
import { supabase } from './supabase'

export async function getToken(): Promise<string | null> {
  const { data } = await supabase.auth.getSession()
  return data.session?.access_token ?? null
}

export async function getUser() {
  const { data } = await supabase.auth.getUser()
  return data.user
}

export async function signOut() {
  await supabase.auth.signOut()
}
