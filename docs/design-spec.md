# Hexal — Design Specification

**Version:** 1.0
**Target:** Light mode primary. Dark mode deferred.
**Intended use:** Hand to Claude Design (or any design agent) as a single source of truth for producing mockups, component variants, marketing pages, and in-app UI.

---

## 1. Product Summary

Hexal is a **horizontal LLM council platform**. A user submits a query; multiple anonymized AI models run in parallel, peer-review each other, and a chairman model ("Apex") synthesizes a final answer. The product also supports single-model ("Oracle"), model-handoff ("The Relay"), and node-pipeline ("Workflow") modes.

The design language is **calm, editorial, and technical**. Think: scientific journal meets cockpit instrument panel. Hexagons are the core geometric motif — the name, the council metaphor, and the grid topology all derive from them.

**Tone:** confident, precise, understated. Never playful, never corporate-techy. No stock AI sparkles. No gradients. No glassmorphism.

---

## 2. Design Principles

1. **Geometry over decoration.** Hexagons carry meaning (models, council positions, confidence). They are never decorative filler.
2. **Light as default, because models are heavy.** The interface is airy and recessive so streaming model output feels like the subject.
3. **Four colors, no more.** The palette is a constraint, not a starting point. Adding a fifth color is a design smell.
4. **Motion = state.** Every animation maps to a real system state (streaming, confidence change, handoff, synthesis). No ambient motion for vibe.
5. **Anonymity until reveal.** Models are shown as white-label identities (Apex, Swift, etc.). Real model attribution appears only on the `/about` page.
6. **Density without noise.** Show a lot of information, but use typography hierarchy and whitespace so the eye lands in one place at a time.

---

## 3. Color System

### 3.1 Core palette (hard cap — 4 colors)

| Token            | Hex       | Role                                                                 |
|------------------|-----------|----------------------------------------------------------------------|
| `--color-bg`     | `#f5f1ed` | Page background (light mode). Warm paper, not pure white.            |
| `--color-surface`| `#ffffff` | Elevated surfaces — cards, modals, input fields, nav on scroll.      |
| `--color-ink`    | `#2c2c2c` | Primary text, hex outlines, icons.                                   |
| `--color-muted`  | `#a89080` | Secondary text, borders, dividers, disabled state, scroll indicators.|
| `--color-accent` | `#6290c3` | Single interactive color — links, focus rings, Apex glow, CTA fills. |

> Note: the originally-specified palette used `#2c2c2c` as background (dark mode). For **light mode** we swap: `#f5f1ed` is the page, `#2c2c2c` becomes `--color-ink`. The accent and muted tokens do double duty across both themes.

### 3.2 Derived tokens (tints/shades allowed only of the above)

| Token                 | Value                             | Use                                             |
|-----------------------|-----------------------------------|-------------------------------------------------|
| `--color-ink-80`      | `#2c2c2c` @ 80% opacity           | Body paragraph text                             |
| `--color-ink-60`      | `#2c2c2c` @ 60% opacity           | Tertiary text, metadata                         |
| `--color-muted-40`    | `#a89080` @ 40% opacity           | Hairline dividers, inactive hex strokes         |
| `--color-muted-15`    | `#a89080` @ 15% opacity           | Background hex grid decoration                  |
| `--color-accent-20`   | `#6290c3` @ 20% opacity           | Accent hover wash, selection background         |
| `--color-accent-glow` | `#6290c3` + `blur(24px)` + 0.5 α  | Apex halo during synthesis                      |

**Forbidden:** no red/green/yellow semantic colors. Error, warn, success states use ink + muted + icon shape, not color.

### 3.3 Opacity scale

Use only: `1.0`, `0.8`, `0.6`, `0.4`, `0.15`, `0.08`. Interpolate motion opacities but never ship a static `0.73`.

---

## 4. Typography

### 4.1 Families

| Family            | Font                     | Use                                     |
|-------------------|--------------------------|-----------------------------------------|
| Sans (UI + body)  | **Inter**                | All text except code and model output   |
| Mono (technical)  | **JetBrains Mono**       | Model names in technical context, code, IDs, timestamps, confidence scores |

Both loaded via `next/font/google` with CSS variables: `--font-inter`, `--font-jetbrains-mono`.

### 4.2 Type scale

Modular, based on 16px root. **Light mode = higher contrast on small text** — never drop below `--color-ink-60` for body.

| Token          | Size   | Line-height | Weight | Tracking | Use                                  |
|----------------|--------|-------------|--------|----------|--------------------------------------|
| `text-display` | 72px   | 0.95        | 700    | -0.03em  | Hero headline (desktop)              |
| `text-h1`      | 48px   | 1.05        | 700    | -0.02em  | Section headers                      |
| `text-h2`      | 32px   | 1.15        | 600    | -0.015em | Sub-sections                         |
| `text-h3`      | 24px   | 1.3         | 600    | -0.01em  | Card titles, feature titles          |
| `text-lead`    | 20px   | 1.5         | 400    | 0        | Hero subtitle, section intros        |
| `text-body`    | 16px   | 1.6         | 400    | 0        | Paragraphs                           |
| `text-sm`      | 14px   | 1.5         | 400    | 0        | Secondary text, nav, footer          |
| `text-xs`      | 12px   | 1.4         | 500    | 0.05em   | Labels, eyebrows, timestamps (UPPER) |
| `text-mono-sm` | 13px   | 1.4         | 400    | 0        | Inline code, IDs, confidence scores  |

Mobile step-down: reduce `text-display` to 48px, `text-h1` to 36px. Everything else unchanged.

### 4.3 Typographic rules

- **One H1 per page.** Sections use H2.
- **Eyebrows** (small-caps uppercase label above headings) use `text-xs` + `--color-muted` + `letter-spacing: 0.1em`. Example: `— THE COUNCIL`.
- **Model names** in body copy are styled with JetBrains Mono at the same size: `The <code>Apex</code> model synthesizes…`
- **Numbers** (confidence 1–10, token counts) are always JetBrains Mono, tabular-nums.
- **Quotation marks** are typographic: “ ” ‘ ’ — never straight.
- **Em dashes** set with hair spaces: `word — word`, not `word--word`.

---

## 5. Spacing & Layout

### 5.1 Spacing scale (4px base)

`4, 8, 12, 16, 24, 32, 48, 64, 96, 128`

No arbitrary values. Use scale tokens.

### 5.2 Grid

- **Page container:** `max-width: 1280px`, `padding-x: 24px` (mobile) / `48px` (desktop), centered.
- **Columns:** 12-col on desktop, 6-col on tablet, 4-col on mobile.
- **Gutter:** 24px desktop, 16px mobile.

### 5.3 Vertical rhythm

- Section padding: `96px` top, `96px` bottom (desktop). `64px` on mobile.
- Between heading and body paragraph: `24px`.
- Between stacked paragraphs: `16px`.

### 5.4 Breakpoints

| Name | px      |
|------|---------|
| sm   | 640     |
| md   | 768     |
| lg   | 1024    |
| xl   | 1280    |
| 2xl  | 1536    |

---

## 6. The Hexagon System

The hexagon is the product's visual atom. It must be rendered consistently across contexts.

### 6.1 Geometry

- **Orientation:** flat-top (two sides horizontal).
- **Aspect ratio:** `width : height = 1 : 0.866` (a regular hexagon's math).
- **SVG points for a hex at origin, size `s`:** `0,s*0.5  s*0.25,0  s*0.75,0  s,s*0.5  s*0.75,s  s*0.25,s` (flat-top).

### 6.2 Sizes

| Name    | Side length | Use                                      |
|---------|-------------|------------------------------------------|
| hex-xs  | 12px        | Inline bullet, footer accent             |
| hex-sm  | 24px        | FAQ icon, nav logo                       |
| hex-md  | 48px        | Model grid cells (non-Apex)              |
| hex-lg  | 88px        | Apex hex in model grid                   |
| hex-xl  | 160px       | Feature-section hero hex                 |
| hex-2xl | 280px       | Landing hero center hex                  |

### 6.3 Hex states

| State       | Stroke                  | Fill                       | Motion                              |
|-------------|-------------------------|----------------------------|-------------------------------------|
| idle        | `--color-ink` @ 1px     | `none`                     | optional slow rotation (30s loop)   |
| active      | `--color-accent` @ 1.5px| `--color-accent-20`        | none                                |
| streaming   | `--color-accent` @ 1.5px| fills bottom→top as tokens arrive (progress wipe) | pulse 1.5s |
| apex        | `--color-accent` @ 2px  | `--color-accent-20`        | glow halo + slow rotation           |
| complete    | `--color-ink` @ 1px     | `--color-bg`               | subtle scale 1.02 → 1               |
| disabled    | `--color-muted-40`      | `none`                     | none                                |

### 6.4 Hex layouts

- **Council ring:** 6 outer hexes at 60° intervals + 1 Apex center. Outer hex center distance from Apex center = `hex-lg × 1.8`.
- **Workflow chain:** vertical stack of hexes with connecting line (1px `--color-muted`) between them.
- **Background grid:** 5% opacity `--color-muted`, hex-md size, honeycomb pattern, purely decorative.
- **Peer review connections:** dashed 1px `--color-accent` lines animated draw-in between hexes.

---

## 7. Motion & Animation

### 7.1 Timing

| Token        | Duration | Easing                                |
|--------------|----------|---------------------------------------|
| `motion-xs`  | 150ms    | `cubic-bezier(0.4, 0, 0.2, 1)`        |
| `motion-sm`  | 300ms    | `cubic-bezier(0.16, 1, 0.3, 1)`       |
| `motion-md`  | 600ms    | `cubic-bezier(0.16, 1, 0.3, 1)`       |
| `motion-lg`  | 1200ms   | `back.out(1.7)` (GSAP)                |
| `motion-idle`| 30000ms  | `linear`, `repeat: -1` (hex rotation) |

### 7.2 Interaction micro-motions

- **Button hover:** `scale(1.02)` + `transition: transform 150ms`
- **Button active:** `scale(0.98)`
- **Card hover:** `translateY(-4px)` + shadow-lg, 300ms
- **Input focus:** animated 1px bottom border in `--color-accent`, 200ms
- **Link hover:** `--color-accent` text + underline slide-in

### 7.3 Scroll choreography (landing page)

- Triggered via GSAP ScrollTrigger.
- Entrance reveals: `opacity 0 → 1`, `translateY(40px → 0)`, `scale(0.9 → 1)`, stagger children by 80ms.
- Pinned sections for Council/Peer Review demonstrations: pin for 1 viewport height while internal animation plays.
- Parallax hex grids: background hexes translate at 30% scroll speed.
- **Accessibility:** respect `prefers-reduced-motion`: disable rotation, shorten durations to 0ms, keep only opacity changes.

### 7.4 Streaming token animation

When a model streams tokens:
- Hex stroke pulses: 1.5s loop, 1px → 2px → 1px.
- Hex fill rises bottom-to-top as % of tokens received (if known) or as a breathing wave if unknown length.
- Text appears character-by-character with no typewriter cursor — just fade-in per token.

---

## 8. Components

### 8.1 Button

| Variant    | Background          | Text            | Border                     | Use                       |
|------------|---------------------|-----------------|----------------------------|---------------------------|
| primary    | `--color-accent`    | `--color-surface`| none                      | Main CTA ("Enter Council")|
| secondary  | `--color-surface`   | `--color-ink`   | 1px `--color-ink`          | Neutral action            |
| ghost      | transparent         | `--color-ink`   | 1px `--color-muted-40`     | Cancel, secondary in modals|
| text       | transparent         | `--color-accent`| none                       | "Learn more →"            |

- Height: 44px (desktop), 48px (mobile tap target).
- Padding: 16px 24px.
- Border radius: **0**. Buttons are sharp rectangles — Hexal does not round.
- Text: `text-sm`, weight 500, no transform.

### 8.2 Input

- 48px height, 16px padding, 1px `--color-muted` border, border-radius 0.
- Focus: border-bottom thickens to 2px `--color-accent`, other borders fade to `--color-muted-40`.
- Label: `text-xs` uppercase eyebrow above input, 8px gap.
- Placeholder: `--color-muted`.

### 8.3 Card

- Background `--color-surface` (#fff).
- Border 1px `--color-muted-40`.
- Padding 32px desktop, 24px mobile.
- Border-radius 0.
- Hover: `translateY(-4px)`, shadow `0 12px 32px rgba(44,44,44,0.08)`.

### 8.4 Navigation

- **Transparent on hero**, becomes `--color-surface` with 1px bottom border `--color-muted-40` after 60px scroll.
- Height 72px.
- Logo: `hex-sm` + wordmark "Hexal" in Inter 500 20px.
- Links: `text-sm`, `--color-ink-80`, hover → `--color-ink`.
- CTA: primary button "Enter Council".
- Mobile: burger icon (3 lines → X), drawer slides from right, full-height, `--color-surface` bg.

### 8.5 FAQ accordion

- Each item is a full-width row separated by 1px `--color-muted-40` top border.
- Question row: `text-lead` (20px), 500 weight, 24px vertical padding.
- Trigger: hex-sm icon on the right, `+` inside (ink), rotates 90° and becomes `−` when open.
- Answer: `text-body`, `--color-ink-80`, 4px left border in `--color-accent`, 24px left padding, fade+height expand in 300ms.
- Only one open at a time (optional — spec allows multi-open; default to single).

### 8.6 Footer

- Background `--color-bg` with 1px top border `--color-muted-40`.
- Three-column grid desktop, single-column mobile.
- Column 1: hex logo + tagline + copyright.
- Column 2: Product links (Council, Oracle, Relay, Workflow).
- Column 3: About links (About, Privacy, Terms, GitHub).
- Bottom strip: hex divider SVG repeating + "© 2026 Hexal. All models anonymized." in `text-xs`.

### 8.7 Model hex cell

A model "cell" shown in the council grid or model row:

```
┌────────────────┐
│   [hex SVG]    │  ← hex-lg for Apex, hex-md for others
│                │
│   Apex         │  ← Inter 600 16px
│   Chairman     │  ← Inter 400 13px, --color-muted
│                │
│   [conf: 8.4]  │  ← JetBrains Mono, only when active
└────────────────┘
```

---

## 9. Page Specifications

### 9.1 Landing page

Sections, top to bottom:

1. **Nav** (sticky) — see 8.4
2. **Hero**
   - Fullscreen minus nav.
   - Center: hex-2xl concentric rings (outer, middle, inner), slow rotation.
   - Left-aligned text: eyebrow "— HEXAL", headline "Seven minds. / One answer.", lead paragraph, primary CTA + text-link secondary.
   - Bottom: scroll indicator (vertical line + mouse SVG, 600ms fade).
3. **ScrollFeatures** (4 pinned panels)
   - Each panel: split layout, text left (eyebrow + h2 + lead + text-link), hex cluster right.
   - Panels:
     1. **The Council** — 6-hex ring + Apex center, peer-review lines animate.
     2. **Oracle** — single hex with progressive fill.
     3. **The Relay** — two hexes horizontally with animated handoff arrow.
     4. **Workflow** — vertical chain of 4 hexes with connecting lines.
4. **ModelsRow** — 7-column grid (collapses to 2-col mobile), hex + name + role per model, stagger reveal on scroll.
5. **FAQ** — see 8.5, max-width 800px, centered.
6. **CTA band** — centered hex, headline "Ready to assemble your council?", primary + text-link.
7. **Footer** — see 8.6.

### 9.2 Query page (`/council`)

- Left sidebar (280px): past queries list, JetBrains Mono timestamps, hover reveals hex indicator.
- Main: query input at top (full width, `text-lead` size), model selector below (hex-md row, click to toggle, selected = accent border).
- Below input: live council view.
  - Desktop: honeycomb layout with Apex centered.
  - Mobile: vertical stack of model rows.
- Each model hex shows streaming fill + confidence number in JetBrains Mono.
- Peer review phase: dashed lines animate between hexes carrying "critique" tokens.
- Apex synthesis: all outer hexes dim, Apex glows, synthesized text appears below the hex in a full-width card.
- "Prompt Lens" button bottom-right → slide-in panel from right (420px) showing per-model interpretation breakdown.

### 9.3 Workflow builder (`/workflow`)

- Canvas: tiled hex-grid background at 5% opacity.
- Draggable nodes (hex cells with label + port dots top/bottom).
- Edges: 1px `--color-ink` lines, curve with bezier, animated flow dots during execution.
- Right panel (320px): node inspector — node type, model choice (dropdown styled as 8.2 input), system prompt textarea, caching toggle.
- Top toolbar: Save, Run, Reset buttons (secondary variant).

### 9.4 About (`/about`)

- Editorial layout, narrow column (720px).
- Introduces each white-label model with its real model backing revealed here and nowhere else.
- Layout: two-col rows — hex on left, model paragraph right, alternating sides.

---

## 10. Iconography

- Icons are **line-based**, 1.5px stroke, `--color-ink`, no fill.
- Source: Lucide or Phosphor (thin variant). No mixing icon sets.
- Icon sizes: 16px (inline), 20px (buttons), 24px (nav).
- Custom icons: hexagon variants (hex with dot, hex with line, hex with check) drawn as SVGs.

---

## 11. Imagery & Illustration

- **No photos.** Hexal is a product about abstract synthesis — photos undermine the metaphor.
- **No AI-generated art.** Ironic given the product, but essential to the brand's trustworthiness.
- **Diagrams only.** Line diagrams built from hexes, straight lines, and text. 1px stroke. Labels in JetBrains Mono.
- **Emoji: never** in UI. Only in plain-text error logs if absolutely necessary.

---

## 12. Accessibility

### 12.1 Contrast

- Body text (`--color-ink-80` on `--color-bg`): ratio 11.1:1 ✓ WCAG AAA.
- Accent text (`--color-accent` on `--color-bg`): ratio 3.9:1 ✗ AA large only. → **use accent only for interactive elements 18px+ or as border/icon, never small body text.**
- Muted text (`--color-muted` on `--color-bg`): ratio 2.6:1 ✗. → **muted is for decorative borders and tertiary metadata only. Never for content.**

### 12.2 Focus

- All interactive elements: visible focus ring, 2px `--color-accent`, 2px offset.
- Focus order matches visual order.
- Skip-to-main link at top, hidden until focused.

### 12.3 Motion

- `prefers-reduced-motion: reduce` → disable all hex rotations, parallax, and scroll-pin animations. Opacity transitions only.
- No auto-playing motion longer than 5s without user interaction trigger.

### 12.4 Keyboard

- Hex model selectors navigable via arrow keys in a grid pattern.
- FAQ accordions open/close with Enter and Space.
- Modals trap focus and restore on close.

### 12.5 Screen readers

- Hex SVGs get `aria-hidden="true"` unless they convey unique meaning.
- Model cells labeled: `"Apex, Chairman, confidence 8.4"`.
- Streaming regions use `aria-live="polite"`.

---

## 13. Content & Copy Style

- **Clipped declarative sentences.** "Seven minds. One answer." not "We bring you the power of seven different AI models."
- **No second person imperatives unless CTA.** Body copy uses third person or first-person plural sparingly.
- **Feature names capitalized, always as proper nouns:** The Council, Oracle, The Relay, Primal Protocol, Scout, Workflow, Prompt Forge, Prompt Lens.
- **Model names capitalized, always Title Case:** Apex, Swift, Prism, Depth, Atlas, Horizon, Pulse.
- **Never use the words:** "powered by AI", "revolutionary", "next-gen", "cutting-edge", "GPT", "Claude" (in marketing copy), "LLM" (outside technical docs).
- **Numerals for 10+**, spelled-out for ≤ 9 (editorial), **except** model counts: "7 models" always numeric.

---

## 14. Tokens file (hand-off format for Claude Design)

```json
{
  "color": {
    "bg":       "#f5f1ed",
    "surface":  "#ffffff",
    "ink":      "#2c2c2c",
    "muted":    "#a89080",
    "accent":   "#6290c3"
  },
  "font": {
    "sans": "Inter, system-ui, sans-serif",
    "mono": "JetBrains Mono, ui-monospace, monospace"
  },
  "radius": {
    "none": "0"
  },
  "space": [0, 4, 8, 12, 16, 24, 32, 48, 64, 96, 128],
  "breakpoints": { "sm": 640, "md": 768, "lg": 1024, "xl": 1280, "2xl": 1536 },
  "motion": {
    "xs":   { "ms": 150,   "ease": "cubic-bezier(0.4,0,0.2,1)" },
    "sm":   { "ms": 300,   "ease": "cubic-bezier(0.16,1,0.3,1)" },
    "md":   { "ms": 600,   "ease": "cubic-bezier(0.16,1,0.3,1)" },
    "lg":   { "ms": 1200,  "ease": "back.out(1.7)" },
    "idle": { "ms": 30000, "ease": "linear", "loop": true }
  },
  "hex": {
    "orientation": "flat-top",
    "sizes": { "xs": 12, "sm": 24, "md": 48, "lg": 88, "xl": 160, "2xl": 280 }
  }
}
```

---

## 15. Dark mode (deferred)

Reserved for a later iteration. The original palette (`#2c2c2c` bg, `#f5f1ed` ink) is the explicit dark-mode plan. No other tokens change. Ship light mode first; do not build dark-mode toggles speculatively.

---

## 16. Things to never design

- Dashboards with gauges.
- Pricing tables.
- "Trusted by" logo bars.
- Testimonial carousels.
- Confetti, sparkles, or celebration motion.
- Chatbot bubbles with avatars.
- Emoji reactions.
- Any element that rounds a corner.

---

## 17. Deliverables checklist for Claude Design

When handing this spec off, expect back:
- [ ] Landing page (full scroll) — desktop + mobile
- [ ] Query page (`/council`) — empty state, streaming state, synthesis state
- [ ] Workflow builder (`/workflow`)
- [ ] About page (`/about`)
- [ ] Nav variants (transparent, scrolled, mobile drawer)
- [ ] Button + Input + Card + FAQ component sheet
- [ ] Hex state sheet (all 6 states × 3 sizes)
- [ ] Motion reference (video or prototype) for hex streaming and council peer-review lines
- [ ] Icon set (line, 1.5px, hex-based custom icons)
- [ ] Token file (JSON, matching section 14)

---

**End of spec.**
