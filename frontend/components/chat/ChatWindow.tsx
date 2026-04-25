// components/chat/ChatWindow.tsx
'use client'
import { useEffect, useRef, useState, useCallback } from 'react'
import { v4 as uuidv4 } from 'uuid'
import { ChatMessage, Mode, ModelName, ScoutMode } from '@/lib/types'
import { buildQueryRequest, improveQuery } from '@/lib/api'
import { streamQuery } from '@/lib/sse'
import { Message } from './Message'
import { ChatInput } from './ChatInput'

const MODE_LABEL: Record<Mode, string> = {
  oracle: 'Oracle', council: 'The Council', relay: 'The Relay', workflow: 'Workflow',
}

function ModeHeader({ mode, models }: { mode: Mode; models: ModelName[] }) {
  return (
    <div className="h-12 flex items-center px-5 border-b border-warm-gray/15 bg-cream/90 backdrop-blur-sm shrink-0">
      <span className="font-black text-sm text-black tracking-tight">{MODE_LABEL[mode]}</span>
      {mode === 'council' && models.length > 0 && (
        <div className="ml-3 flex gap-1">
          {models.map(m => (
            <span key={m} className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-black/8 text-warm-gray">
              {m}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

export function ChatWindow() {
  const [messages, setMessages]   = useState<ChatMessage[]>([])
  const [mode, setMode]           = useState<Mode>('oracle')
  const [models, setModels]       = useState<ModelName[]>(['Apex'])
  const [primal, setPrimal]       = useState(false)
  const [scout, setScout]         = useState<ScoutMode>('off')
  const [streaming, setStreaming] = useState(false)
  const [forgeHint, setForgeHint] = useState<string | null>(null)
  const [hasSent, setHasSent]     = useState(false)
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

    setHasSent(true)
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
      ? (models.length === 1 ? models : ['Apex' as ModelName])
      : models.length > 0 ? models : ['Apex' as ModelName]

    let url: string, token: string, body: string
    try {
      ;({ url, token, body } = await buildQueryRequest({
        mode,
        query,
        models: effectiveModels,
        primal_protocol: primal,
        scout,
      }))
    } catch {
      setMessages(prev => prev.map(m =>
        m.id === assistantId
          ? { ...m, content: 'Not signed in — please sign in to chat.', isStreaming: false }
          : m
      ))
      setStreaming(false)
      return
    }

    try {

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
        <div className="mx-5 my-2 px-4 py-2.5 bg-denim/8 border border-denim/20 rounded-2xl flex items-center gap-3 text-xs">
          <span className="text-denim font-bold shrink-0">Forge suggests:</span>
          <span className="text-black flex-1 truncate">{forgeHint}</span>
          <button onClick={() => { send(forgeHint); setForgeHint(null) }} className="text-denim font-bold hover:underline shrink-0">Use it</button>
          <button onClick={() => setForgeHint(null)} className="text-warm-gray hover:text-black shrink-0">✕</button>
        </div>
      )}

      <div className="flex-1 overflow-y-auto py-6 flex flex-col gap-0.5 relative">
        {/* Empty state — latches off on first send */}
        <div className={`absolute inset-0 flex flex-col items-center justify-center gap-4 text-center px-6 pointer-events-none ${hasSent ? 'hidden' : ''}`}>
          <div className="w-12 h-12 bg-black rounded-3xl flex items-center justify-center shadow-lg">
            <span className="text-cream font-black text-lg">H</span>
          </div>
          <div className="flex flex-col gap-1">
            <p className="font-black text-xl text-black">Ask anything</p>
            <p className="text-sm text-warm-gray">Press <kbd className="px-1.5 py-0.5 bg-black/8 rounded-md text-xs font-mono">/</kbd> to switch modes</p>
          </div>
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
        onClear={() => { setMessages([]); setHasSent(false) }}
      />
    </div>
  )
}
