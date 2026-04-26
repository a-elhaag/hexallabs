// components/chat/ChatWindow.tsx
'use client'
import { useEffect, useRef, useState, useCallback } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { v4 as uuidv4 } from 'uuid'
import { ChatMessage, Mode, ModelName, ScoutMode } from '@/lib/types'
import { buildQueryRequest, improveQuery } from '@/lib/api'
import { streamQuery } from '@/lib/sse'
import { getSessionMessages } from '@/lib/db'
import { Message } from './Message'
import { CouncilGrid } from './CouncilGrid'
import { ChatInput } from './ChatInput'
import { ScoutSearchBubble, ScoutResult } from './ScoutSearchBubble'

// A "turn" is either a single ChatMessage (oracle/relay) or a group (council)
type Turn =
  | { type: 'single'; msg: ChatMessage; scout?: ScoutResult }
  | { type: 'council'; msgs: ChatMessage[]; scout?: ScoutResult }


export function ChatWindow() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const [turns, setTurns]         = useState<Turn[]>([])
  const [mode, setMode]           = useState<Mode>('oracle')
  const [models, setModels]       = useState<ModelName[]>(['Apex'])
  const [primal, setPrimal]       = useState(false)
  const [scout, setScout]         = useState<ScoutMode>('off')
  const [streaming, setStreaming] = useState(false)
  const [forgeHint, setForgeHint] = useState<string | null>(null)
  const [hasSent, setHasSent]     = useState(false)
  const [loadingSession, setLoadingSession] = useState(false)
  const bottomRef                 = useRef<HTMLDivElement>(null)
  const abortRef                  = useRef<AbortController | null>(null)
  const sessionIdRef              = useRef<string | null>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [turns])

  // Load session from ?session= param, or reset for ?new=1
  useEffect(() => {
    const sessionId = searchParams.get('session')
    const isNew = searchParams.get('new') === '1'

    if (isNew || (!sessionId && !isNew)) {
      abortRef.current?.abort()
      setStreaming(false)
      setTurns([])
      setHasSent(false)
      setForgeHint(null)
      sessionIdRef.current = null
      return
    }

    if (!sessionId) return

    // URL just caught up to an in-progress session — don't reload
    if (sessionIdRef.current === sessionId) return

    abortRef.current?.abort()
    setStreaming(false)
    setLoadingSession(true)
    setTurns([])
    setHasSent(false)

    getSessionMessages(sessionId)
      .then(messages => {
        const loaded: Turn[] = messages
          .filter(m => m.content?.trim())
          .map(m => ({
            type: 'single' as const,
            msg: {
              id: uuidv4(),
              role: m.role === 'model' ? 'assistant' : m.role as 'user' | 'assistant',
              content: m.content,
              model: m.model as ModelName | undefined,
            },
          }))
        if (loaded.length > 0) {
          setTurns(loaded)
          setHasSent(true)
        }
      })
      .catch(() => {})
      .finally(() => setLoadingSession(false))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams.get('session'), searchParams.get('new')])

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
    const isRelay = mode === 'relay'
    const isWorkflow = mode === 'workflow'

    // Relay needs exactly 2 models; fall back to Apex+Swift if not configured
    const relayChain: [ModelName, ModelName] = isRelay
      ? [effectiveModels[0] ?? 'Apex', effectiveModels[1] ?? 'Swift']
      : ['Apex', 'Swift']

    // Workflow: build nodes from selected models (or default Swift→Apex chain)
    const workflowModels = effectiveModels.length >= 2
      ? effectiveModels
      : ['Swift', 'Apex'] as ModelName[]
    const workflowNodes = isWorkflow
      ? workflowModels.map((m, i) => ({
          id: `node_${i}`,
          type: 'model',
          model: m,
          inputs: i === 0 ? [] : [`node_${i - 1}`],
        }))
      : undefined

    let assistantTurn: Turn
    let singleId = ''
    let relayBId = ''
    let synthId = ''

    if (isCouncil || isWorkflow) {
      const councilModels = isWorkflow ? workflowModels : effectiveModels
      assistantTurn = {
        type: 'council',
        msgs: councilModels.map(m => ({
          id: uuidv4(),
          role: 'assistant' as const,
          content: '',
          model: m,
          isStreaming: true,
        })),
      }
      if (isCouncil) synthId = uuidv4()
    } else {
      singleId = uuidv4()
      assistantTurn = {
        type: 'single',
        msg: {
          id: singleId,
          role: 'assistant',
          content: '',
          isStreaming: true,
          model: isRelay ? relayChain[0] : mode === 'oracle' ? effectiveModels[0] : undefined,
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
        relay_chain: isRelay ? relayChain : undefined,
        workflow_nodes: workflowNodes,
        primal_protocol: primal,
        scout,
        session_id: sessionIdRef.current ?? undefined,
        force_relay_demo: isRelay && searchParams.get('demo') === '1' ? true : undefined,
      }))
    } catch {
      setTurns(prev => {
        const last = prev[prev.length - 1]
        if (!last) return prev
        if (last.type === 'single') {
          return [...prev.slice(0, -1), { ...last, msg: { ...last.msg, content: 'Not signed in — please sign in to chat.', isStreaming: false } }]
        }
        if (last.type === 'council') {
          return [...prev.slice(0, -1), { ...last, msgs: last.msgs.map(m => ({ ...m, isStreaming: false })) }]
        }
        return prev
      })
      setStreaming(false)
      return
    }

    try {
      abortRef.current = new AbortController()

      await streamQuery(url, token, body, {
        session: (d) => {
          if (!sessionIdRef.current) {
            router.replace(`/chat?session=${d.session_id}`)
          }
          sessionIdRef.current = d.session_id
        },
        token: (d) => {
          if (isCouncil || isWorkflow) {
            appendDeltaByHex(d.hex, d.delta)
          } else if (isRelay && relayBId && d.hex === relayChain[1]) {
            appendDeltaById(relayBId, d.delta)
          } else {
            appendDeltaById(singleId, d.delta)
          }
        },
        relay_handoff: (d) => {
          relayBId = uuidv4()
          const bMsg: ChatMessage = {
            id: relayBId,
            role: 'assistant',
            content: '',
            model: d.to as ModelName,
            isStreaming: true,
          }
          setTurns(prev => {
            // mark model A done
            const updated = prev.map(turn => {
              if (turn.type === 'single' && turn.msg.id === singleId) {
                return { ...turn, msg: { ...turn.msg, isStreaming: false } }
              }
              return turn
            })
            return [...updated, { type: 'single' as const, msg: bMsg }]
          })
        },
        synth_start: () => {
          if (isCouncil) {
            const synthMsg: ChatMessage = { id: synthId, role: 'assistant', content: '', model: 'Apex' as ModelName, isStreaming: true }
            setTurns(prev => [...prev, { type: 'single', msg: synthMsg }])
          }
        },
        synth_token: (d) => appendDeltaById(isCouncil ? synthId : singleId, d.delta),
        hex_done: (d) => {
          if (isCouncil || isWorkflow) {
            setTurns(prev => prev.map(turn => {
              if (turn.type !== 'council') return turn
              return { ...turn, msgs: turn.msgs.map(m => m.model === d.hex ? { ...m, isStreaming: false } : m) }
            }))
          }
        },
        tool_call: () => {
          setTurns(prev => {
            const last = prev[prev.length - 1]
            if (!last) return prev
            return [...prev.slice(0, -1), { ...last, scout: { summary: '', urls: [], result_count: 0, pending: true } }]
          })
        },
        tool_result: (d) => {
          setTurns(prev => {
            const last = prev[prev.length - 1]
            if (!last) return prev
            return [...prev.slice(0, -1), { ...last, scout: { summary: d.summary, urls: d.urls, result_count: d.result_count, error: d.error, pending: false } }]
          })
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
            if (last.type === 'council') {
              return [...prev.slice(0, -1), { ...last, msgs: last.msgs.map(m => ({ ...m, isStreaming: false })) }]
            }
            return prev
          })
          setStreaming(false)
        },
        _error: (err) => {
          setTurns(prev => {
            const last = prev[prev.length - 1]
            if (!last) return prev
            if (last.type === 'single') {
              return [...prev.slice(0, -1), { ...last, msg: { ...last.msg, content: `Error: ${err.message}`, isStreaming: false } }]
            }
            if (last.type === 'council') {
              return [...prev.slice(0, -1), { ...last, msgs: last.msgs.map(m => ({ ...m, isStreaming: false })) }]
            }
            return prev
          })
          setStreaming(false)
        },
      }, abortRef.current.signal)
    } catch (err) {
      if (err instanceof Error && err.name !== 'AbortError') {
        setTurns(prev => {
          const last = prev[prev.length - 1]
          if (!last) return prev
          if (last.type === 'single') {
            return [...prev.slice(0, -1), { ...last, msg: { ...last.msg, content: `Error: ${err.message}`, isStreaming: false } }]
          }
          if (last.type === 'council') {
            return [...prev.slice(0, -1), { ...last, msgs: last.msgs.map(m => ({ ...m, isStreaming: false })) }]
          }
          return prev
        })
      }
      setStreaming(false)
    }
  }

  const isDemoMode = searchParams.get('demo') === '1'

  return (
    <div className="flex flex-col h-full">

      {isDemoMode && mode === 'relay' && (
        <div className="mx-5 mt-2 px-4 py-2 bg-denim/10 border border-denim/30 rounded-2xl flex items-center gap-2 text-xs">
          <span className="w-2 h-2 rounded-full bg-denim animate-pulse shrink-0" />
          <span className="text-denim font-bold">Demo mode — handoff fires after ~300 chars</span>
        </div>
      )}

      {forgeHint && (
        <div className="mx-5 my-2 px-4 py-2.5 bg-denim/8 border border-denim/20 rounded-2xl flex items-center gap-3 text-xs">
          <span className="text-denim font-bold shrink-0">Forge suggests:</span>
          <span className="text-[#2c2c2c] flex-1 truncate">{forgeHint}</span>
          <button onClick={() => { send(forgeHint); setForgeHint(null) }} className="text-denim font-bold hover:underline shrink-0">Use it</button>
          <button onClick={() => setForgeHint(null)} className="text-warm-gray hover:text-[#2c2c2c] shrink-0">✕</button>
        </div>
      )}

      <div className="flex-1 overflow-y-auto py-6 flex flex-col gap-0.5 relative">
        {loadingSession && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="w-6 h-6 border-2 border-[#2c2c2c]/20 border-t-[#2c2c2c]/60 rounded-full animate-spin" />
          </div>
        )}
        <div className={`absolute inset-0 flex flex-col items-center justify-center gap-4 text-center px-6 pointer-events-none ${hasSent || loadingSession ? 'hidden' : ''}`}>
          <div className="w-12 h-12 bg-[#2c2c2c] rounded-3xl flex items-center justify-center shadow-lg">
            <span className="text-cream font-black text-lg">H</span>
          </div>
          <div className="flex flex-col gap-1">
            <p className="font-black text-xl text-[#2c2c2c]">Ask anything</p>
            <p className="text-sm text-warm-gray">Press <kbd className="px-1.5 py-0.5 bg-[#2c2c2c]/8 rounded-md text-xs font-mono">/</kbd> to switch modes</p>
          </div>
        </div>

        {turns.map((turn, i) =>
          turn.type === 'single' ? (
            <div key={turn.msg.id}>
              {turn.scout && turn.msg.role === 'assistant' && (
                <ScoutSearchBubble result={turn.scout} />
              )}
              <Message msg={turn.msg} />
            </div>
          ) : (
            <div key={turn.msgs[0]?.id ?? i}>
              {turn.scout && <ScoutSearchBubble result={turn.scout} />}
              <CouncilGrid messages={turn.msgs} />
            </div>
          )
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
      />
    </div>
  )
}
