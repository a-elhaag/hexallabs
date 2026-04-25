// components/chat/ChatWindow.tsx
'use client'
import { useEffect, useRef, useState, useCallback } from 'react'
import { v4 as uuidv4 } from 'uuid'
import { ChatMessage, Mode, ModelName, ScoutMode } from '@/lib/types'
import { buildQueryRequest, improveQuery } from '@/lib/api'
import { streamQuery } from '@/lib/sse'
import { Message } from './Message'
import { ChatInput } from './ChatInput'

function ModeHeader({ mode, models }: { mode: Mode; models: ModelName[] }) {
  const label = mode === 'oracle' ? 'Oracle'
    : mode === 'council' ? 'The Council'
    : mode === 'relay'   ? 'The Relay'
    : 'Workflow'
  return (
    <div className="h-12 flex items-center px-4 border-b border-warm-gray/20 bg-cream/80 backdrop-blur-sm flex-shrink-0">
      <span className="font-black text-sm text-black tracking-tight">{label}</span>
      {mode === 'council' && models.length > 0 && (
        <span className="ml-2 text-xs text-warm-gray font-semibold">
          · {models.join(', ')}
        </span>
      )}
    </div>
  )
}

export function ChatWindow() {
  const [messages, setMessages]   = useState<ChatMessage[]>([])
  const [mode, setMode]           = useState<Mode>('oracle')
  const [models, setModels]       = useState<ModelName[]>(['apex'])
  const [primal, setPrimal]       = useState(false)
  const [scout, setScout]         = useState<ScoutMode>('off')
  const [streaming, setStreaming] = useState(false)
  const [forgeHint, setForgeHint] = useState<string | null>(null)
  const bottomRef                 = useRef<HTMLDivElement>(null)
  const abortRef                  = useRef<AbortController | null>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const appendDelta = useCallback((id: string, delta: string) => {
    setMessages(prev => prev.map(m =>
      m.id === id ? { ...m, content: m.content + delta } : m
    ))
  }, [])

  async function send(query: string) {
    if (streaming) return

    // Forge hint — fire in background, ignore failures
    if (query.length > 30) {
      improveQuery(query)
        .then(r => { if (r.improved_query && r.improved_query !== query) setForgeHint(r.improved_query) })
        .catch(() => {})
    }

    const userMsg: ChatMessage = { id: uuidv4(), role: 'user', content: query }
    const assistantId = uuidv4()
    const assistantMsg: ChatMessage = {
      id: assistantId, role: 'assistant', content: '', isStreaming: true,
      model: mode === 'oracle' ? models[0] : undefined,
    }
    setMessages(prev => [...prev, userMsg, assistantMsg])
    setStreaming(true)
    setForgeHint(null)

    const effectiveModels = mode === 'oracle'
      ? (models.length === 1 ? models : ['apex' as ModelName])
      : models.length > 0 ? models : ['apex' as ModelName]

    try {
      const { url, token, body } = await buildQueryRequest({
        mode,
        query,
        models: effectiveModels,
        primal_protocol: primal,
        scout,
      })

      abortRef.current = new AbortController()

      await streamQuery(url, token, body, {
        token:       (d) => appendDelta(assistantId, d.delta),
        synth_token: (d) => appendDelta(assistantId, d.delta),
        done: () => {
          setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, isStreaming: false } : m))
          setStreaming(false)
        },
        error: (d) => {
          setMessages(prev => prev.map(m =>
            m.id === assistantId ? { ...m, content: `Error: ${d.message}`, isStreaming: false } : m
          ))
          setStreaming(false)
        },
      }, abortRef.current.signal)
    } catch (err) {
      setMessages(prev => prev.map(m =>
        m.id === assistantId
          ? { ...m, content: err instanceof Error ? `Error: ${err.message}` : 'Error', isStreaming: false }
          : m
      ))
      setStreaming(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      <ModeHeader mode={mode} models={models} />

      {forgeHint && (
        <div className="px-4 py-2 bg-denim/10 border-b border-denim/20 flex items-center gap-3 text-xs">
          <span className="text-denim font-semibold">Forge suggests:</span>
          <span className="text-black flex-1 truncate">{forgeHint}</span>
          <button onClick={() => { send(forgeHint); setForgeHint(null) }} className="text-denim font-bold hover:underline">Use it</button>
          <button onClick={() => setForgeHint(null)} className="text-warm-gray hover:text-black">Dismiss</button>
        </div>
      )}

      <div className="flex-1 overflow-y-auto py-4 flex flex-col gap-1 relative">
        {/* Empty state */}
        <div className={`absolute inset-0 flex flex-col items-center justify-center gap-3 text-center px-6 transition-opacity duration-150 pointer-events-none ${messages.length > 0 ? 'opacity-0 invisible' : 'opacity-50 visible'}`}>
          <div className="w-10 h-10 bg-black rounded-2xl flex items-center justify-center">
            <span className="text-cream font-black text-base">H</span>
          </div>
          <p className="font-black text-xl text-black">Ask anything</p>
          <p className="text-sm text-warm-gray">Press / to change mode or select models</p>
        </div>
        {messages.map(m => <Message key={m.id} msg={m} />)}
        <div ref={bottomRef} />
      </div>

      <ChatInput
        onSend={send}
        disabled={streaming}
        mode={mode}
        onMode={setMode}
        models={models}
        onModels={setModels}
        primal={primal}
        onPrimal={setPrimal}
        scout={scout}
        onScout={setScout}
        onClear={() => setMessages([])}
      />
    </div>
  )
}
