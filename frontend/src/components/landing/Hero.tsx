"use client";

import Link from "next/link";
import { useLayoutEffect, useMemo, useRef } from "react";
import { Hex } from "./Hex";
import { ensureGsap, prefersReducedMotion } from "~/lib/gsap";

const OUTER_ANGLES_DEG = [-90, -30, 30, 90, 150, 210];

const EDGES: Array<[number, number]> = [
  // Spokes: center (0) → each outer (1..6)
  [0, 1],
  [0, 2],
  [0, 3],
  [0, 4],
  [0, 5],
  [0, 6],
  // Ring: each outer to next (peer review)
  [1, 2],
  [2, 3],
  [3, 4],
  [4, 5],
  [5, 6],
  [6, 1],
];

export function Hero() {
  const rootRef = useRef<HTMLElement | null>(null);
  const stageRef = useRef<HTMLDivElement | null>(null);
  const apexRef = useRef<HTMLDivElement | null>(null);
  const outerRefs = useRef<Array<HTMLDivElement | null>>([]);
  const lineRefs = useRef<Array<SVGLineElement | null>>([]);
  const headlineRef = useRef<HTMLDivElement | null>(null);
  const ctasRef = useRef<HTMLDivElement | null>(null);
  const phase1HeadlineRef = useRef<HTMLDivElement | null>(null);

  const setOuterRef = useMemo(
    () => (i: number) => (el: HTMLDivElement | null) => {
      outerRefs.current[i] = el;
    },
    [],
  );

  const setLineRef = useMemo(
    () => (i: number) => (el: SVGLineElement | null) => {
      lineRefs.current[i] = el;
    },
    [],
  );

  useLayoutEffect(() => {
    const { gsap, ScrollTrigger } = ensureGsap();
    const root = rootRef.current;
    const stage = stageRef.current;
    const apex = apexRef.current;
    const outers = outerRefs.current.filter(
      (el): el is HTMLDivElement => el !== null,
    );
    const lines = lineRefs.current.filter(
      (el): el is SVGLineElement => el !== null,
    );
    const headline = headlineRef.current;
    const ctas = ctasRef.current;
    const phase1 = phase1HeadlineRef.current;

    if (!root || !stage || !apex || outers.length !== 6 || !headline || !ctas) {
      return;
    }

    const computePositions = () => {
      const w = stage.clientWidth;
      const h = stage.clientHeight;
      const r = Math.min(w, h) * 0.22;
      return OUTER_ANGLES_DEG.map((deg) => {
        const rad = (deg * Math.PI) / 180;
        return { x: Math.cos(rad) * r, y: Math.sin(rad) * r };
      });
    };

    // Initial state: everything collapsed at center, hidden
    gsap.set([apex, ...outers], {
      xPercent: -50,
      yPercent: -50,
      left: "50%",
      top: "50%",
      position: "absolute",
    });
    gsap.set(apex, { scale: 0.35, opacity: 0 });
    gsap.set(outers, { x: 0, y: 0, scale: 0.35, opacity: 0 });
    lines.forEach((line) => {
      const len = line.getTotalLength?.() ?? 400;
      gsap.set(line, {
        strokeDasharray: len,
        strokeDashoffset: len,
        opacity: 0.9,
      });
    });
    gsap.set([headline, ctas], { opacity: 0, y: 24 });
    if (phase1) gsap.set(phase1, { opacity: 0, y: 16 });

    const reduced = prefersReducedMotion();
    const mm = gsap.matchMedia();

    // Desktop: pinned scroll-scrub timeline
    mm.add("(min-width: 768px)", () => {
      if (reduced) {
        // Static final state
        gsap.set(apex, { opacity: 1, scale: 1.25 });
        apex.classList.add("hex-glow-on");
        gsap.set(outers, { opacity: 0.15, scale: 0.8 });
        gsap.set([headline, ctas], { opacity: 1, y: 0 });
        return;
      }

      const positions = computePositions();

      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: root,
          start: "top top",
          end: "bottom bottom",
          scrub: 0.8,
          pin: stage,
          pinSpacing: true,
          anticipatePin: 1,
          invalidateOnRefresh: true,
        },
      });

      // Phase 1 (0 → 0.12): Apex fades in
      tl.to(apex, { opacity: 1, scale: 1, duration: 0.12, ease: "power2.out" }, 0);
      if (phase1) {
        tl.to(phase1, { opacity: 1, y: 0, duration: 0.12 }, 0.03);
      }

      // Phase 2 (0.12 → 0.38): Six outer hexes fan out
      tl.to(
        outers,
        {
          opacity: 1,
          scale: 1,
          x: (i) => positions[i]?.x ?? 0,
          y: (i) => positions[i]?.y ?? 0,
          duration: 0.26,
          stagger: 0.025,
          ease: "power3.out",
        },
        0.12,
      );
      if (phase1) {
        tl.to(phase1, { opacity: 0, y: -12, duration: 0.08 }, 0.3);
      }

      // Phase 3 (0.38 → 0.66): peer-review lines draw
      tl.to(
        lines,
        {
          strokeDashoffset: 0,
          duration: 0.28,
          stagger: 0.018,
          ease: "power2.inOut",
        },
        0.38,
      );

      // Phase 4 (0.66 → 0.88): outers collapse, Apex glows
      tl.to(
        outers,
        {
          x: 0,
          y: 0,
          scale: 0.5,
          opacity: 0.12,
          duration: 0.2,
          ease: "power2.inOut",
        },
        0.66,
      );
      tl.to(
        lines,
        { opacity: 0, duration: 0.18, ease: "power2.in" },
        0.66,
      );
      tl.to(
        apex,
        { scale: 1.35, duration: 0.2, ease: "power2.out" },
        0.66,
      );
      tl.add(() => apex.classList.add("hex-glow-on"), 0.7);
      tl.add(() => apex.classList.remove("hex-glow-on"), 0.65);

      // Phase 5 (0.88 → 1.0): headline + CTAs
      tl.to(
        headline,
        { opacity: 1, y: 0, duration: 0.12, ease: "power2.out" },
        0.88,
      );
      tl.to(
        ctas,
        { opacity: 1, y: 0, duration: 0.12, ease: "power2.out" },
        0.92,
      );

      return () => {
        tl.scrollTrigger?.kill();
        tl.kill();
      };
    });

    // Mobile: autoplay once when hero in view
    mm.add("(max-width: 767px)", () => {
      if (reduced) {
        gsap.set(apex, { opacity: 1, scale: 1.15 });
        apex.classList.add("hex-glow-on");
        gsap.set(outers, { opacity: 0.18, scale: 0.85 });
        gsap.set([headline, ctas], { opacity: 1, y: 0 });
        return;
      }

      const positions = computePositions();

      const tl = gsap.timeline({
        paused: true,
        defaults: { ease: "power3.out" },
      });

      tl.to(apex, { opacity: 1, scale: 1, duration: 0.5 }, 0);
      if (phase1) tl.to(phase1, { opacity: 1, y: 0, duration: 0.4 }, 0.1);
      tl.to(
        outers,
        {
          opacity: 1,
          scale: 1,
          x: (i) => positions[i]?.x ?? 0,
          y: (i) => positions[i]?.y ?? 0,
          duration: 0.9,
          stagger: 0.06,
        },
        0.4,
      );
      tl.to(
        lines,
        { strokeDashoffset: 0, duration: 0.7, stagger: 0.04, ease: "power2.inOut" },
        1.0,
      );
      if (phase1) tl.to(phase1, { opacity: 0, y: -8, duration: 0.3 }, 1.5);
      tl.to(
        outers,
        { x: 0, y: 0, scale: 0.55, opacity: 0.12, duration: 0.6, ease: "power2.inOut" },
        1.9,
      );
      tl.to(lines, { opacity: 0, duration: 0.4 }, 1.9);
      tl.to(apex, { scale: 1.3, duration: 0.5 }, 1.9);
      tl.add(() => apex.classList.add("hex-glow-on"), 2.1);
      tl.to(headline, { opacity: 1, y: 0, duration: 0.5 }, 2.3);
      tl.to(ctas, { opacity: 1, y: 0, duration: 0.5 }, 2.5);

      const trigger = ScrollTrigger.create({
        trigger: root,
        start: "top 85%",
        once: true,
        onEnter: () => tl.play(),
      });

      return () => {
        trigger.kill();
        tl.kill();
      };
    });

    const onResize = () => ScrollTrigger.refresh();
    window.addEventListener("resize", onResize);

    return () => {
      window.removeEventListener("resize", onResize);
      mm.revert();
    };
  }, []);

  return (
    <section
      ref={rootRef}
      id="hero"
      className="relative md:h-[340vh]"
      aria-label="Hexal introduction"
    >
      <div
        ref={stageRef}
        className="relative flex h-screen w-full items-center justify-center overflow-hidden"
      >
        <div className="pointer-events-none absolute inset-0 -z-10">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(98,144,195,0.18),transparent_62%)]" />
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_20%_10%,rgba(168,144,128,0.12),transparent_55%)]" />
          <div className="absolute inset-x-0 top-1/2 h-px bg-gradient-to-r from-transparent via-[color:var(--line-strong)] to-transparent" />
        </div>

        <svg
          aria-hidden
          viewBox="-300 -300 600 600"
          className="pointer-events-none absolute inset-0 m-auto h-[min(80vh,80vw)] w-[min(80vh,80vw)]"
          fill="none"
        >
          {EDGES.map((edge, i) => (
            <line
              key={i}
              ref={setLineRef(i)}
              x1="0"
              y1="0"
              x2="0"
              y2="0"
              stroke="var(--color-accent)"
              strokeWidth="1.2"
              strokeLinecap="round"
              style={{
                mixBlendMode: "screen",
              }}
              data-edge={`${edge[0]}-${edge[1]}`}
            />
          ))}
        </svg>

        <div className="absolute inset-0 flex items-center justify-center">
          <Hex
            ref={apexRef}
            size={140}
            label="Apex"
            sublabel="synthesis"
            variant="solid"
            className="[&.hex-glow-on_.hex-clip]:!bg-[color:var(--color-accent)] [&.hex-glow-on_.hex-clip]:!text-[color:var(--color-surface)] [&.hex-glow-on_.hex-clip]:shadow-[0_0_80px_20px_rgba(98,144,195,0.45)]"
            ariaHidden
          />
          {Array.from({ length: 6 }).map((_, i) => (
            <Hex
              key={i}
              ref={setOuterRef(i)}
              size={96}
              variant="outline"
              ariaHidden
              label={String(i + 1)}
            />
          ))}
        </div>

        <div
          ref={phase1HeadlineRef}
          className="pointer-events-none absolute inset-x-0 top-[18vh] px-6 text-center md:top-[20vh]"
        >
          <p className="font-mono text-[0.7rem] tracking-[0.28em] uppercase text-soft sm:text-xs">
            When one model isn&rsquo;t enough
          </p>
        </div>

        <div
          ref={headlineRef}
          className="pointer-events-none absolute inset-x-0 top-[14vh] px-6 text-center md:top-[16vh]"
        >
          <p className="font-mono text-[0.7rem] tracking-[0.28em] uppercase text-soft sm:text-xs">
            The horizontal LLM council
          </p>
          <h1 className="mt-4 text-balance text-4xl font-semibold leading-[1.02] tracking-tight text-ink sm:text-6xl md:text-7xl">
            Seven minds.
            <br />
            <span className="bg-gradient-to-r from-[color:var(--color-bg)] via-[color:var(--color-accent)] to-[color:var(--color-bg)] bg-clip-text text-transparent">
              One synthesis.
            </span>
          </h1>
          <p className="mx-auto mt-5 max-w-xl text-balance text-base text-soft sm:text-lg">
            Hexal runs your question through a council of AI models that debate,
            critique, and agree &mdash; so you get the answer instead of a
            best-guess.
          </p>
        </div>

        <div
          ref={ctasRef}
          className="pointer-events-auto absolute inset-x-0 bottom-[10vh] z-10 flex flex-col items-center justify-center gap-3 px-6 sm:flex-row md:bottom-[14vh]"
        >
          <Link
            href="/signup"
            className="inline-flex items-center justify-center rounded-full bg-[color:var(--color-accent)] px-7 py-3.5 text-base font-semibold text-[color:var(--color-surface)] shadow-[0_20px_40px_-16px_rgba(98,144,195,0.7)] transition-transform duration-300 hover:scale-[1.03] active:scale-[0.97]"
            style={{ transitionTimingFunction: "var(--ease-hexal)" }}
          >
            Try the Council
          </Link>
          <Link
            href="#how"
            className="inline-flex items-center justify-center rounded-full border border-strong px-7 py-3.5 text-base font-medium text-ink/85 transition-[background,color,transform] duration-300 hover:bg-[color:var(--color-bg)]/[0.04] hover:text-ink active:scale-[0.97]"
            style={{ transitionTimingFunction: "var(--ease-hexal)" }}
          >
            Watch demo
          </Link>
        </div>

        <div className="pointer-events-none absolute inset-x-0 bottom-6 flex justify-center">
          <span className="font-mono text-[0.6rem] tracking-[0.3em] uppercase text-soft/80">
            Scroll
          </span>
        </div>
      </div>
    </section>
  );
}

export default Hero;
