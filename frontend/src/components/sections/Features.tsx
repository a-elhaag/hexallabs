"use client";

import { useEffect, useRef, forwardRef, useImperativeHandle } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import {
  Users, Crosshair, ArrowRightLeft,
  Workflow as WorkflowIcon, Search, Zap,
  type LucideIcon,
} from "lucide-react";

gsap.registerPlugin(ScrollTrigger);

interface Feature { name: string; Icon: LucideIcon; desc: string; }

const FEATURES: Feature[] = [
  { name: "The Council",     Icon: Users,          desc: "2–7 models run in parallel. Anonymous peer review. Apex synthesizes weighted by confidence." },
  { name: "Oracle",          Icon: Crosshair,      desc: "Single model, direct response. Fast and focused when the full council isn't needed."          },
  { name: "The Relay",       Icon: ArrowRightLeft, desc: "Mid-generation handoff. One model starts, another takes over. Context fully preserved."       },
  { name: "Workflow",        Icon: WorkflowIcon,   desc: "Node-based pipeline. Chain models and tools — output of each step feeds the next."            },
  { name: "Scout",           Icon: Search,         desc: "Web search injected as context before models respond. Always grounded in real data."          },
  { name: "Primal Protocol", Icon: Zap,            desc: "Toggle on any mode. Apex rewrites synthesis in brutally compressed, signal-dense form."       },
];

const COLS = 3;
const ROWS = 2;

function colsFor(idx: number) {
  return Array.from({ length: COLS }, (_, i) => (i === idx % COLS ? "2fr" : "0.55fr")).join(" ");
}
function rowsFor(idx: number) {
  return Array.from({ length: ROWS }, (_, i) => (i === Math.floor(idx / COLS) ? "2fr" : "0.55fr")).join(" ");
}

interface CardRefs {
  card:   HTMLDivElement;
  accent: HTMLDivElement;
  ghost:  HTMLDivElement;
  icon:   HTMLDivElement;
  name:   HTMLDivElement;
  desc:   HTMLParagraphElement;
}

const FeatureCard = forwardRef<CardRefs, { feature: Feature; initialActive: boolean }>(
  function FeatureCard({ feature, initialActive }, ref) {
    const { name, Icon, desc } = feature;

    const cardRef   = useRef<HTMLDivElement>(null);
    const accentRef = useRef<HTMLDivElement>(null);
    const ghostRef  = useRef<HTMLDivElement>(null);
    const iconRef   = useRef<HTMLDivElement>(null);
    const nameRef   = useRef<HTMLDivElement>(null);
    const descRef   = useRef<HTMLParagraphElement>(null);

    useImperativeHandle(ref, () => ({
      card:   cardRef.current!,
      accent: accentRef.current!,
      ghost:  ghostRef.current!,
      icon:   iconRef.current!,
      name:   nameRef.current!,
      desc:   descRef.current!,
    }));

    return (
      <div
        ref={cardRef}
        className="relative overflow-hidden rounded-card cursor-pointer select-none"
        style={{
          background:  "#faf7f4",
          border:      "1.5px solid rgba(168,144,128,0.13)",
          boxShadow:   initialActive ? "0 28px 72px rgba(0,0,0,0.28)" : "0 1px 6px rgba(0,0,0,0.07)",
        }}
      >
        <div ref={accentRef} style={{ display: "none" }} />

        {/* Ghost icon — invisible until activated */}
        <div
          ref={ghostRef}
          className="pointer-events-none absolute right-0 bottom-0 text-muted"
          style={{ opacity: 0, transform: "translate(20px, 20px) scale(0.8)" }}
        >
          <Icon size={160} strokeWidth={0.55} />
        </div>

        {/* Content */}
        <div className="relative z-10 flex flex-col items-center justify-center h-full gap-4 p-8 text-center">

          {/* Small icon — hidden from paint on active card */}
          <div
            ref={iconRef}
            className="text-accent"
            style={{ opacity: initialActive ? 0 : 1 }}
          >
            <Icon size={48} strokeWidth={1.2} />
          </div>

          {/* Name */}
          <div
            ref={nameRef}
            className="font-extrabold tracking-tight leading-[1.1]"
            style={{
              color:    initialActive ? "var(--color-accent)" : "#111111",
              fontSize: initialActive ? "1.65rem"             : "1.05rem",
            }}
          >
            {name}
          </div>

          {/* Desc — out of flow when inactive so siblings stay truly centered */}
          <p
            ref={descRef}
            className="text-[0.8rem] font-medium text-[#7a6a62] leading-[1.72] max-w-[18rem]"
            style={{ opacity: initialActive ? 1 : 0, display: initialActive ? "block" : "none" }}
          >
            {desc}
          </p>
        </div>
      </div>
    );
  }
);

// Instantly reset a card to inactive state, killing any in-progress tweens
function collapseInstant(refs: CardRefs) {
  gsap.killTweensOf([refs.accent, refs.ghost, refs.icon, refs.name, refs.desc, refs.card]);
  gsap.set(refs.accent, { height: 0 });
  gsap.set(refs.ghost,  { opacity: 0, scale: 0.8, x: 20, y: 20 });
  gsap.set(refs.name,   { color: "#111111", fontSize: "1.05rem" });
  gsap.set(refs.desc,   { opacity: 0, y: 6, display: "none" });
  gsap.set(refs.card,   { boxShadow: "0 1px 6px rgba(0,0,0,0.07)", borderColor: "rgba(168,144,128,0.13)" });
  gsap.set(refs.icon,   { opacity: 1, scale: 1, y: 0 });
}

function expand(idx: number, refs: CardRefs, gridEl: HTMLDivElement | null) {
  const tl = gsap.timeline();

  if (gridEl) {
    tl.to(gridEl, {
      gridTemplateColumns: colsFor(idx),
      gridTemplateRows:    rowsFor(idx),
      duration: 0.85,
      ease: "power3.out",
    }, 0);
  }

  tl.to(refs.card, {
    boxShadow:   "0 28px 72px rgba(0,0,0,0.28)",
    borderColor: "rgba(98,144,195,0.4)",
    duration: 0.6, ease: "power2.out",
  }, 0);

  // Content enters after grid mostly settled
  tl.to(refs.icon, { opacity: 0, scale: 0.5, y: -10, duration: 0.25, ease: "power2.in" }, 0.6);
  tl.to(refs.name, { color: "var(--color-accent)", fontSize: "1.65rem", duration: 0.45, ease: "power2.inOut" }, 0.62);
  tl.fromTo(refs.ghost,
    { opacity: 0, scale: 0.75, x: 20, y: 20 },
    { opacity: 0.14, scale: 1.2, x: 12, y: 12, duration: 0.55, ease: "power2.out" },
    0.68
  );
  tl.set(refs.desc, { display: "block" }, 0.72);
  tl.fromTo(refs.desc,
    { opacity: 0, y: 8 },
    { opacity: 1, y: 0, duration: 0.5, ease: "power2.out" },
    0.72
  );

  return tl;
}

function collapse(refs: CardRefs) {
  const tl = gsap.timeline();
  tl.to(refs.desc,   { opacity: 0, y: 6, duration: 0.2, ease: "power2.in" }, 0);
  tl.set(refs.desc,  { display: "none" }, 0.2);
  tl.to(refs.ghost,  { opacity: 0, scale: 0.8, duration: 0.2, ease: "power2.in" }, 0);
  tl.to(refs.name,   { color: "#111111", fontSize: "1.05rem", duration: 0.32, ease: "power2.inOut" }, 0);
  tl.to(refs.card,   { boxShadow: "0 1px 6px rgba(0,0,0,0.07)", borderColor: "rgba(168,144,128,0.13)", duration: 0.4 }, 0);
  tl.fromTo(refs.icon,
    { opacity: 0, scale: 0.5, y: -10 },
    { opacity: 1, scale: 1, y: 0, duration: 0.38, ease: "power2.out" },
    0.24
  );
  return tl;
}

export function Features() {
  const sectionRef = useRef<HTMLDivElement>(null);
  const gridRef    = useRef<HTMLDivElement>(null);
  const cardRefs   = useRef<(CardRefs | null)[]>([]);
  const activeIdx  = useRef(0);
  const tlRef      = useRef<gsap.core.Timeline | null>(null);

  function activateCard(idx: number) {
    if (idx === activeIdx.current) return;

    const prevIdx = activeIdx.current;
    activeIdx.current = idx;

    tlRef.current?.kill();

    // Any card that's neither prev nor next: instant reset (avoids stuck mid-animation state)
    cardRefs.current.forEach((refs, i) => {
      if (refs && i !== prevIdx && i !== idx) collapseInstant(refs);
    });

    const prev = cardRefs.current[prevIdx];
    const next = cardRefs.current[idx];
    if (!next) return;

    const tl = gsap.timeline();
    if (prev) tl.add(collapse(prev), 0);
    tl.add(expand(idx, next, gridRef.current), prev ? 0.15 : 0);
    tlRef.current = tl;
  }

  useEffect(() => {
    // Run initial expand (grid already at correct cols/rows in HTML, only animates content)
    const first = cardRefs.current[0];
    if (first) tlRef.current = expand(0, first, null); // null = skip grid animation on mount

    const st = ScrollTrigger.create({
      trigger: sectionRef.current,
      start:   "top top",
      end:     "bottom bottom",
      onUpdate(self) {
        const idx = Math.min(FEATURES.length - 1, Math.floor(self.progress * FEATURES.length));
        activateCard(idx);
      },
    });

    return () => {
      st.kill();
      tlRef.current?.kill();
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div ref={sectionRef} style={{ height: `${FEATURES.length * 90}vh` }} className="relative">
      <div className="sticky top-0 h-screen flex flex-col items-center justify-center gap-8 px-6">

        <div className="self-start w-full max-w-300 mx-auto px-4">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-[0.63rem] font-bold uppercase tracking-[0.18em] text-muted">Modes</span>
            <div className="w-10 h-px bg-[rgba(168,144,128,0.2)]" />
          </div>
          <h2 className="text-[2.4rem] font-extrabold text-surface tracking-tight leading-[1.08] mb-3">
            Pick your mode.
          </h2>
          <p className="text-[0.88rem] text-muted font-medium">
            Six ways to run a query. One platform.
          </p>
        </div>

        <div
          ref={gridRef}
          style={{
            display:             "grid",
            gridTemplateColumns: colsFor(0),
            gridTemplateRows:    rowsFor(0),
            gap:                 "1rem",
            width:               "min(1200px, 96vw)",
            height:              "clamp(480px, 72vh, 700px)",
          }}
        >
          {FEATURES.map((f, i) => (
            <FeatureCard
              key={f.name}
              ref={el => { cardRefs.current[i] = el; }}
              feature={f}
              initialActive={i === 0}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
