// components/chat/ChatWindow.tsx
'use client'
import { useEffect, useRef, useState, useCallback } from 'react'
import { v4 as uuidv4 } from 'uuid'
import { ChatMessage, Mode, ModelName, ScoutMode } from '@/lib/types'
import { buildQueryRequest, improveQuery } from '@/lib/api'
import { streamQuery } from '@/lib/sse'
import { Message } from './Message'
import { CouncilGrid } from './CouncilGrid'
import { ChatInput } from './ChatInput'

const MODE_LABEL: Record<Mode, string> = {
  oracle: 'Oracle', council: 'The Council', relay: 'The Relay', workflow: 'Workflow',
}

// A "turn" is either a single ChatMessage (oracle/relay) or a group (council)
type Turn =
  | { type: 'single'; msg: ChatMessage }
  | { type: 'council'; msgs: ChatMessage[] }

function ModeHeader({ mode, models }: { mode: Mode; models: ModelName[] }) {
  return (
    <div className="h-12 flex items-center px-5 border-b border-warm-gray/15 bg-cream/90 backdrop-blur-sm shrink-0">
      <span className="font-black text-sm text-[#2c2c2c] tracking-tight">{MODE_LABEL[mode]}</span>
      {mode === 'council' && models.length > 0 && (
        <div className="ml-3 flex gap-1">
          {models.map(m => (
            <span key={m} className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#2c2c2c]/8 text-warm-gray">
              {m}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

export function ChatWindow() {
  const [turns, setTurns]         = useState<Turn[]>([])
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
  }, [turns])

  // For oracle/relay: append delta to single message by id
  const appendDeltaById = useCallback((id: string, delta: string) => {
    setTurns(prev => prev.map(turn => {
      if (turn.type === 'single' && turn.msg.id === id) {
        return { ...turn, msg: { ...turn.msg, content: turn.msg.content + delta } }
      }
      return turn
    }))
  }, [])

  // For council: append delta to a model card by hex (= ModelName)
  const appendDeltaByHex = useCallback((hex: string, delta: string) => {
    setTurns(prev => prev.map(turn => {
      if (turn.type !== 'council') return turn
      const updated = turn.msgs.map(m =>
        m.model === hex ? { ...m, content: m.content + delta } : m
      )
      return { ...turn, msgs: updated }
    }))
  }, [])

  function stopGeneration() {
    abortRef.current?.abort()
    setStreaming(false)
    setTurns(prev => prev.map(turn => {
      if (turn.type === 'single') {
        return { ...turn, msg: { ...turn.msg, isStreaming: false } }
      }
      return { ...turn, msgs: turn.msgs.map(m => ({ ...m, isStreaming: false })) }
    }))
  }

  async function send(query: string) {
    if (streaming) return

    if (query.length > 30) {
      improveQuery(query)
        .then(r => { if (r.improved_query && r.improved_query !== query) setForgeHint(r.improved_query) })
        .catch(() => {})
    }

    setHasSent(true)
    setForgeHint(null)

    const userTurn: Turn = { type: 'single', msg: { id: uuidv4(), role: 'user', content: query } }

    const effectiveModels = mode === 'oracle'
      ? (models.length === 1 ? models : ['Apex' as ModelName])
      : models.length > 0 ? models : ['Apex' as ModelName]

    const isCouncil = mode === 'council'

    let assistantTurn: Turn
    let singleId = ''

    if (isCouncil) {
      assistantTurn = {
        type: 'council',
        msgs: effectiveModels.map(m => ({
          id: uuidv4(),
          role: 'assistant' as const,
          content: '',
          model: m,
          isStreaming: true,
        })),
      }
    } else {
      singleId = uuidv4()
      assistantTurn = {
        type: 'single',
        msg: {
          id: singleId,
          role: 'assistant',
          content: '',
          isStreaming: true,
          model: mode === 'oracle' ? effectiveModels[0] : undefined,
        },
      }
    }

    setTurns(prev => [...prev, userTurn, assistantTurn])
    setStreaming(true)

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
      setTurns(prev => {
        const last = prev[prev.length - 1]
        if (!last) return prev
        if (last.type === 'single') {
          return [...prev.slice(0, -1), { ...last, msg: { ...last.msg, content: 'Not signed in — please sign in to chat.', isStreaming: false } }]
        }
        return prev
      })
      setStreaming(false)
      return
    }

    try {
      abortRef.current = new AbortController()

      await streamQuery(url, token, body, {
        token: (d) => {
          if (isCouncil) {
            appendDeltaByHex(d.hex, d.delta)
          } else {
            appendDeltaById(singleId, d.delta)
          }
        },
        synth_token: (d) => appendDeltaById(singleId, d.delta),
        hex_done: (d) => {
          if (isCouncil) {
            setTurns(prev => prev.map(turn => {
              if (turn.type !== 'council') return turn
              return { ...turn, msgs: turn.msgs.map(m => m.model === d.hex ? { ...m, isStreaming: false } : m) }
            }))
          }
        },
        done: () => {
          setTurns(prev => prev.map(turn => {
            if (turn.type === 'single') return { ...turn, msg: { ...turn.msg, isStreaming: false } }
            return { ...turn, msgs: turn.msgs.map(m => ({ ...m, isStreaming: false })) }
          }))
          setStreaming(false)
        },
        error: (d) => {
          setTurns(prev => {
            const last = prev[prev.length - 1]
            if (!last) return prev
            if (last.type === 'single') {
              return [...prev.slice(0, -1), { ...last, msg: { ...last.msg, content: `Error: ${d.message}`, isStreaming: false } }]
            }
            return prev
          })
          setStreaming(false)
        },
      }, abortRef.current.signal)
    } catch (err) {
      setTurns(prev => {
        const last = prev[prev.length - 1]
        if (!last) return prev
        if (last.type === 'single') {
          const msg = err instanceof Error ? `Error: ${err.message}` : 'Error'
          return [...prev.slice(0, -1), { ...last, msg: { ...last.msg, content: msg, isStreaming: false } }]
        }
        return prev
      })
      setStreaming(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      <ModeHeader mode={mode} models={models} />

      {forgeHint && (
        <div className="mx-5 my-2 px-4 py-2.5 bg-denim/8 border border-denim/20 rounded-2xl flex items-center gap-3 text-xs">
          <span className="text-denim font-bold shrink-0">Forge suggests:</span>
          <span className="text-[#2c2c2c] flex-1 truncate">{forgeHint}</span>
          <button onClick={() => { send(forgeHint); setForgeHint(null) }} className="text-denim font-bold hover:underline shrink-0">Use it</button>
          <button onClick={() => setForgeHint(null)} className="text-warm-gray hover:text-[#2c2c2c] shrink-0">✕</button>
        </div>
      )}

      <div className="flex-1 overflow-y-auto py-6 flex flex-col gap-0.5 relative">
        <div className={`absolute inset-0 flex flex-col items-center justify-center gap-4 text-center px-6 pointer-events-none ${hasSent ? 'hidden' : ''}`}>
          <div className="w-12 h-12 bg-[#2c2c2c] rounded-3xl flex items-center justify-center shadow-lg">
            <span className="text-cream font-black text-lg">H</span>
          </div>
          <div className="flex flex-col gap-1">
            <p className="font-black text-xl text-[#2c2c2c]">Ask anything</p>
            <p className="text-sm text-warm-gray">Press <kbd className="px-1.5 py-0.5 bg-[#2c2c2c]/8 rounded-md text-xs font-mono">/</kbd> to switch modes</p>
          </div>
        </div>

        {turns.map((turn, i) =>
          turn.type === 'single'
            ? <Message key={turn.msg.id} msg={turn.msg} />
            : <CouncilGrid key={turn.msgs[0]?.id ?? i} messages={turn.msgs} />
        )}
        <div ref={bottomRef} />
      </div>

      <ChatInput
        onSend={send}
        onStop={stopGeneration}
        streaming={streaming}
        mode={mode}
        onMode={setMode}
        models={models}
        onModels={setModels}
        primal={primal}
        onPrimal={setPrimal}
        scout={scout}
        onScout={setScout}
        onClear={() => { setTurns([]); setHasSent(false) }}
      />
    </div>
  )
}
