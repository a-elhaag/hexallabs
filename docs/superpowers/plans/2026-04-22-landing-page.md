# Landing Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a 7-scene cinematic scroll-snapped landing page for Hexal LM with SVG animations and brand design system.

**Architecture:** CSS `scroll-snap-type: y mandatory` container holds 7 fullscreen scenes. Each scene is a self-contained React component with inline SVGs. An `IntersectionObserver` in `SceneContainer` adds `.animate` class to visible scenes, triggering CSS keyframe animations. `SceneContext` tracks the active scene index for the progress nav.

**Tech Stack:** Next.js 15 App Router · TypeScript strict · Tailwind CSS v4 · `next/font/google` · Pure CSS animations + vanilla JS IntersectionObserver · No new deps

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `frontend/src/app/layout.tsx` | Modify | Load 3 fonts, set metadata, expose CSS vars |
| `frontend/src/styles/globals.css` | Modify | CSS vars, scroll-snap, keyframes, animation classes |
| `frontend/src/app/page.tsx` | Rewrite | Mount SceneContainer + all 7 scenes |
| `frontend/src/components/landing/SceneContainer.tsx` | Create | scroll-snap wrapper, IntersectionObserver, SceneContext |
| `frontend/src/components/landing/SceneNav.tsx` | Create | Fixed top nav + fixed right progress dots |
| `frontend/src/components/landing/scenes/HeroScene.tsx` | Create | Scene 01: hex logo draw + headline + CTA |
| `frontend/src/components/landing/scenes/ProblemScene.tsx` | Create | Scene 02: single circle + glitch words |
| `frontend/src/components/landing/scenes/CouncilScene.tsx` | Create | Scene 03: hex grid + peer-review lines + confidence counter |
| `frontend/src/components/landing/scenes/OracleScene.tsx` | Create | Scene 04: magnifying glass SVG draw |
| `frontend/src/components/landing/scenes/RelayScene.tsx` | Create | Scene 05: A→B→C chain + pulse dot |
| `frontend/src/components/landing/scenes/WorkflowScene.tsx` | Create | Scene 06: node graph + bezier edges |
| `frontend/src/components/landing/scenes/CtaScene.tsx` | Create | Scene 07: concentric rings + CTA buttons |

---

## Task 1: Font Setup + CSS Foundation

**Files:**
- Modify: `frontend/src/app/layout.tsx`
- Modify: `frontend/src/styles/globals.css`

- [ ] **Step 1: Update layout.tsx — load 3 fonts**

Replace the full contents of `frontend/src/app/layout.tsx` with:

```tsx
import "~/styles/globals.css";

import { type Metadata } from "next";
import { Inter, JetBrains_Mono, Space_Grotesk } from "next/font/google";

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  weight: ["300", "400", "600"],
  variable: "--font-display",
});

const inter = Inter({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-body",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400"],
  variable: "--font-mono",
});

export const metadata: Metadata = {
  title: "Hexal LM — Multiple minds. One answer.",
  description:
    "Seven models run in parallel. Each self-rates confidence. Apex synthesizes the weighted truth.",
  icons: [{ rel: "icon", url: "/favicon.ico" }],
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      className={`${spaceGrotesk.variable} ${inter.variable} ${jetbrainsMono.variable}`}
    >
      <body>{children}</body>
    </html>
  );
}
```

- [ ] **Step 2: Update globals.css — CSS vars, scroll-snap, keyframes**

Replace the full contents of `frontend/src/styles/globals.css` with:

```css
@import "tailwindcss";

@theme {
  /* Fonts */
  --font-display: var(--font-display), ui-sans-serif, system-ui, sans-serif;
  --font-body: var(--font-body), ui-sans-serif, system-ui, sans-serif;
  --font-mono: var(--font-mono), ui-monospace, monospace;

  /* Brand colors */
  --color-bg: #2c2c2c;
  --color-muted: #a89080;
  --color-surface: #f5f1ed;
  --color-accent: #6290c3;

  /* Easing */
  --ease-spring: cubic-bezier(0.16, 1, 0.3, 1);
}

/* Reset */
*, *::before, *::after { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }

/* Scroll container */
.scene-container {
  height: 100svh;
  overflow-y: scroll;
  scroll-snap-type: y mandatory;
  background: #2c2c2c;
}

/* Each scene */
.scene {
  height: 100svh;
  scroll-snap-align: start;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #2c2c2c;
}

/* ── Animation entrance classes ── */
/* Elements start invisible; .animate on parent triggers them */

.anim-headline span {
  display: inline-block;
  opacity: 0;
  transform: translateY(20px);
}
.scene.animate .anim-headline span {
  animation: word-in 400ms var(--ease-spring) forwards;
}

.anim-fade {
  opacity: 0;
  transform: translateY(16px);
}
.scene.animate .anim-fade {
  animation: fade-up 400ms var(--ease-spring) forwards;
}

.anim-scale {
  opacity: 0;
  transform: scale(0.85);
}
.scene.animate .anim-scale {
  animation: scale-in 300ms var(--ease-spring) forwards;
}

.anim-svg-draw {
  stroke-dashoffset: var(--path-length, 1000);
  stroke-dasharray: var(--path-length, 1000);
}
.scene.animate .anim-svg-draw {
  animation: svg-draw 600ms var(--ease-spring) forwards;
}

/* ── Keyframes ── */
@keyframes word-in {
  to { opacity: 1; transform: translateY(0); }
}

@keyframes fade-up {
  to { opacity: 1; transform: translateY(0); }
}

@keyframes scale-in {
  to { opacity: 1; transform: scale(1); }
}

@keyframes svg-draw {
  to { stroke-dashoffset: 0; }
}

@keyframes pulse-ring {
  0% { transform: scale(0.4); opacity: 0.8; }
  100% { transform: scale(1); opacity: 0; }
}

@keyframes hex-fill {
  to { opacity: 0.35; }
}

@keyframes glitch-flash {
  0%, 100% { color: #a89080; }
  20% { color: #ef4444; opacity: 0.7; }
  40% { color: #f5f1ed; }
  60% { color: #ef4444; opacity: 0.5; }
}

@keyframes pulse-glow {
  0%, 100% { filter: drop-shadow(0 0 4px #6290c3); opacity: 0.8; }
  50% { filter: drop-shadow(0 0 12px #6290c3); opacity: 1; }
}

@keyframes travel-dot {
  0% { offset-distance: 0%; }
  100% { offset-distance: 100%; }
}

/* ── Animation delay utilities ── */
.delay-100 { animation-delay: 100ms !important; }
.delay-200 { animation-delay: 200ms !important; }
.delay-300 { animation-delay: 300ms !important; }
.delay-400 { animation-delay: 400ms !important; }
.delay-500 { animation-delay: 500ms !important; }
.delay-600 { animation-delay: 600ms !important; }
.delay-700 { animation-delay: 700ms !important; }
.delay-800 { animation-delay: 800ms !important; }

/* ── Reduced motion ── */
@media (prefers-reduced-motion: reduce) {
  .scene * {
    animation: none !important;
    transition: none !important;
    opacity: 1 !important;
    transform: none !important;
    stroke-dashoffset: 0 !important;
  }
}
```

- [ ] **Step 3: Verify fonts load — start dev server**

```bash
cd frontend && bun dev
```

Open http://localhost:3000. Page should render (T3 default content). Check DevTools → Network → filter "font" — should see Space Grotesk, Inter, JetBrains Mono requests. No console errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/app/layout.tsx frontend/src/styles/globals.css
git commit -m "feat(landing): font setup and CSS animation foundation"
```

---

## Task 2: SceneContainer + SceneContext

**Files:**
- Create: `frontend/src/components/landing/SceneContainer.tsx`

- [ ] **Step 1: Create the directory**

```bash
mkdir -p frontend/src/components/landing/scenes
```

- [ ] **Step 2: Create SceneContainer.tsx**

Create `frontend/src/components/landing/SceneContainer.tsx`:

```tsx
"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";

interface SceneContextValue {
  activeScene: number;
  scrollToScene: (index: number) => void;
}

const SceneContext = createContext<SceneContextValue>({
  activeScene: 0,
  scrollToScene: () => undefined,
});

export function useScene() {
  return useContext(SceneContext);
}

interface SceneContainerProps {
  children: React.ReactNode;
}

export default function SceneContainer({ children }: SceneContainerProps) {
  const [activeScene, setActiveScene] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const scenes = container.querySelectorAll<HTMLElement>("[data-scene]");

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            entry.target.classList.add("animate");
            const index = (entry.target as HTMLElement).dataset.scene;
            if (index !== undefined) setActiveScene(Number(index));
          }
        }
      },
      { threshold: 0.5, root: container },
    );

    scenes.forEach((scene) => observer.observe(scene));
    return () => observer.disconnect();
  }, []);

  const scrollToScene = useCallback((index: number) => {
    const container = containerRef.current;
    if (!container) return;
    const scenes = container.querySelectorAll<HTMLElement>("[data-scene]");
    scenes[index]?.scrollIntoView({ behavior: "smooth" });
  }, []);

  return (
    <SceneContext.Provider value={{ activeScene, scrollToScene }}>
      <div ref={containerRef} className="scene-container">
        {children}
      </div>
    </SceneContext.Provider>
  );
}
```

- [ ] **Step 3: Typecheck**

```bash
cd frontend && bun run typecheck
```

Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/landing/SceneContainer.tsx
git commit -m "feat(landing): SceneContainer with IntersectionObserver and SceneContext"
```

---

## Task 3: SceneNav (top nav + progress dots)

**Files:**
- Create: `frontend/src/components/landing/SceneNav.tsx`

- [ ] **Step 1: Create SceneNav.tsx**

Create `frontend/src/components/landing/SceneNav.tsx`:

```tsx
"use client";

import { useScene } from "~/components/landing/SceneContainer";

const SCENE_COUNT = 7;

export default function SceneNav() {
  const { activeScene, scrollToScene } = useScene();

  return (
    <>
      {/* Fixed top nav */}
      <nav
        className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-8 py-4 transition-opacity duration-300"
        style={{
          opacity: activeScene === 0 || activeScene === 6 ? 1 : 0.4,
        }}
      >
        <span
          className="text-[#f5f1ed] text-sm font-semibold tracking-tight select-none"
          style={{ fontFamily: "var(--font-display)" }}
        >
          hexal
        </span>
        <div className="flex items-center gap-6">
          <a
            href="#council"
            className="text-[#a89080] text-xs font-medium hover:text-[#f5f1ed] transition-colors"
            style={{ fontFamily: "var(--font-body)" }}
          >
            The Council
          </a>
          <a
            href="#oracle"
            className="text-[#a89080] text-xs font-medium hover:text-[#f5f1ed] transition-colors"
            style={{ fontFamily: "var(--font-body)" }}
          >
            Oracle
          </a>
          <a
            href="#"
            className="text-[#a89080] text-xs font-medium hover:text-[#f5f1ed] transition-colors"
            style={{ fontFamily: "var(--font-body)" }}
          >
            Sign in
          </a>
          <button
            className="bg-[#6290c3] text-white text-xs font-medium px-3 py-1.5 rounded hover:scale-[1.02] active:scale-[0.98] transition-transform"
            style={{ fontFamily: "var(--font-body)" }}
          >
            Try free
          </button>
        </div>
      </nav>

      {/* Fixed right progress dots */}
      <div className="fixed right-6 top-1/2 -translate-y-1/2 z-50 flex flex-col gap-3">
        {Array.from({ length: SCENE_COUNT }, (_, i) => (
          <button
            key={i}
            onClick={() => scrollToScene(i)}
            aria-label={`Go to scene ${i + 1}`}
            className="transition-all duration-300 rounded-full bg-[#3a3a3a] hover:bg-[#6290c3]"
            style={{
              width: 6,
              height: activeScene === i ? 20 : 6,
              background: activeScene === i ? "#6290c3" : "#3a3a3a",
            }}
          />
        ))}
      </div>
    </>
  );
}
```

- [ ] **Step 2: Typecheck**

```bash
cd frontend && bun run typecheck
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/landing/SceneNav.tsx
git commit -m "feat(landing): SceneNav with progress dots and fixed top nav"
```

---

## Task 4: page.tsx scaffold + HeroScene

**Files:**
- Rewrite: `frontend/src/app/page.tsx`
- Create: `frontend/src/components/landing/scenes/HeroScene.tsx`

- [ ] **Step 1: Create HeroScene.tsx**

Create `frontend/src/components/landing/scenes/HeroScene.tsx`:

```tsx
export default function HeroScene() {
  return (
    <section
      className="scene flex-col gap-10"
      data-scene="0"
      id="hero"
    >
      {/* Hex logo SVG — draws via stroke-dashoffset */}
      <svg
        width="120"
        height="120"
        viewBox="0 0 120 120"
        fill="none"
        aria-hidden="true"
      >
        {/* Outer hex */}
        <polygon
          points="60,8 104,32 104,80 60,104 16,80 16,32"
          stroke="#6290c3"
          strokeWidth="1.5"
          className="anim-svg-draw delay-100"
          style={{ "--path-length": "280" } as React.CSSProperties}
        />
        {/* Inner hex */}
        <polygon
          points="60,24 88,40 88,72 60,88 32,72 32,40"
          stroke="#a89080"
          strokeWidth="1"
          opacity={0.5}
          className="anim-svg-draw delay-300"
          style={{ "--path-length": "190" } as React.CSSProperties}
        />
        {/* Center dot */}
        <circle
          cx="60"
          cy="60"
          r="5"
          fill="#6290c3"
          className="anim-scale delay-500"
        />
      </svg>

      {/* Headline */}
      <h1
        className="anim-headline text-center leading-tight"
        style={{
          fontFamily: "var(--font-display)",
          fontWeight: 300,
          fontSize: "clamp(2.5rem, 5vw, 4rem)",
          color: "#f5f1ed",
          letterSpacing: "-0.025em",
        }}
      >
        {"Multiple minds.".split(" ").map((word, i) => (
          <span
            key={i}
            className={`delay-${(i + 3) * 100}` as string}
            style={{ marginRight: "0.3em" }}
          >
            {word}
          </span>
        ))}
        <br />
        {"One answer.".split(" ").map((word, i) => (
          <span
            key={`b${i}`}
            className={`delay-${(i + 5) * 100}` as string}
            style={{ marginRight: "0.3em" }}
          >
            {word}
          </span>
        ))}
      </h1>

      {/* CTA */}
      <button
        className="anim-scale delay-700 bg-[#6290c3] text-white rounded px-6 py-3 hover:scale-[1.02] active:scale-[0.98] transition-transform"
        style={{ fontFamily: "var(--font-body)", fontWeight: 500, fontSize: "0.9rem" }}
      >
        Try the Council →
      </button>
    </section>
  );
}
```

- [ ] **Step 2: Rewrite page.tsx**

Replace the full contents of `frontend/src/app/page.tsx`:

```tsx
import SceneContainer from "~/components/landing/SceneContainer";
import SceneNav from "~/components/landing/SceneNav";
import HeroScene from "~/components/landing/scenes/HeroScene";

export default function HomePage() {
  return (
    <>
      <SceneNav />
      <SceneContainer>
        <HeroScene />
        {/* remaining scenes added in subsequent tasks */}
      </SceneContainer>
    </>
  );
}
```

- [ ] **Step 3: Run dev server and verify**

```bash
cd frontend && bun dev
```

Open http://localhost:3000. Verify:
- Dark background scene fills viewport
- Hex logo SVG draws in on load (stroke animates)
- Headline words fade up sequentially
- CTA button scales in
- Top nav visible with "hexal" wordmark
- One progress dot visible on right, active (blue pill)

- [ ] **Step 4: Typecheck**

```bash
cd frontend && bun run typecheck
```

Expected: no errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/app/page.tsx frontend/src/components/landing/scenes/HeroScene.tsx
git commit -m "feat(landing): Hero scene with SVG draw animation"
```

---

## Task 5: ProblemScene

**Files:**
- Create: `frontend/src/components/landing/scenes/ProblemScene.tsx`
- Modify: `frontend/src/app/page.tsx` (add scene)

- [ ] **Step 1: Create ProblemScene.tsx**

Create `frontend/src/components/landing/scenes/ProblemScene.tsx`:

```tsx
export default function ProblemScene() {
  return (
    <section
      className="scene flex-col gap-12"
      data-scene="1"
      id="problem"
    >
      {/* Single circle SVG */}
      <svg
        width="140"
        height="140"
        viewBox="0 0 140 140"
        fill="none"
        aria-hidden="true"
      >
        <circle
          cx="70"
          cy="70"
          r="50"
          stroke="#a89080"
          strokeWidth="1.5"
          className="anim-svg-draw delay-100"
          style={{ "--path-length": "315" } as React.CSSProperties}
        />
        {/* Vertical crosshair */}
        <line
          x1="70" y1="20" x2="70" y2="120"
          stroke="#a89080"
          strokeWidth="0.8"
          opacity={0.4}
          className="anim-svg-draw delay-300"
          style={{ "--path-length": "100" } as React.CSSProperties}
        />
        {/* Horizontal crosshair */}
        <line
          x1="20" y1="70" x2="120" y2="70"
          stroke="#a89080"
          strokeWidth="0.8"
          opacity={0.4}
          className="anim-svg-draw delay-400"
          style={{ "--path-length": "100" } as React.CSSProperties}
        />
        <circle cx="70" cy="70" r="4" fill="#a89080" className="anim-scale delay-500" />
      </svg>

      {/* Headline */}
      <h2
        className="anim-fade delay-400 text-center"
        style={{
          fontFamily: "var(--font-display)",
          fontWeight: 300,
          fontSize: "clamp(1.8rem, 3.5vw, 2.8rem)",
          color: "#f5f1ed",
          letterSpacing: "-0.02em",
        }}
      >
        One model. One blind spot.
      </h2>

      {/* Problem words */}
      <div
        className="flex gap-6"
        style={{ fontFamily: "var(--font-mono)", fontSize: "0.85rem" }}
      >
        <span className="anim-fade delay-500" style={{ color: "#a89080" }}>
          bias
        </span>
        <span className="anim-fade delay-600" style={{ color: "#a89080" }}>
          gaps
        </span>
        <span
          className="anim-fade delay-700"
          style={{
            color: "#a89080",
            animation: undefined,
          }}
        >
          <span
            className="anim-fade delay-700"
            style={{ display: "inline-block" }}
          >
            <span
              style={{
                color: "#a89080",
                display: "inline-block",
              }}
              className="scene-0-glitch"
            >
              hallucination
            </span>
          </span>
        </span>
      </div>

      <style>{`
        .scene.animate .scene-0-glitch {
          animation: glitch-flash 600ms 900ms ease forwards;
        }
      `}</style>
    </section>
  );
}
```

- [ ] **Step 2: Add ProblemScene to page.tsx**

Edit `frontend/src/app/page.tsx`:

```tsx
import SceneContainer from "~/components/landing/SceneContainer";
import SceneNav from "~/components/landing/SceneNav";
import HeroScene from "~/components/landing/scenes/HeroScene";
import ProblemScene from "~/components/landing/scenes/ProblemScene";

export default function HomePage() {
  return (
    <>
      <SceneNav />
      <SceneContainer>
        <HeroScene />
        <ProblemScene />
      </SceneContainer>
    </>
  );
}
```

- [ ] **Step 3: Verify in browser**

Scroll past hero scene. Problem scene should snap into view. Verify:
- Circle draws in
- Crosshairs extend
- "One model. One blind spot." fades up
- "bias · gaps · hallucination" appear sequentially
- "hallucination" flashes red briefly

- [ ] **Step 4: Typecheck**

```bash
cd frontend && bun run typecheck
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/landing/scenes/ProblemScene.tsx frontend/src/app/page.tsx
git commit -m "feat(landing): Problem scene with glitch animation"
```

---

## Task 6: CouncilScene

**Files:**
- Create: `frontend/src/components/landing/scenes/CouncilScene.tsx`
- Modify: `frontend/src/app/page.tsx`

- [ ] **Step 1: Create CouncilScene.tsx**

Create `frontend/src/components/landing/scenes/CouncilScene.tsx`:

```tsx
"use client";

import { useEffect, useRef, useState } from "react";

const HEX_CLIP = "polygon(50% 0%, 93% 25%, 93% 75%, 50% 100%, 7% 75%, 7% 25%)";

interface HexProps {
  size: number;
  color: string;
  delay: number;
  confidence?: number;
  isApex?: boolean;
}

function Hex({ size, color, delay, confidence, isApex }: HexProps) {
  return (
    <div
      className="anim-scale relative flex items-center justify-center"
      style={{
        width: size,
        height: size,
        background: color,
        clipPath: HEX_CLIP,
        animationDelay: `${delay}ms`,
      }}
    >
      {confidence !== undefined && (
        <span
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: isApex ? "0.75rem" : "0.6rem",
            color: isApex ? "#fff" : "#f5f1ed",
            opacity: 0.9,
          }}
        >
          {confidence.toFixed(1)}
        </span>
      )}
    </div>
  );
}

const OUTER_CONFIDENCES = [7.2, 8.1, 6.9, 8.4, 7.7, 8.9];

export default function CouncilScene() {
  const [counting, setCounting] = useState(false);
  const [counts, setCounts] = useState(OUTER_CONFIDENCES.map(() => 0));
  const [apexCount, setApexCount] = useState(0);
  const sceneRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const el = sceneRef.current;
    if (!el) return;
    const observer = new MutationObserver(() => {
      if (el.classList.contains("animate")) {
        setCounting(true);
        observer.disconnect();
      }
    });
    observer.observe(el, { attributes: true, attributeFilter: ["class"] });
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!counting) return;
    const duration = 1000;
    const start = Date.now();
    const tick = () => {
      const progress = Math.min((Date.now() - start) / duration, 1);
      setCounts(OUTER_CONFIDENCES.map((target) => target * progress));
      setApexCount(8.4 * progress);
      if (progress < 1) requestAnimationFrame(tick);
    };
    const raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [counting]);

  return (
    <section
      ref={sceneRef}
      className="scene flex-col gap-10"
      data-scene="2"
      id="council"
    >
      {/* Hex grid — Apex center, 6 surrounding */}
      <div className="relative flex items-center justify-center" style={{ width: 220, height: 220 }}>
        {/* SVG peer-review lines */}
        <svg
          className="absolute inset-0"
          width="220"
          height="220"
          viewBox="0 0 220 220"
          fill="none"
          aria-hidden="true"
        >
          {/* Lines from apex (110,110) to outer hex centers */}
          {[
            [110, 40], [175, 75], [175, 145],
            [110, 180], [45, 145], [45, 75],
          ].map(([x, y], i) => (
            <line
              key={i}
              x1="110" y1="110"
              x2={x} y2={y}
              stroke="#6290c3"
              strokeWidth="0.8"
              opacity={0.3}
              className="anim-svg-draw"
              style={{
                "--path-length": "80",
                animationDelay: `${600 + i * 80}ms`,
              } as React.CSSProperties}
            />
          ))}
        </svg>

        {/* Apex hex center */}
        <div className="absolute" style={{ top: 80, left: 80 }}>
          <Hex size={60} color="#6290c3" delay={200} confidence={apexCount} isApex />
        </div>

        {/* Outer hexes at clock positions */}
        {[
          { top: 12,  left: 90,  i: 0 },
          { top: 55,  left: 157, i: 1 },
          { top: 127, left: 157, i: 2 },
          { top: 162, left: 90,  i: 3 },
          { top: 127, left: 23,  i: 4 },
          { top: 55,  left: 23,  i: 5 },
        ].map(({ top, left, i }) => (
          <div key={i} className="absolute" style={{ top, left }}>
            <Hex
              size={36}
              color="rgba(168,144,128,0.2)"
              delay={300 + i * 80}
              confidence={counts[i]}
            />
          </div>
        ))}
      </div>

      <h2
        className="anim-fade delay-200 text-center"
        style={{
          fontFamily: "var(--font-display)",
          fontWeight: 300,
          fontSize: "clamp(1.8rem, 3.5vw, 2.8rem)",
          color: "#f5f1ed",
          letterSpacing: "-0.02em",
        }}
      >
        Seven minds. Parallel.
      </h2>

      <p
        className="anim-fade delay-400 text-center"
        style={{
          fontFamily: "var(--font-mono)",
          fontSize: "0.72rem",
          color: "#a89080",
        }}
      >
        confidence: {apexCount.toFixed(1)} · peer rounds: 1 · models: 7
      </p>
    </section>
  );
}
```

- [ ] **Step 2: Add CouncilScene to page.tsx**

```tsx
import SceneContainer from "~/components/landing/SceneContainer";
import SceneNav from "~/components/landing/SceneNav";
import CouncilScene from "~/components/landing/scenes/CouncilScene";
import HeroScene from "~/components/landing/scenes/HeroScene";
import ProblemScene from "~/components/landing/scenes/ProblemScene";

export default function HomePage() {
  return (
    <>
      <SceneNav />
      <SceneContainer>
        <HeroScene />
        <ProblemScene />
        <CouncilScene />
      </SceneContainer>
    </>
  );
}
```

- [ ] **Step 3: Verify in browser**

Scroll to Council scene. Verify:
- Apex hex (blue, larger) appears first
- 6 outer hexes scale in staggered
- Peer-review lines draw from apex outward
- Confidence numbers count up from 0

- [ ] **Step 4: Typecheck**

```bash
cd frontend && bun run typecheck
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/landing/scenes/CouncilScene.tsx frontend/src/app/page.tsx
git commit -m "feat(landing): Council scene with hex grid and confidence counter"
```

---

## Task 7: OracleScene

**Files:**
- Create: `frontend/src/components/landing/scenes/OracleScene.tsx`
- Modify: `frontend/src/app/page.tsx`

- [ ] **Step 1: Create OracleScene.tsx**

Create `frontend/src/components/landing/scenes/OracleScene.tsx`:

```tsx
export default function OracleScene() {
  return (
    <section
      className="scene flex-col gap-10"
      data-scene="3"
      id="oracle"
    >
      {/* Magnifying glass SVG — matches reference image */}
      <svg
        width="180"
        height="200"
        viewBox="0 0 180 200"
        fill="none"
        aria-hidden="true"
      >
        {/* Outer circle */}
        <circle
          cx="80" cy="85" r="60"
          stroke="#a89080"
          strokeWidth="1.5"
          className="anim-svg-draw delay-100"
          style={{ "--path-length": "377" } as React.CSSProperties}
        />
        {/* Vertical crosshair */}
        <line
          x1="80" y1="25" x2="80" y2="145"
          stroke="#6290c3"
          strokeWidth="0.8"
          opacity={0.5}
          className="anim-svg-draw delay-300"
          style={{ "--path-length": "120" } as React.CSSProperties}
        />
        {/* Horizontal crosshair */}
        <line
          x1="20" y1="85" x2="140" y2="85"
          stroke="#6290c3"
          strokeWidth="0.8"
          opacity={0.5}
          className="anim-svg-draw delay-400"
          style={{ "--path-length": "120" } as React.CSSProperties}
        />
        {/* Equatorial ellipse */}
        <ellipse
          cx="80" cy="95" rx="38" ry="20"
          stroke="#6290c3"
          strokeWidth="1.2"
          className="anim-svg-draw delay-500"
          style={{ "--path-length": "188" } as React.CSSProperties}
        />
        {/* Handle */}
        <line
          x1="124" y1="134" x2="168" y2="185"
          stroke="#a89080"
          strokeWidth="7"
          strokeLinecap="round"
          className="anim-fade delay-600"
        />
      </svg>

      <h2
        className="anim-fade delay-300 text-center"
        style={{
          fontFamily: "var(--font-display)",
          fontWeight: 300,
          fontSize: "clamp(1.8rem, 3.5vw, 2.8rem)",
          color: "#f5f1ed",
          letterSpacing: "-0.02em",
        }}
      >
        One lens. Direct.
      </h2>

      <p
        className="anim-fade delay-500"
        style={{
          fontFamily: "var(--font-mono)",
          fontSize: "0.72rem",
          color: "#a89080",
        }}
      >
        mode: oracle · model: apex · latency: 0.8s
      </p>
    </section>
  );
}
```

- [ ] **Step 2: Add OracleScene to page.tsx**

```tsx
import SceneContainer from "~/components/landing/SceneContainer";
import SceneNav from "~/components/landing/SceneNav";
import CouncilScene from "~/components/landing/scenes/CouncilScene";
import HeroScene from "~/components/landing/scenes/HeroScene";
import OracleScene from "~/components/landing/scenes/OracleScene";
import ProblemScene from "~/components/landing/scenes/ProblemScene";

export default function HomePage() {
  return (
    <>
      <SceneNav />
      <SceneContainer>
        <HeroScene />
        <ProblemScene />
        <CouncilScene />
        <OracleScene />
      </SceneContainer>
    </>
  );
}
```

- [ ] **Step 3: Verify in browser**

Scroll to Oracle scene. Verify magnifying glass draws: outer circle first, then crosshairs, then ellipse, then handle slides in.

- [ ] **Step 4: Typecheck + commit**

```bash
cd frontend && bun run typecheck
git add frontend/src/components/landing/scenes/OracleScene.tsx frontend/src/app/page.tsx
git commit -m "feat(landing): Oracle scene with magnifying glass SVG draw"
```

---

## Task 8: RelayScene

**Files:**
- Create: `frontend/src/components/landing/scenes/RelayScene.tsx`
- Modify: `frontend/src/app/page.tsx`

- [ ] **Step 1: Create RelayScene.tsx**

Create `frontend/src/components/landing/scenes/RelayScene.tsx`:

```tsx
export default function RelayScene() {
  return (
    <section
      className="scene flex-col gap-10"
      data-scene="4"
      id="relay"
    >
      <svg
        width="280"
        height="100"
        viewBox="0 0 280 100"
        fill="none"
        aria-hidden="true"
      >
        {/* Node A */}
        <circle cx="40" cy="50" r="24" stroke="#a89080" strokeWidth="1.2" className="anim-scale delay-100" />
        <text x="40" y="55" textAnchor="middle" fill="#a89080" fontSize="11" fontFamily="var(--font-mono)">A</text>

        {/* Line A→B */}
        <line
          x1="64" y1="50" x2="116" y2="50"
          stroke="#a89080" strokeWidth="1"
          strokeDasharray="4,4"
          className="anim-svg-draw delay-300"
          style={{ "--path-length": "52" } as React.CSSProperties}
        />

        {/* Node B — active */}
        <circle cx="140" cy="50" r="28" fill="rgba(98,144,195,0.18)" stroke="#6290c3" strokeWidth="1.5" className="anim-scale delay-400" />
        <text x="140" y="55" textAnchor="middle" fill="#6290c3" fontSize="11" fontFamily="var(--font-mono)">B</text>

        {/* Pulse dot A→B */}
        <circle r="5" fill="#6290c3" className="anim-fade delay-500" style={{ animationName: "none" }}>
          <animateMotion dur="1.2s" begin="0.5s" repeatCount="indefinite">
            <mpath href="#path-ab" />
          </animateMotion>
        </circle>
        <path id="path-ab" d="M64,50 L116,50" stroke="none" />

        {/* Line B→C */}
        <line
          x1="168" y1="50" x2="220" y2="50"
          stroke="#3a3a3a" strokeWidth="1"
          strokeDasharray="4,4"
          opacity={0.4}
          className="anim-svg-draw delay-600"
          style={{ "--path-length": "52" } as React.CSSProperties}
        />

        {/* Node C — dim */}
        <circle cx="244" cy="50" r="24" stroke="#3a3a3a" strokeWidth="1" opacity={0.35} className="anim-scale delay-700" />
        <text x="244" y="55" textAnchor="middle" fill="#555" fontSize="11" fontFamily="var(--font-mono)">C</text>
      </svg>

      <h2
        className="anim-fade delay-200 text-center"
        style={{
          fontFamily: "var(--font-display)",
          fontWeight: 300,
          fontSize: "clamp(1.8rem, 3.5vw, 2.8rem)",
          color: "#f5f1ed",
          letterSpacing: "-0.02em",
        }}
      >
        Mid-thought handoff.
      </h2>

      <p
        className="anim-fade delay-500"
        style={{
          fontFamily: "var(--font-mono)",
          fontSize: "0.72rem",
          color: "#a89080",
        }}
      >
        mode: relay · handoff at token 412 · context preserved
      </p>
    </section>
  );
}
```

- [ ] **Step 2: Add RelayScene to page.tsx**

```tsx
import SceneContainer from "~/components/landing/SceneContainer";
import SceneNav from "~/components/landing/SceneNav";
import CouncilScene from "~/components/landing/scenes/CouncilScene";
import HeroScene from "~/components/landing/scenes/HeroScene";
import OracleScene from "~/components/landing/scenes/OracleScene";
import ProblemScene from "~/components/landing/scenes/ProblemScene";
import RelayScene from "~/components/landing/scenes/RelayScene";

export default function HomePage() {
  return (
    <>
      <SceneNav />
      <SceneContainer>
        <HeroScene />
        <ProblemScene />
        <CouncilScene />
        <OracleScene />
        <RelayScene />
      </SceneContainer>
    </>
  );
}
```

- [ ] **Step 3: Verify in browser**

Scroll to Relay scene. Verify: nodes appear L→R, dashed lines draw, pulse dot travels A→B on loop, C node dims correctly.

- [ ] **Step 4: Typecheck + commit**

```bash
cd frontend && bun run typecheck
git add frontend/src/components/landing/scenes/RelayScene.tsx frontend/src/app/page.tsx
git commit -m "feat(landing): Relay scene with animated pulse dot chain"
```

---

## Task 9: WorkflowScene

**Files:**
- Create: `frontend/src/components/landing/scenes/WorkflowScene.tsx`
- Modify: `frontend/src/app/page.tsx`

- [ ] **Step 1: Create WorkflowScene.tsx**

Create `frontend/src/components/landing/scenes/WorkflowScene.tsx`:

```tsx
export default function WorkflowScene() {
  return (
    <section
      className="scene flex-col gap-10"
      data-scene="5"
      id="workflow"
    >
      <svg
        width="220"
        height="220"
        viewBox="0 0 220 220"
        fill="none"
        aria-hidden="true"
      >
        {/* Input node left */}
        <rect x="10" y="20" width="80" height="36" rx="8"
          stroke="#a89080" strokeWidth="1"
          className="anim-fade delay-100"
        />
        <text x="50" y="43" textAnchor="middle" fill="#a89080" fontSize="10" fontFamily="var(--font-mono)">Swift</text>

        {/* Input node right */}
        <rect x="130" y="20" width="80" height="36" rx="8"
          stroke="#a89080" strokeWidth="1"
          className="anim-fade delay-200"
        />
        <text x="170" y="43" textAnchor="middle" fill="#a89080" fontSize="10" fontFamily="var(--font-mono)">Prism</text>

        {/* Bezier edge left→center */}
        <path
          d="M50,56 C50,100 110,100 110,112"
          stroke="#6290c3" strokeWidth="1"
          className="anim-svg-draw delay-300"
          style={{ "--path-length": "90" } as React.CSSProperties}
        />

        {/* Bezier edge right→center */}
        <path
          d="M170,56 C170,100 110,100 110,112"
          stroke="#6290c3" strokeWidth="1"
          className="anim-svg-draw delay-400"
          style={{ "--path-length": "90" } as React.CSSProperties}
        />

        {/* Center node — Apex, active */}
        <rect x="60" y="112" width="100" height="40" rx="8"
          fill="rgba(98,144,195,0.2)"
          stroke="#6290c3" strokeWidth="1.5"
          className="anim-scale delay-500"
          style={{ animation: undefined }}
        >
          <animate
            attributeName="filter"
            values="drop-shadow(0 0 4px #6290c3);drop-shadow(0 0 12px #6290c3);drop-shadow(0 0 4px #6290c3)"
            dur="2s"
            repeatCount="indefinite"
            begin="0.5s"
          />
        </rect>
        <text x="110" y="137" textAnchor="middle" fill="#6290c3" fontSize="10" fontFamily="var(--font-mono)">Apex</text>

        {/* Edge center→output */}
        <line
          x1="110" y1="152" x2="110" y2="178"
          stroke="#a89080" strokeWidth="1"
          className="anim-svg-draw delay-600"
          style={{ "--path-length": "26" } as React.CSSProperties}
        />

        {/* Output node */}
        <rect x="60" y="178" width="100" height="36" rx="8"
          stroke="#3a3a3a" strokeWidth="1"
          opacity={0.5}
          className="anim-fade delay-700"
        />
        <text x="110" y="201" textAnchor="middle" fill="#555" fontSize="10" fontFamily="var(--font-mono)">Output</text>
      </svg>

      <h2
        className="anim-fade delay-200 text-center"
        style={{
          fontFamily: "var(--font-display)",
          fontWeight: 300,
          fontSize: "clamp(1.8rem, 3.5vw, 2.8rem)",
          color: "#f5f1ed",
          letterSpacing: "-0.02em",
        }}
      >
        Your pipeline. Any order.
      </h2>

      <p
        className="anim-fade delay-500"
        style={{
          fontFamily: "var(--font-mono)",
          fontSize: "0.72rem",
          color: "#a89080",
        }}
      >
        mode: workflow · nodes: 4 · edges: 3
      </p>
    </section>
  );
}
```

- [ ] **Step 2: Add WorkflowScene to page.tsx**

```tsx
import SceneContainer from "~/components/landing/SceneContainer";
import SceneNav from "~/components/landing/SceneNav";
import CouncilScene from "~/components/landing/scenes/CouncilScene";
import HeroScene from "~/components/landing/scenes/HeroScene";
import OracleScene from "~/components/landing/scenes/OracleScene";
import ProblemScene from "~/components/landing/scenes/ProblemScene";
import RelayScene from "~/components/landing/scenes/RelayScene";
import WorkflowScene from "~/components/landing/scenes/WorkflowScene";

export default function HomePage() {
  return (
    <>
      <SceneNav />
      <SceneContainer>
        <HeroScene />
        <ProblemScene />
        <CouncilScene />
        <OracleScene />
        <RelayScene />
        <WorkflowScene />
      </SceneContainer>
    </>
  );
}
```

- [ ] **Step 3: Verify in browser**

Scroll to Workflow scene. Verify: input nodes drop in, bezier edges draw, Apex center node pulses glow, output node fades in below.

- [ ] **Step 4: Typecheck + commit**

```bash
cd frontend && bun run typecheck
git add frontend/src/components/landing/scenes/WorkflowScene.tsx frontend/src/app/page.tsx
git commit -m "feat(landing): Workflow scene with node graph and bezier edges"
```

---

## Task 10: CtaScene + final page.tsx

**Files:**
- Create: `frontend/src/components/landing/scenes/CtaScene.tsx`
- Modify: `frontend/src/app/page.tsx` (final version)

- [ ] **Step 1: Create CtaScene.tsx**

Create `frontend/src/components/landing/scenes/CtaScene.tsx`:

```tsx
export default function CtaScene() {
  return (
    <section
      className="scene flex-col gap-10"
      data-scene="6"
      id="cta"
    >
      {/* Concentric rings */}
      <div className="relative flex items-center justify-center" style={{ width: 200, height: 200 }}>
        {[
          { size: 200, delay: 100, opacity: 0.15 },
          { size: 140, delay: 300, opacity: 0.3 },
          { size: 80,  delay: 500, opacity: 0.5 },
        ].map(({ size, delay, opacity }, i) => (
          <div
            key={i}
            className="absolute rounded-full border border-[#6290c3]"
            style={{
              width: size,
              height: size,
              opacity,
              animation: `pulse-ring 2.4s ${delay * 2}ms ease-out infinite`,
            }}
          />
        ))}
        {/* Center dot */}
        <div
          className="rounded-full bg-[#6290c3] anim-scale delay-600"
          style={{ width: 24, height: 24, position: "absolute" }}
        />
      </div>

      <h2
        className="anim-fade delay-300 text-center"
        style={{
          fontFamily: "var(--font-display)",
          fontWeight: 300,
          fontSize: "clamp(1.8rem, 3.5vw, 2.8rem)",
          color: "#f5f1ed",
          letterSpacing: "-0.02em",
        }}
      >
        Start your first council.
      </h2>

      <div className="flex gap-4 anim-fade delay-500">
        <button
          className="bg-[#6290c3] text-white rounded px-6 py-3 hover:scale-[1.02] active:scale-[0.98] transition-transform"
          style={{ fontFamily: "var(--font-body)", fontWeight: 500, fontSize: "0.9rem" }}
        >
          Try the Council →
        </button>
        <button
          className="text-[#a89080] rounded px-6 py-3 border border-[#3a3a3a] hover:border-[#a89080] hover:text-[#f5f1ed] transition-colors"
          style={{ fontFamily: "var(--font-body)", fontWeight: 500, fontSize: "0.9rem" }}
        >
          Learn more
        </button>
      </div>
    </section>
  );
}
```

- [ ] **Step 2: Final page.tsx — all 7 scenes**

Replace the full contents of `frontend/src/app/page.tsx`:

```tsx
import SceneContainer from "~/components/landing/SceneContainer";
import SceneNav from "~/components/landing/SceneNav";
import CouncilScene from "~/components/landing/scenes/CouncilScene";
import CtaScene from "~/components/landing/scenes/CtaScene";
import HeroScene from "~/components/landing/scenes/HeroScene";
import OracleScene from "~/components/landing/scenes/OracleScene";
import ProblemScene from "~/components/landing/scenes/ProblemScene";
import RelayScene from "~/components/landing/scenes/RelayScene";
import WorkflowScene from "~/components/landing/scenes/WorkflowScene";

export default function HomePage() {
  return (
    <>
      <SceneNav />
      <SceneContainer>
        <HeroScene />
        <ProblemScene />
        <CouncilScene />
        <OracleScene />
        <RelayScene />
        <WorkflowScene />
        <CtaScene />
      </SceneContainer>
    </>
  );
}
```

- [ ] **Step 3: Full walkthrough in browser**

```bash
cd frontend && bun dev
```

Scroll through all 7 scenes. Verify:
1. Hero — hex draws, headline animates, CTA scales
2. Problem — circle draws, glitch on "hallucination"
3. Council — hexes stagger in, lines draw, counters run
4. Oracle — magnifying glass draws piece by piece
5. Relay — nodes appear, pulse dot travels chain
6. Workflow — nodes drop, bezier edges draw, Apex glows
7. CTA — rings pulse, two buttons appear

Progress dots on right track active scene. Nav opacity dims on scenes 2–6.

- [ ] **Step 4: Typecheck**

```bash
cd frontend && bun run typecheck
```

Expected: no errors.

- [ ] **Step 5: Lint**

```bash
cd frontend && bun run lint
```

Fix any lint errors before committing.

- [ ] **Step 6: Final commit**

```bash
git add frontend/src/components/landing/scenes/CtaScene.tsx frontend/src/app/page.tsx
git commit -m "feat(landing): CTA scene and complete 7-scene landing page"
```

---

## Self-Review

**Spec coverage check:**
- ✅ 7 scenes: Hero, Problem, Council, Oracle, Relay, Workflow, CTA
- ✅ CSS scroll-snap-type: y mandatory
- ✅ Space Grotesk 300 / Inter 500 / JetBrains Mono 400
- ✅ Dark bg #2c2c2c + #f5f1ed surface (used in CouncilScene data card, CTA)
- ✅ Visual-led, 3–5 word headlines
- ✅ IntersectionObserver adds `.animate` class
- ✅ SVG stroke-dashoffset draw pattern
- ✅ Confidence counter (CouncilScene)
- ✅ Pulse dot (RelayScene animateMotion)
- ✅ Concentric rings pulse (CtaScene)
- ✅ Progress dots (SceneNav)
- ✅ Fixed top nav with opacity dim on mid-scenes
- ✅ prefers-reduced-motion in globals.css
- ✅ No GSAP, no new deps, TypeScript strict

**Type consistency check:**
- `SceneContext` exported from `SceneContainer.tsx`, imported in `SceneNav.tsx` via `useScene()` ✅
- `data-scene` attribute is a string on DOM, parsed with `Number()` in observer ✅
- All scene files export default functions, no props required ✅

**Placeholder check:** None found.
