// proxy.ts — Next.js 16 auth guard (renamed from middleware.ts)
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

const PUBLIC_PATHS = ['/', '/auth/login', '/auth/signup']

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl
  if (PUBLIC_PATHS.some(p => pathname === p)) return NextResponse.next()

  // Supabase v2 cookie name for project uthyhzzdwisqwkusdizn
  const authCookie = request.cookies.get('sb-uthyhzzdwisqwkusdizn-auth-token')

  if (!authCookie?.value) {
    return NextResponse.redirect(new URL('/auth/login', request.url))
  }
  return NextResponse.next()
}

export const config = {
  matcher: ['/chat/:path*', '/settings/:path*'],
}
