// app/page.tsx
import { Navbar } from '@/components/landing/Navbar'
import { Hero } from '@/components/landing/Hero'
import { Models } from '@/components/landing/Models'
import { Features } from '@/components/landing/Features'

export default function LandingPage() {
  return (
    <>
      <Navbar />
      <Hero />
      <Models />
      <Features />
    </>
  )
}
