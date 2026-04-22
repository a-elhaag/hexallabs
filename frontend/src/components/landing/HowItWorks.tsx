"use client";

import { useLayoutEffect, useMemo, useRef } from "react";
import { ensureGsap, prefersReducedMotion } from "~/lib/gsap";

type StageId = "ask" | "forge" | "council" | "review" | "synthesis";

interface Step {
  id: StageId;
  num: string;
  title: string;
  body: string;
}

const STEPS: Step[] = [
  {
    id: "ask",
    num: "01",
    title: "Ask",
    body: "You type a question. Big or small, vague or surgical — the council handles it either way.",
  },
  {
    id: "forge",
    num: "02",
    title: "Forge",
    body: "Prompt Forge rewrites your query for clarity before it hits the models. You review and edit in one click, or skip it.",
  },
  {
    id: "council",
    num: "03",
    title: "Council",
    body: "Two to seven models run in parallel. Each drafts an answer and self-rates its confidence from 1 to 10.",
  },
  {
    id: "review",
    num: "04",
    title: "Peer review",
    body: "Models see each other's answers anonymously, critique them, and adjust their own confidence. No hierarchy, no names.",
  },
  {
    id: "synthesis",
    num: "05",
    title: "Synthesis",
    body: "Apex weighs every response by final confidence and delivers one synthesized answer — with full transparency on who said what.",
  },
];

export function HowItWorks() {
  const sectionRef = useRef<HTMLElement | null>(null);
  const diagramRef = useRef<HTMLDivElement | null>(null);
  const stepRefs = useRef<Array<HTMLLIElement | null>>([]);

  const setStepRef = useMemo(
    () => (i: number) => (el: HTMLLIElement | null) => {
      stepRefs.current[i] = el;
    },
    [],
  );

  useLayoutEffect(() => {
    const { gsap, ScrollTrigger } = ensureGsap();
    const diagram = diagramRef.current;
    const steps = stepRefs.current.filter(
      (el): el is HTMLLIElement => el !== null,
    );
    if (!diagram || steps.length === 0) return;

    const reduced = prefersReducedMotion();
    const mm = gsap.matchMedia();

    // Desktop: scrub diagram stage + reveal each card
    mm.add("(min-width: 768px)", () => {
      if (reduced) return;
      const triggers: ScrollTrigger[] = [];

      steps.forEach((step, i) => {
        gsap.fromTo(
          step,
          { opacity: 0, y: 40 },
          {
            opacity: 1,
            y: 0,
            duration: 0.6,
            ease: "power3.out",
            scrollTrigger: {
              trigger: step,
              start: "top 80%",
              toggleActions: "play none none reverse",
            },
          },
        );
        const t = ScrollTrigger.create({
          trigger: step,
          start: "top 50%",
          end: "bottom 50%",
          onEnter: () => {
            diagram.dataset.stage = STEPS[i]?.id ?? "ask";
          },
          onEnterBack: () => {
            diagram.dataset.stage = STEPS[i]?.id ?? "ask";
          },
        });
        triggers.push(t);
      });

      return () => triggers.forEach((t) => t.kill());
    });

    // Mobile: fade in each row when it enters
    mm.add("(max-width: 767px)", () => {
      if (reduced) return;
      steps.forEach((step) => {
        gsap.fromTo(
          step,
          { opacity: 0, y: 32 },
          {
            opacity: 1,
            y: 0,
            duration: 0.6,
            ease: "power3.out",
            scrollTrigger: {
              trigger: step,
              start: "top 85%",
              toggleActions: "play none none reverse",
            },
          },
        );
      });
    });

    return () => {
      mm.revert();
    };
  }, []);

  return (
    <section
      ref={sectionRef}
      id="how"
      className="relative mx-auto max-w-7xl px-5 py-24 sm:px-8 sm:py-36"
    >
      <div className="mb-14 sm:mb-20">
        <p className="font-mono text-xs tracking-[0.28em] uppercase text-[color:var(--color-accent)]">
          How it works
        </p>
        <h2 className="mt-3 text-balance text-3xl font-semibold tracking-tight text-ink sm:text-5xl">
          A council, not a chatbot.
        </h2>
        <p className="mt-4 max-w-2xl text-base text-soft sm:text-lg">
          Five steps from your question to one synthesized answer.
        </p>
      </div>

      <div className="grid gap-12 md:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)] md:gap-20">
        <div className="hidden md:block">
          <div
            ref={diagramRef}
            data-stage="ask"
            className="sticky top-[18vh] aspect-square w-full rounded-[2.5rem] border border-soft bg-card p-6 shadow-card"
          >
            <Diagram />
          </div>
        </div>

        <ol className="space-y-10 md:space-y-40">
          {STEPS.map((step, i) => (
            <li
              key={step.id}
              ref={setStepRef(i)}
              className="relative rounded-3xl border border-soft bg-card p-7 text-ink shadow-card sm:p-9"
            >
              <div className="md:hidden mb-6 aspect-[4/3] rounded-2xl border border-soft bg-inset p-4">
                <Diagram inline stage={step.id} />
              </div>
              <div className="flex items-baseline gap-4">
                <span className="font-mono text-sm tracking-[0.18em] uppercase text-[color:var(--color-accent)]">
                  {step.num}
                </span>
                <h3 className="text-2xl font-semibold tracking-tight sm:text-3xl">
                  {step.title}
                </h3>
              </div>
              <p className="mt-4 text-base leading-relaxed text-ink/70 sm:text-lg">
                {step.body}
              </p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

export default HowItWorks;

/* ------------------------------ Diagram ------------------------------ */

function Diagram({ inline = false, stage }: { inline?: boolean; stage?: StageId }) {
  // 6 outer hex positions on a circle radius 110 centered at (0,0)
  const r = 110;
  const outers = [-90, -30, 30, 90, 150, 210].map((deg) => {
    const rad = (deg * Math.PI) / 180;
    return { x: Math.cos(rad) * r, y: Math.sin(rad) * r };
  });

  return (
    <svg
      viewBox="-180 -180 360 360"
      className="h-full w-full"
      aria-hidden
    >
      <defs>
        <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="4" result="b" />
          <feMerge>
            <feMergeNode in="b" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        <clipPath id="hexclip">
          <polygon points="-18,-31 18,-31 36,0 18,31 -18,31 -36,0" />
        </clipPath>
      </defs>

      <g
        className={inline ? `diagram-g stage-${stage ?? "ask"}` : "diagram-g"}
      >
        {/* spokes */}
        {outers.map((p, i) => (
          <line
            key={`s${i}`}
            x1="0"
            y1="0"
            x2={p.x}
            y2={p.y}
            stroke="currentColor"
            strokeWidth="1"
            className="spoke opacity-0 transition-opacity duration-500"
            style={{
              transitionTimingFunction: "var(--ease-hexal)",
              color: "var(--color-accent)",
            }}
          />
        ))}
        {/* ring */}
        {outers.map((p, i) => {
          const next = outers[(i + 1) % outers.length]!;
          return (
            <line
              key={`r${i}`}
              x1={p.x}
              y1={p.y}
              x2={next.x}
              y2={next.y}
              stroke="currentColor"
              strokeWidth="1"
              className="ring opacity-0 transition-opacity duration-500"
              style={{
                transitionTimingFunction: "var(--ease-hexal)",
                color: "var(--color-accent)",
              }}
            />
          );
        })}

        {/* outer hexes */}
        {outers.map((p, i) => (
          <g key={`h${i}`} transform={`translate(${p.x} ${p.y})`}>
            <g
              className="outer transition-[opacity,transform] duration-500"
              style={{
                transitionTimingFunction: "var(--ease-hexal)",
                transformOrigin: "center",
                transformBox: "fill-box",
              }}
            >
              <polygon
                points="-18,-31 18,-31 36,0 18,31 -18,31 -36,0"
                fill="var(--color-bg)"
                stroke="var(--color-muted)"
                strokeWidth="1.2"
              />
            </g>
          </g>
        ))}

        {/* center/apex */}
        <g
          className="apex transition-transform duration-500"
          style={{ transitionTimingFunction: "var(--ease-hexal)" }}
        >
          <polygon
            points="-26,-45 26,-45 52,0 26,45 -26,45 -52,0"
            fill="var(--color-accent)"
            className="apex-fill transition-[fill,filter] duration-500"
            filter="url(#glow)"
            style={{ transitionTimingFunction: "var(--ease-hexal)" }}
          />
          <text
            x="0"
            y="6"
            textAnchor="middle"
            fontSize="16"
            fontWeight="600"
            fill="var(--color-surface)"
          >
            Apex
          </text>
        </g>

        {/* query bubble (phase 1) */}
        <g className="query transition-opacity duration-500 opacity-0">
          <rect
            x="-60"
            y="-150"
            width="120"
            height="40"
            rx="20"
            fill="var(--color-bg)"
          />
          <text
            x="0"
            y="-124"
            textAnchor="middle"
            fontSize="14"
            fill="var(--color-surface)"
            fontFamily="var(--font-mono)"
          >
            &quot;ask...&quot;
          </text>
        </g>
      </g>

      <style>{`
        .diagram-g .outer { opacity: 0; }
        .diagram-g .apex { transform: scale(0.2); opacity: 0; }
        .diagram-g .apex-fill { fill: var(--color-muted); }

        /* Stage: ask */
        [data-stage="ask"] .query,
        .stage-ask .query { opacity: 1; }
        [data-stage="ask"] .apex,
        .stage-ask .apex { transform: scale(0.5); opacity: 0.3; }

        /* Stage: forge */
        [data-stage="forge"] .query,
        .stage-forge .query { opacity: 1; transform: translateY(20px); }
        [data-stage="forge"] .apex,
        .stage-forge .apex { transform: scale(0.65); opacity: 0.5; }

        /* Stage: council */
        [data-stage="council"] .apex,
        .stage-council .apex { transform: scale(0.75); opacity: 0.7; }
        [data-stage="council"] .outer,
        .stage-council .outer { opacity: 1; }
        [data-stage="council"] .spoke,
        .stage-council .spoke { opacity: 0.35; }

        /* Stage: review */
        [data-stage="review"] .apex,
        .stage-review .apex { transform: scale(0.8); opacity: 0.8; }
        [data-stage="review"] .outer,
        .stage-review .outer { opacity: 1; }
        [data-stage="review"] .spoke,
        .stage-review .spoke { opacity: 0.4; }
        [data-stage="review"] .ring,
        .stage-review .ring { opacity: 0.7; }

        /* Stage: synthesis */
        [data-stage="synthesis"] .apex,
        .stage-synthesis .apex { transform: scale(1.1); opacity: 1; }
        [data-stage="synthesis"] .apex-fill,
        .stage-synthesis .apex-fill { fill: var(--color-accent); }
        [data-stage="synthesis"] .outer,
        .stage-synthesis .outer { opacity: 0.2; transform: scale(0.5); }
        [data-stage="synthesis"] .spoke,
        .stage-synthesis .spoke { opacity: 0; }
        [data-stage="synthesis"] .ring,
        .stage-synthesis .ring { opacity: 0; }
      `}</style>
    </svg>
  );
}
