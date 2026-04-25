import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'HexalLabs',
  description: 'Seven minds. One answer.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
