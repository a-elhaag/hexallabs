# Hexal LM — Landing Page Design Spec

**Date:** 2026-04-22  
**Branch:** feat/oracle-sse  
**Status:** Approved

---

## Overview

Scrollytelling landing page for Hexal LM. Cinematic fullscreen scenes, scroll-snapped. Each scene introduces one product concept using its iconic SVG visual. No marketing copy walls — visuals carry the story.

---

## Locked Decisions

| Dimension | Decision |
|---|---|
| Scroll architecture | CSS `scroll-snap-type: y mandatory`. Each scene snaps. No JS hijacking. |
| Fonts | Space Grotesk 300 (display) · Inter 500 (body) · JetBrains Mono 400 (data) |
| Color mode | Dark bg (`#2c2c2c`) always. `#f5f1ed` surface cards for feature content. |
| Content density | Visual-led. 3–5 word headlines. No paragraph copy per scene. |
| Animation engine | Pure CSS + minimal vanilla JS (IntersectionObserver, counters). No GSAP. No new deps. |

---

## Color System

```
--color-bg:      #2c2c2c   All scene backgrounds
--color-muted:   #a89080   Body text, inactive SVG strokes, nav links
--color-surface: #f5f1ed   Hero headline, feature surface cards
--color-accent:  #6290c3   CTA, active hexes, SVG glow, mode labels
```

---

## Typography

All fonts loaded via `next/font/google`, CSS variables exposed on `:root`, latin subset only.

| Role | Font | Weight | Usage |
|---|---|---|---|
| Display | Space Grotesk | 300 | Scene headlines, logo, card titles |
| Body | Inter | 500 | Subtitles, nav links, descriptions |
| Mono | JetBrains Mono | 400 | Confidence scores, latency, token counts |

---

## Scene Sequence

7 fullscreen scenes. Scroll advances scene. Each scene = `100svh`, `scroll-snap-align: start`.

### Scene 01 — Hero

**Headline:** "Multiple minds. One answer."  
**Visual:** Nested hexagon logo draws in via `stroke-dashoffset`. Center dot pulses.  
**Animation sequence:**
1. Outer hex outline draws (600ms, dashoffset)
2. Inner hex draws (400ms, 100ms delay)
3. Center dot scales 0→1 (200ms)
4. Headline words fade + translateY(-16px)→0, 40ms stagger per word
5. CTA button scales 0.85→1 (300ms, 200ms delay)

**Elements:** Logo · headline · single CTA "Try the Council →"

---

### Scene 02 — Problem

**Headline:** "One model. One blind spot."  
**Visual:** Single circle, crosshairs, slow pulse. Words "bias · gaps · hallucination" glitch in sequentially. Red tint flash on "hallucination".  
**Animation sequence:**
1. Circle draws dashoffset (500ms)
2. Crosshair lines extend outward (300ms, 200ms delay)
3. Problem words type on sequentially (100ms each)
4. Red overlay flash on final word (glitch keyframe)

**Purpose:** Establishes tension before the solution.

---

### Scene 03 — The Council

**Headline:** "Seven minds. Parallel."  
**Visual:** Hex grid. Apex hex (center, larger, accent fill). 6 outer hexes. Peer-review lines animate between hexes. Confidence numbers count up inside each.  
**Animation sequence:**
1. Apex hex scales 0.4→1 (300ms)
2. Outer hexes scale in staggered 80ms each
3. Hex fills animate (opacity 0→0.3) as model "streams"
4. Peer-review SVG lines draw between hexes (dashoffset, 400ms each)
5. Confidence numbers count 0→N via JS counter (800ms)

**Layout:** Apex center, 6 surrounding in honeycomb pattern.

---

### Scene 04 — Oracle

**Headline:** "One lens. Direct."  
**Visual:** Magnifying glass. Circle (muted stroke), equatorial ellipse (accent stroke), crosshair lines (accent, low opacity), handle (muted, rounded cap). Matches reference image 1.  
**Animation sequence:**
1. Outer circle draws dashoffset (500ms)
2. Vertical crosshair extends top→bottom (300ms, 150ms delay)
3. Horizontal crosshair extends left→right (300ms, 200ms delay)
4. Ellipse draws dashoffset (400ms, 300ms delay)
5. Handle slides in from bottom-right translateX/Y (250ms, 400ms delay)

---

### Scene 05 — The Relay

**Headline:** "Mid-thought handoff."  
**Visual:** Three model nodes (A→B→C) connected by dashed lines. Pulse dot travels the chain. Active node glows accent.  
**Animation sequence:**
1. Node A appears (scale 0→1, 200ms)
2. Dashed line A→B draws (dashoffset, 300ms)
3. Node B appears accent-filled (250ms)
4. Pulse dot animates A→B along path (400ms)
5. Line B→C draws dim (300ms, 500ms delay)
6. Node C appears dim (200ms)

---

### Scene 06 — Workflow

**Headline:** "Your pipeline. Any order."  
**Visual:** Node graph. Two input nodes top, one active center node (accent), one output node bottom. Bezier edges. Matches reference image 4.  
**Animation sequence:**
1. Input nodes drop from above, staggered (translateY(-20px)→0, 200ms each)
2. Bezier edges draw dashoffset (400ms each)
3. Center node pulses accent glow (keyframe loop)
4. Output node fades in (300ms, 600ms delay)

---

### Scene 07 — CTA

**Headline:** "Start your first council."  
**Visual:** Concentric rings expanding outward from center dot.  
**Animation sequence:**
1. Inner ring expands + fades (scale 0.3→1, opacity 1→0.2, 800ms loop)
2. Mid ring same, 200ms delay
3. Outer ring same, 400ms delay
4. Headline fades up (300ms)
5. Primary CTA scales 0.9→1 (300ms, 150ms delay)
6. Ghost "Learn more" link fades (200ms, 300ms delay)

**Buttons:** "Try the Council →" (accent filled) · "Learn more" (ghost, muted)

---

## Navigation

### Top Nav (fixed)

```
[hexal]                    The Council · Oracle · Sign in · [Try free]
```

- Position: `fixed top-0`, full width, `z-50`
- Background: transparent always (no blur, no frosted glass)
- Opacity: 0.4 during mid scenes (02–06), 1.0 at scene 01 and 07
- Transition: opacity 300ms ease
- Logo: Space Grotesk 600, `#f5f1ed`
- Links: Inter 500, `#a89080`, hover opacity 1.0
- "Try free" button: accent bg, `#fff` text, small (px-3 py-1.5, text-xs)

### Scene Progress (fixed right)

- 7 dots, vertical stack, right edge, centered vertically
- Inactive: 6×6px circle, `#3a3a3a`
- Active: 6×20px pill, `#6290c3`, transition width 300ms
- Click → scroll to scene (JS `scrollIntoView`)

---

## Motion Specification

### Global

```css
/* Easing — per CLAUDE.md */
--ease-spring: cubic-bezier(0.16, 1, 0.3, 1);

/* Scroll container */
.scene-container {
  height: 100svh;
  overflow-y: scroll;
  scroll-snap-type: y mandatory;
}

/* Each scene */
.scene {
  height: 100svh;
  scroll-snap-align: start;
  position: relative;
  overflow: hidden;
}
```

### Entrance trigger

`IntersectionObserver` on each scene with `threshold: 0.5`. When intersecting: add `.animate` class → CSS animations run. Animations are one-shot (no reverse on exit).

### Reduced motion

```css
@media (prefers-reduced-motion: reduce) {
  .scene * { animation: none !important; transition: none !important; }
}
```

### SVG draw pattern

```css
.svg-draw {
  stroke-dasharray: var(--path-length);
  stroke-dashoffset: var(--path-length);
  animation: draw 600ms var(--ease-spring) forwards;
}
@keyframes draw {
  to { stroke-dashoffset: 0; }
}
```

### Micro-interactions

- CTA hover: `scale(1.02)`, 150ms
- CTA active: `scale(0.98)`, 80ms
- All via CSS `:hover`/`:active`, no JS

---

## File Structure

```
frontend/src/
├── app/
│   ├── layout.tsx          # Font setup (Space Grotesk, Inter, JetBrains Mono)
│   └── page.tsx            # SceneContainer + all scenes
├── components/landing/
│   ├── SceneContainer.tsx  # scroll-snap wrapper + IntersectionObserver setup
│   ├── SceneNav.tsx        # Fixed progress dots + fixed top nav
│   └── scenes/
│       ├── HeroScene.tsx
│       ├── ProblemScene.tsx
│       ├── CouncilScene.tsx
│       ├── OracleScene.tsx
│       ├── RelayScene.tsx
│       ├── WorkflowScene.tsx
│       └── CtaScene.tsx
└── styles/
    └── globals.css         # CSS vars, scroll-snap, animation keyframes
```

---

## Component Contracts

### `SceneContainer`

```tsx
// Wraps all scenes. Sets up IntersectionObserver on all [data-scene] elements.
// Observer adds `.animate` class when scene reaches threshold: 0.5.
// Tracks activeScene index in state, exposes via SceneContext for SceneNav.
interface SceneContainerProps {
  children: React.ReactNode
}
```

### Each `*Scene`

```tsx
// No props needed for animation — IntersectionObserver adds `.animate`
// class directly to the scene DOM element via `data-scene` attribute.
// Self-contained SVG + headline + optional CTA.
// Export as default, no required props.
export default function HeroScene() { ... }
```

### `SceneNav`

```tsx
// Fixed top nav + fixed right progress dots.
// Reads activeScene from context. Handles dot click → scrollIntoView.
```

---

## Constraints

- No new npm packages (hexal-stack-constraints)
- No GSAP (removed from project)
- No `any` in TypeScript
- All SVGs inline (no external files) — needed for CSS animation of stroke properties
- `next/font/google` only for font loading
- No auth required on landing — public route

---

## Out of Scope

- Mobile responsive layout (desktop-first for now, mobile pass later)
- Dark/light toggle
- Internationalization
- Auth flows (login/signup pages separate)
