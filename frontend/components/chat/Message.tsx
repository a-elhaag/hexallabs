'use client'
import { useEffect, useRef } from 'react'
import { ChatMessage, MODEL_DISPLAY } from '@/lib/types'

function StreamingCursor() {
  return (
    <span
      className="inline-block w-0.75 h-[1em] bg-current rounded-full ml-0.5 align-middle"
      style={{ animation: 'cursorBlink 1s ease-in-out infinite' }}
    />
  )
}

export function Message({ msg }: { msg: ChatMessage }) {
  const isUser = msg.role === 'user'
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    el.style.animation = 'msgIn 0.28s cubic-bezier(0.16,1,0.3,1) both'
  }, [])

  return (
    <div
      ref={ref}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} px-5 py-1.5`}
      style={{ opacity: 0 }}
    >
      {!isUser && (
        <div className="w-7 h-7 rounded-full bg-black flex items-center justify-center shrink-0 mr-2.5 mt-0.5 self-start">
          <span className="text-cream font-black text-[10px]">
            {msg.model ? (MODEL_DISPLAY[msg.model] ?? msg.model)[0] : 'H'}
          </span>
        </div>
      )}

      <div
        className={`max-w-[72%] px-4 py-3 text-sm leading-relaxed ${
          isUser
            ? 'bg-denim text-white rounded-3xl rounded-br-lg'
            : 'bg-white border border-warm-gray/20 text-black rounded-3xl rounded-bl-lg shadow-sm'
        }`}
        style={{ wordBreak: 'break-word', whiteSpace: 'pre-wrap' }}
      >
        {!isUser && msg.model && (
          <p className="text-[10px] font-bold text-warm-gray/70 uppercase tracking-widest mb-1.5">
            {MODEL_DISPLAY[msg.model] ?? msg.model}
          </p>
        )}
        <span>{msg.content}</span>
        {msg.isStreaming && <StreamingCursor />}
      </div>
    </div>
  )
}
