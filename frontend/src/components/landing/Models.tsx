"use client";

import { useLayoutEffect, useMemo, useRef, useState } from "react";
import { ensureGsap, prefersReducedMotion } from "~/lib/gsap";
import { Hex } from "./Hex";

interface ModelSpec {
  name: string;
  role: string;
  blurb: string;
}

const APEX: ModelSpec = {
  name: "Apex",
  role: "Chairman",
  blurb: "Synthesizes the council's final answer, weighted by confidence.",
};

const OUTER: ModelSpec[] = [
  { name: "Swift", role: "Fast organizer", blurb: "Quick structure, fast drafts, efficient at triage." },
  { name: "Prism", role: "Reasoning", blurb: "Breaks problems into clean logical facets." },
  { name: "Depth", role: "Deep analysis", blurb: "Patience over speed. Finds what the others miss." },
  { name: "Atlas", role: "Open-source", blurb: "Transparent weights. A different point of view." },
  { name: "Horizon", role: "Long context", blurb: "Holds the whole document in its head at once." },
  { name: "Pulse", role: "Latest reasoning", blurb: "Cutting-edge reasoning, fresh from the frontier." },
];

// percent positions of each outer hex inside the square stage
const OUTER_POSITIONS = [
  { top: "12%", left: "50%" },
  { top: "32%", left: "82%" },
  { top: "68%", left: "82%" },
  { top: "88%", left: "50%" },
  { top: "68%", left: "18%" },
  { top: "32%", left: "18%" },
];

export function Models() {
  const sectionRef = useRef<HTMLElement | null>(null);
  const stageRef = useRef<HTMLDivElement | null>(null);
  const apexRef = useRef<HTMLDivElement | null>(null);
  const outerRefs = useRef<Array<HTMLDivElement | null>>([]);
  const [flipped, setFlipped] = useState<number | null>(null);

  const setOuterRef = useMemo(
    () => (i: number) => (el: HTMLDivElement | null) => {
      outerRefs.current[i] = el;
    },
    [],
  );

  useLayoutEffect(() => {
    const { gsap } = ensureGsap();
    const stage = stageRef.current;
    const apex = apexRef.current;
    const outers = outerRefs.current.filter(
      (el): el is HTMLDivElement => el !== null,
    );
    if (!stage || !apex || outers.length !== 6) return;

    if (prefersReducedMotion()) {
      gsap.set([apex, ...outers], { opacity: 1, x: 0, y: 0, scale: 1 });
      apex.classList.add("hex-glow-on");
      return;
    }

    // Compute directional offsets for assemble-from-edges effect
    const w = stage.clientWidth;
    const offsets = outers.map((_, i) => {
      const angle = ((i * 60 - 90) * Math.PI) / 180;
      const dist = w * 1.1;
      return { x: Math.cos(angle) * dist, y: Math.sin(angle) * dist };
    });

    gsap.set(apex, { opacity: 0, scale: 0.35, rotate: -30 });
    outers.forEach((el, i) => {
      gsap.set(el, {
        opacity: 0,
        scale: 0.4,
        x: offsets[i]?.x ?? 0,
        y: offsets[i]?.y ?? 0,
      });
    });

    const ctx = gsap.context(() => {
      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: stage,
          start: "top 70%",
          toggleActions: "play none none reverse",
        },
      });

      tl.to(outers, {
        opacity: 1,
        scale: 1,
        x: 0,
        y: 0,
        duration: 1,
        stagger: 0.08,
        ease: "power3.out",
      });
      tl.to(
        apex,
        { opacity: 1, scale: 1, rotate: 0, duration: 0.8, ease: "power3.out" },
        "-=0.4",
      );
      tl.add(() => apex.classList.add("hex-glow-on"), "+=0.05");
    }, sectionRef);

    return () => ctx.revert();
  }, []);

  return (
    <section
      ref={sectionRef}
      id="models"
      className="relative mx-auto max-w-7xl px-5 py-24 sm:px-8 sm:py-36"
    >
      <div className="grid items-center gap-12 md:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)] md:gap-20">
        <div>
          <p className="font-mono text-xs tracking-[0.28em] uppercase text-[color:var(--color-accent)]">
            The council
          </p>
          <h2 className="mt-3 text-balance text-3xl font-semibold tracking-tight sm:text-5xl">
            Seven specialists. <br />
            <span className="text-[color:var(--color-muted)]">One chair.</span>
          </h2>
          <p className="mt-5 max-w-lg text-base text-[color:var(--color-muted)] sm:text-lg">
            Each model brings a different strength. Tap a hex to see the role it
            plays. Real model attribution lives on the{" "}
            <a
              href="/about"
              className="text-[color:var(--color-surface)] underline-offset-4 hover:underline"
            >
              about page
            </a>
            .
          </p>
        </div>

        <div className="relative mx-auto w-full max-w-[520px]">
          <div
            ref={stageRef}
            className="relative mx-auto aspect-square w-full"
          >
            {/* Apex at center */}
            <button
              type="button"
              onClick={() => setFlipped(flipped === 0 ? null : 0)}
              className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 cursor-pointer focus:outline-none"
              aria-label={`${APEX.name} — ${APEX.role}`}
              aria-expanded={flipped === 0}
            >
              <Hex
                ref={apexRef}
                size={144}
                variant="solid"
                glow
                className="[&.hex-glow-on_.hex-clip]:!bg-[color:var(--color-accent)] [&.hex-glow-on_.hex-clip]:!text-[color:var(--color-surface)]"
              >
                {flipped === 0 ? (
                  <>
                    <span className="text-[0.62rem] leading-tight font-mono uppercase tracking-[0.14em] opacity-80">
                      {APEX.role}
                    </span>
                    <span className="mt-1 block max-w-[9ch] text-[0.62rem] leading-snug opacity-80">
                      {APEX.blurb}
                    </span>
                  </>
                ) : (
                  <>
                    <span className="text-lg font-semibold tracking-tight">
                      {APEX.name}
                    </span>
                    <span className="mt-1 font-mono text-[0.58rem] uppercase tracking-[0.14em] opacity-70">
                      Chairman
                    </span>
                  </>
                )}
              </Hex>
            </button>

            {/* 6 outer */}
            {OUTER.map((m, i) => {
              const pos = OUTER_POSITIONS[i]!;
              const isFlipped = flipped === i + 1;
              return (
                <button
                  key={m.name}
                  type="button"
                  onClick={() => setFlipped(isFlipped ? null : i + 1)}
                  className="absolute -translate-x-1/2 -translate-y-1/2 cursor-pointer focus:outline-none"
                  style={{ top: pos.top, left: pos.left }}
                  aria-label={`${m.name} — ${m.role}`}
                  aria-expanded={isFlipped}
                >
                  <Hex
                    ref={setOuterRef(i)}
                    size={110}
                    variant={isFlipped ? "solid" : "outline"}
                    className="transition-[transform] duration-300 hover:scale-[1.06] active:scale-[0.97]"
                  >
                    {isFlipped ? (
                      <>
                        <span className="text-[0.58rem] leading-tight font-mono uppercase tracking-[0.14em]">
                          {m.role}
                        </span>
                        <span className="mt-1 block max-w-[11ch] text-[0.6rem] leading-snug">
                          {m.blurb}
                        </span>
                      </>
                    ) : (
                      <>
                        <span className="text-base font-semibold tracking-tight">
                          {m.name}
                        </span>
                        <span className="mt-1 font-mono text-[0.54rem] uppercase tracking-[0.14em] opacity-70">
                          {m.role}
                        </span>
                      </>
                    )}
                  </Hex>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}

export default Models;
