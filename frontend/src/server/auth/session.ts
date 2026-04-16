/**
 * Helper: get the current session user from a Next.js API route.
 * Returns null if unauthenticated — callers should 401.
 */
import { auth } from "~/server/auth";

export async function getSessionUser(): Promise<{ id: string; name?: string | null; email?: string | null } | null> {
  const session = await auth();
  if (!session?.user?.id) return null;
  return session.user;
}
