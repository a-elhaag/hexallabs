'use client'
import { useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
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
      className="w-full max-w-4xl mx-auto px-6 py-1.5"
      style={{ opacity: 0 }}
    >
      {isUser ? (
        <div className="flex justify-end">
          <div
            className="max-w-[75%] px-4 py-3 text-sm leading-relaxed bg-denim text-white rounded-3xl rounded-br-lg"
            style={{ wordBreak: 'break-word', whiteSpace: 'pre-wrap' }}
          >
            {msg.content}
          </div>
        </div>
      ) : (
        <div className="text-sm leading-relaxed text-[#2c2c2c]">
          {msg.model && (
            <p className="text-[10px] font-black text-warm-gray/70 uppercase tracking-widest mb-2">
              {MODEL_DISPLAY[msg.model] ?? msg.model}
            </p>
          )}
          <ReactMarkdown
            components={{
              p:      ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
              strong: ({ children }) => <strong className="font-bold">{children}</strong>,
              em:     ({ children }) => <em className="italic">{children}</em>,
              code:   ({ children, className }) => {
                const isBlock = !!className
                return isBlock
                  ? <code className="text-xs font-mono">{children}</code>
                  : <code className="bg-[#2c2c2c]/8 px-1 py-0.5 rounded-md text-xs font-mono">{children}</code>
              },
              pre:    ({ children }) => <pre className="bg-[#2c2c2c]/8 rounded-xl p-3 overflow-x-auto text-xs font-mono my-2">{children}</pre>,
              ul:     ({ children }) => <ul className="list-disc pl-4 mb-2 space-y-0.5">{children}</ul>,
              ol:     ({ children }) => <ol className="list-decimal pl-4 mb-2 space-y-0.5">{children}</ol>,
              li:     ({ children }) => <li>{children}</li>,
              h1:     ({ children }) => <h1 className="font-black text-base mb-1">{children}</h1>,
              h2:     ({ children }) => <h2 className="font-bold text-sm mb-1">{children}</h2>,
              h3:     ({ children }) => <h3 className="font-semibold text-sm mb-1">{children}</h3>,
              table:  ({ children }) => <div className="overflow-x-auto my-3"><table className="w-full text-xs border-collapse">{children}</table></div>,
              thead:  ({ children }) => <thead className="bg-[#2c2c2c]/8">{children}</thead>,
              tbody:  ({ children }) => <tbody>{children}</tbody>,
              tr:     ({ children }) => <tr className="border-b border-warm-gray/20">{children}</tr>,
              th:     ({ children }) => <th className="px-3 py-2 text-left font-bold text-[#2c2c2c]">{children}</th>,
              td:     ({ children }) => <td className="px-3 py-2 text-[#2c2c2c]">{children}</td>,
            }}
          >
            {msg.content}
          </ReactMarkdown>
          {msg.isStreaming && <StreamingCursor />}
        </div>
      )}
    </div>
  )
}
