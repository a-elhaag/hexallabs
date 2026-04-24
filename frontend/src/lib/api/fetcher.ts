"use client";

import { createClient } from "~/lib/supabase/client";
import { env } from "~/env";
import type { SseEvent } from "./types";

export class AuthRequiredError extends Error {
  constructor() {
    super("Authentication required");
    this.name = "AuthRequiredError";
  }
}

async function getAccessToken(): Promise<string> {
  const supabase = createClient();
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) throw new AuthRequiredError();
  return session.access_token;
}

export async function authedFetch(
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  let token = await getAccessToken();

  const makeRequest = (t: string) =>
    fetch(`${env.NEXT_PUBLIC_BACKEND_URL}${path}`, {
      ...init,
      headers: {
        ...init.headers,
        Authorization: `Bearer ${t}`,
        "Content-Type": "application/json",
      },
    });

  let res = await makeRequest(token);

  if (res.status === 401) {
    const supabase = createClient();
    const { data, error } = await supabase.auth.refreshSession();
    if (error ?? !data.session) {
      if (typeof window !== "undefined") {
        window.location.assign("/login");
      }
      throw new AuthRequiredError();
    }
    token = data.session.access_token;
    res = await makeRequest(token);
    if (res.status === 401) {
      if (typeof window !== "undefined") {
        window.location.assign("/login");
      }
      throw new AuthRequiredError();
    }
  }

  return res;
}

export async function* streamSSE<T = unknown>(
  path: string,
  body: unknown,
  signal?: AbortSignal,
): AsyncGenerator<SseEvent<T>> {
  const res = await authedFetch(path, {
    method: "POST",
    body: JSON.stringify(body),
    signal,
  });

  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  }

  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      const parts = buffer.split("\n\n");
      buffer = parts.pop() ?? "";

      for (const part of parts) {
        const lines = part.split("\n");
        let event = "";
        let data = "";

        for (const line of lines) {
          if (line.startsWith("event: ")) {
            event = line.slice(7).trim();
          } else if (line.startsWith("data: ")) {
            data = line.slice(6).trim();
          }
        }

        if (event && data) {
          try {
            yield { event, data: JSON.parse(data) as T };
          } catch {
            // skip malformed frame
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
