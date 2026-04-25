// lib/sse.ts
// SSE via fetch POST — EventSource only supports GET, so we use fetch+ReadableStream.

import type { SseEventMap } from './types'

type Handler<K extends keyof SseEventMap> = (data: SseEventMap[K]) => void

type Handlers = {
  [K in keyof SseEventMap]?: Handler<K>
} & {
  _error?: (err: Error) => void
}

export async function streamQuery(
  url: string,
  token: string,
  body: string,
  handlers: Handlers,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
    },
    body,
    signal,
  })

  if (!res.ok) {
    handlers._error?.(new Error(`Query failed: ${res.status}`))
    return
  }

  const reader = res.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const parts = buffer.split('\n\n')
    buffer = parts.pop() ?? ''

    for (const chunk of parts) {
      if (!chunk.trim() || chunk.startsWith(':')) continue  // heartbeat

      let eventName = 'message'
      let dataLine = ''

      for (const line of chunk.split('\n')) {
        if (line.startsWith('event:')) eventName = line.slice(6).trim()
        else if (line.startsWith('data:')) dataLine = line.slice(5).trim()
      }

      try {
        const parsed = JSON.parse(dataLine)
        const handler = handlers[eventName as keyof SseEventMap]
        if (handler) (handler as Handler<keyof SseEventMap>)(parsed)
      } catch {
        // malformed chunk — skip
      }
    }
  }
}
