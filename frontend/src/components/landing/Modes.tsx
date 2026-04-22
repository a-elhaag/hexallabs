"use client";

import { useLayoutEffect, useMemo, useRef } from "react";
import { ensureGsap, prefersReducedMotion } from "~/lib/gsap";

interface Mode {
  name: string;
  tagline: string;
  body: string;
  illustration: "council" | "oracle" | "relay" | "workflow" | "scout" | "primal" | "forge" | "lens";
}

const MODES: Mode[] = [
  {
    name: "The Council",
    tagline: "Seven minds, one synthesis.",
    body:
      "Two to seven models run in parallel, peer-review each other anonymously, and Apex synthesizes weighted by final confidence.",
    illustration: "council",
  },
  {
    name: "Oracle",
    tagline: "One model. Straight answer.",
    body:
      "When you want a specialist, not a committee. Pick one model, get one response, with the same streaming UI as every other mode.",
    illustration: "oracle",
  },
  {
    name: "The Relay",
    tagline: "Mid-thought handoff.",
    body:
      "One model starts. When it hits a topic another handles better, it passes context and partial output down the line.",
    illustration: "relay",
  },
  {
    name: "Workflow",
    tagline: "Drag, drop, ship.",
    body:
      "Build pipelines of models and tools visually. Each node streams into the next. Council and Oracle are presets inside this system.",
    illustration: "workflow",
  },
  {
    name: "Scout",
    tagline: "Fresh facts, injected.",
    body:
      "Toggle web search as context. The council sees what the live web sees before any of them opens their mouths.",
    illustration: "scout",
  },
  {
    name: "Primal Protocol",
    tagline: "No filler. No fluff.",
    body:
      "Toggle on any mode. Apex compresses the final synthesis into brutally terse caveman-style. Same answer, a quarter of the tokens.",
    illustration: "primal",
  },
  {
    name: "Prompt Forge",
    tagline: "Before your query ever runs.",
    body:
      "Forge rewrites your prompt for clarity. You see the rewrite and accept, edit, or skip — all before a single token is spent.",
    illustration: "forge",
  },
  {
    name: "Prompt Lens",
    tagline: "How each mind read your question.",
    body:
      "After the answer ships, Lens shows how each model interpreted the prompt — so you can see where they agreed and where they split.",
    illustration: "lens",
  },
];

export function Modes() {
  const sectionRef = useRef<HTMLElement | null>(null);
  const rowRefs = useRef<Array<HTMLLIElement | null>>([]);

  const setRowRef = useMemo(
    () => (i: number) => (el: HTMLLIElement | null) => {
      rowRefs.current[i] = el;
    },
    [],
  );

  useLayoutEffect(() => {
    const { gsap } = ensureGsap();
    const rows = rowRefs.current.filter(
      (el): el is HTMLLIElement => el !== null,
    );
    if (rows.length === 0) return;
    if (prefersReducedMotion()) return;

    const ctx = gsap.context(() => {
      rows.forEach((row) => {
        gsap.fromTo(
          row,
          { opacity: 0, y: 48 },
          {
            opacity: 1,
            y: 0,
            duration: 0.7,
            ease: "power3.out",
            scrollTrigger: {
              trigger: row,
              start: "top 85%",
              toggleActions: "play none none reverse",
            },
          },
        );
      });
    }, sectionRef);

    return () => ctx.revert();
  }, []);

  return (
    <section
      ref={sectionRef}
      id="modes"
      className="relative mx-auto max-w-7xl px-5 py-24 sm:px-8 sm:py-36"
    >
      <div className="mb-16 max-w-2xl">
        <p className="font-mono text-xs tracking-[0.28em] uppercase text-[color:var(--color-accent)]">
          Modes
        </p>
        <h2 className="mt-3 text-balance text-3xl font-semibold tracking-tight sm:text-5xl">
          Eight ways to ask.
        </h2>
        <p className="mt-4 text-base text-[color:var(--color-muted)] sm:text-lg">
          One query, many shapes. Mix and match any of these on any question.
        </p>
      </div>

      <ul className="space-y-24 sm:space-y-36">
        {MODES.map((mode, i) => {
          const reverse = i % 2 === 1;
          return (
            <li
              key={mode.name}
              ref={setRowRef(i)}
              className={`grid items-center gap-10 md:grid-cols-2 md:gap-16 ${
                reverse ? "md:[&>*:first-child]:order-2" : ""
              }`}
            >
              <div className="relative aspect-[5/4] w-full overflow-hidden rounded-[2rem] border border-white/5 bg-gradient-to-br from-white/[0.04] to-transparent">
                <ModeIllustration kind={mode.illustration} />
              </div>
              <div className={reverse ? "md:pr-8" : "md:pl-8"}>
                <p className="font-mono text-xs tracking-[0.24em] uppercase text-[color:var(--color-muted)]">
                  {String(i + 1).padStart(2, "0")} / Mode
                </p>
                <h3 className="mt-3 text-balance text-3xl font-semibold tracking-tight sm:text-4xl">
                  {mode.name}
                </h3>
                <p className="mt-3 text-lg text-[color:var(--color-accent)] sm:text-xl">
                  {mode.tagline}
                </p>
                <p className="mt-4 text-base leading-relaxed text-[color:var(--color-muted)] sm:text-lg">
                  {mode.body}
                </p>
              </div>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

export default Modes;

/* -------------------------- Mode illustrations -------------------------- */

function ModeIllustration({ kind }: { kind: Mode["illustration"] }) {
  const label = kind.slice(0, 1).toUpperCase() + kind.slice(1);

  switch (kind) {
    case "council":
      return <CouncilIllus />;
    case "oracle":
      return <OracleIllus />;
    case "relay":
      return <RelayIllus />;
    case "workflow":
      return <WorkflowIllus />;
    case "scout":
      return <ScoutIllus />;
    case "primal":
      return <PrimalIllus />;
    case "forge":
      return <ForgeIllus />;
    case "lens":
      return <LensIllus />;
    default:
      return (
        <div className="flex h-full items-center justify-center text-sm text-[color:var(--color-muted)]">
          {label}
        </div>
      );
  }
}

function CouncilIllus() {
  const r = 74;
  const pts = [-90, -30, 30, 90, 150, 210].map((d) => {
    const rad = (d * Math.PI) / 180;
    return { x: Math.cos(rad) * r, y: Math.sin(rad) * r };
  });
  return (
    <svg viewBox="-160 -130 320 260" className="h-full w-full" aria-hidden>
      {pts.map((p, i) => {
        const next = pts[(i + 1) % pts.length]!;
        return (
          <line
            key={`e${i}`}
            x1={p.x}
            y1={p.y}
            x2={next.x}
            y2={next.y}
            stroke="var(--color-accent)"
            strokeOpacity="0.35"
            strokeWidth="1"
          />
        );
      })}
      {pts.map((p, i) => (
        <line
          key={`s${i}`}
          x1="0"
          y1="0"
          x2={p.x}
          y2={p.y}
          stroke="var(--color-accent)"
          strokeOpacity="0.25"
          strokeWidth="1"
        />
      ))}
      {pts.map((p, i) => (
        <polygon
          key={`h${i}`}
          transform={`translate(${p.x} ${p.y})`}
          points="-14,-24 14,-24 28,0 14,24 -14,24 -28,0"
          fill="var(--color-bg)"
          stroke="var(--color-muted)"
          strokeWidth="1.2"
        />
      ))}
      <polygon
        points="-22,-38 22,-38 44,0 22,38 -22,38 -44,0"
        fill="var(--color-accent)"
      />
    </svg>
  );
}

function OracleIllus() {
  return (
    <svg viewBox="-160 -130 320 260" className="h-full w-full" aria-hidden>
      <circle cx="0" cy="0" r="92" fill="none" stroke="var(--color-muted)" strokeOpacity="0.22" />
      <circle cx="0" cy="0" r="62" fill="none" stroke="var(--color-muted)" strokeOpacity="0.3" />
      <polygon
        points="-30,-52 30,-52 60,0 30,52 -30,52 -60,0"
        fill="var(--color-accent)"
      />
      <text
        x="0"
        y="7"
        textAnchor="middle"
        fontSize="18"
        fontWeight="700"
        fill="var(--color-surface)"
      >
        1
      </text>
    </svg>
  );
}

function RelayIllus() {
  return (
    <svg viewBox="-160 -110 320 220" className="h-full w-full" aria-hidden>
      {[-110, 0, 110].map((x, i) => (
        <g key={x}>
          <polygon
            transform={`translate(${x} 0)`}
            points="-24,-42 24,-42 48,0 24,42 -24,42 -48,0"
            fill={i === 1 ? "var(--color-accent)" : "var(--color-bg)"}
            stroke="var(--color-muted)"
            strokeWidth="1.2"
          />
        </g>
      ))}
      <path
        d="M -62 0 L -48 0 M 48 0 L 62 0"
        stroke="var(--color-accent)"
        strokeWidth="2"
        strokeDasharray="4 4"
      />
      <path
        d="M 58 -8 L 66 0 L 58 8"
        fill="none"
        stroke="var(--color-accent)"
        strokeWidth="2"
      />
    </svg>
  );
}

function WorkflowIllus() {
  return (
    <svg viewBox="-160 -130 320 260" className="h-full w-full" aria-hidden>
      {[
        { x: -100, y: -70, c: "var(--color-bg)" },
        { x: 100, y: -70, c: "var(--color-bg)" },
        { x: 0, y: 10, c: "var(--color-accent)" },
        { x: 0, y: 85, c: "var(--color-bg)" },
      ].map((n, i) => (
        <g key={i}>
          <rect
            x={n.x - 42}
            y={n.y - 20}
            width="84"
            height="40"
            rx="14"
            fill={n.c}
            stroke="var(--color-muted)"
            strokeOpacity="0.5"
          />
        </g>
      ))}
      <path
        d="M -100 -50 Q -100 -10 -20 0 M 100 -50 Q 100 -10 20 0 M 0 30 L 0 65"
        stroke="var(--color-accent)"
        strokeOpacity="0.7"
        strokeWidth="1.5"
        fill="none"
      />
    </svg>
  );
}

function ScoutIllus() {
  return (
    <svg viewBox="-160 -130 320 260" className="h-full w-full" aria-hidden>
      <circle cx="-40" cy="-20" r="54" fill="none" stroke="var(--color-muted)" strokeWidth="1.4" />
      <path
        d="M 5 25 L 60 80"
        stroke="var(--color-muted)"
        strokeWidth="5"
        strokeLinecap="round"
      />
      <path
        d="M -80 -20 A 40 25 0 0 0 0 -20"
        fill="none"
        stroke="var(--color-accent)"
        strokeWidth="1"
      />
      <path
        d="M -80 -20 A 40 15 0 0 1 0 -20"
        fill="none"
        stroke="var(--color-accent)"
        strokeWidth="1"
      />
      <line x1="-40" y1="-75" x2="-40" y2="35" stroke="var(--color-accent)" strokeWidth="1" />
    </svg>
  );
}

function PrimalIllus() {
  return (
    <svg viewBox="-160 -100 320 200" className="h-full w-full" aria-hidden>
      {[-110, -65, -20, 25, 70].map((y, i) => (
        <rect
          key={y}
          x={-120}
          y={y - 3}
          width={i === 2 ? 240 : 180 - i * 20}
          height="6"
          rx="3"
          fill="var(--color-muted)"
          opacity="0.45"
        />
      ))}
      <polygon
        transform="translate(90 0)"
        points="-22,-38 22,-38 44,0 22,38 -22,38 -44,0"
        fill="var(--color-accent)"
      />
      <text
        x="90"
        y="6"
        textAnchor="middle"
        fontSize="11"
        fontFamily="var(--font-mono)"
        fill="var(--color-surface)"
        letterSpacing="2"
      >
        UGH
      </text>
    </svg>
  );
}

function ForgeIllus() {
  return (
    <svg viewBox="-160 -110 320 220" className="h-full w-full" aria-hidden>
      <rect
        x="-130"
        y="-60"
        width="120"
        height="36"
        rx="18"
        fill="var(--color-bg)"
        stroke="var(--color-muted)"
        strokeOpacity="0.4"
      />
      <text
        x="-70"
        y="-36"
        textAnchor="middle"
        fontSize="12"
        fontFamily="var(--font-mono)"
        fill="var(--color-muted)"
      >
        raw...
      </text>
      <path
        d="M 10 -42 L 34 -42"
        stroke="var(--color-accent)"
        strokeWidth="1.5"
      />
      <path
        d="M 30 -48 L 38 -42 L 30 -36"
        fill="none"
        stroke="var(--color-accent)"
        strokeWidth="1.5"
      />
      <rect
        x="48"
        y="-60"
        width="120"
        height="36"
        rx="18"
        fill="var(--color-accent)"
      />
      <text
        x="108"
        y="-36"
        textAnchor="middle"
        fontSize="12"
        fontFamily="var(--font-mono)"
        fill="var(--color-surface)"
      >
        forged.
      </text>
      <polygon
        transform="translate(-20 55)"
        points="-32,-26 32,-26 50,0 32,26 -32,26 -50,0"
        fill="none"
        stroke="var(--color-muted)"
        strokeOpacity="0.55"
      />
      <text
        x="-20"
        y="58"
        textAnchor="middle"
        fontSize="11"
        fontFamily="var(--font-mono)"
        fill="var(--color-muted)"
      >
        PROMPT FORGE
      </text>
    </svg>
  );
}

function LensIllus() {
  return (
    <svg viewBox="-160 -110 320 220" className="h-full w-full" aria-hidden>
      <circle cx="0" cy="0" r="74" fill="none" stroke="var(--color-muted)" strokeOpacity="0.4" strokeWidth="1.5" />
      <circle cx="0" cy="0" r="46" fill="none" stroke="var(--color-accent)" strokeOpacity="0.7" strokeWidth="1.5" />
      {[-60, -20, 20, 60].map((a) => (
        <line
          key={a}
          x1="-110"
          y1={a}
          x2="110"
          y2={a}
          stroke="var(--color-muted)"
          strokeOpacity="0.2"
        />
      ))}
      {[
        { x: -80, y: -60, c: "var(--color-accent)" },
        { x: -20, y: -20, c: "var(--color-surface)" },
        { x: 35, y: 15, c: "var(--color-surface)" },
        { x: 75, y: 50, c: "var(--color-accent)" },
      ].map((p, i) => (
        <circle key={i} cx={p.x} cy={p.y} r="5" fill={p.c} />
      ))}
    </svg>
  );
}
