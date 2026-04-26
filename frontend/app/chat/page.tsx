// app/chat/page.tsx
import { Suspense } from 'react'
import { AppShell } from '@/components/layout/AppShell'
import { ChatWindow } from '@/components/chat/ChatWindow'

export default function ChatPage() {
  return (
    <AppShell>
      <Suspense fallback={null}>
        <ChatWindow />
      </Suspense>
    </AppShell>
  )
}
