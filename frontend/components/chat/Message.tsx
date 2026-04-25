// components/chat/Message.tsx
import { ChatMessage, MODEL_DISPLAY } from '@/lib/types'

export function Message({ msg }: { msg: ChatMessage }) {
  const isUser = msg.role === 'user'
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} px-4 py-1`}>
      <div
        className={`max-w-[75%] px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
          isUser
            ? 'bg-denim text-white rounded-br-sm'
            : 'bg-white border border-warm-gray/30 text-black rounded-bl-sm'
        }`}
      >
        {msg.role === 'assistant' && msg.model && (
          <p className="text-[10px] font-bold text-warm-gray uppercase tracking-widest mb-1">
            {MODEL_DISPLAY[msg.model] ?? msg.model}
          </p>
        )}
        {msg.content}
        {msg.isStreaming && (
          <span className="inline-block w-1.5 h-4 bg-current ml-0.5 animate-pulse align-middle" />
        )}
      </div>
    </div>
  )
}
