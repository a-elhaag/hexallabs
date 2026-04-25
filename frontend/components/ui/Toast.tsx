// components/ui/Toast.tsx
'use client'
import { useEffect, useState } from 'react'
import { X } from 'lucide-react'

interface ToastProps {
  message: string
  type?: 'success' | 'error' | 'info'
  onDismiss: () => void
}

export function Toast({ message, type = 'info', onDismiss }: ToastProps) {
  const [visible, setVisible] = useState(true)

  useEffect(() => {
    const t = setTimeout(() => {
      setVisible(false)
      setTimeout(onDismiss, 300)
    }, 4000)
    return () => clearTimeout(t)
  }, [onDismiss])

  const colors = {
    success: 'bg-denim text-white',
    error:   'bg-[#2c2c2c] text-cream border border-red-500',
    info:    'bg-[#2c2c2c] text-cream',
  }

  return (
    <div
      aria-live="polite"
      className={`fixed bottom-6 right-6 z-50 flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg text-sm font-semibold transition-all duration-300 [transition-timing-function:cubic-bezier(0.16,1,0.3,1)] ${colors[type]} ${visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2'}`}
    >
      <span>{message}</span>
      <button onClick={() => { setVisible(false); setTimeout(onDismiss, 300) }} aria-label="Dismiss">
        <X size={14} />
      </button>
    </div>
  )
}
