// components/layout/AppShell.tsx
'use client'
import { useRouter } from 'next/navigation'
import { Sidebar } from './Sidebar'

export function AppShell({ children }: { children: React.ReactNode }) {
  const router = useRouter()

  function handleSessionSelect(id: string) {
    router.push(`/chat?session=${id}`)
  }

  return (
    <div className="flex h-screen overflow-hidden bg-cream">
      <Sidebar onSessionSelect={handleSessionSelect} />
      <main className="flex-1 flex flex-col overflow-hidden">
        {children}
      </main>
    </div>
  )
}
