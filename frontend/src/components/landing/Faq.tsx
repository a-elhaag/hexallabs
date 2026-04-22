"use client";

import { useLayoutEffect, useMemo, useRef } from "react";
import { ensureGsap, prefersReducedMotion } from "~/lib/gsap";

interface QA {
  q: string;
  a: string;
}

const FAQ: QA[] = [
  {
    q: "What is Hexal?",
    a: "Hexal is a horizontal LLM platform. Instead of sending your question to one model and hoping for the best, it runs a council of models in parallel, has them critique each other anonymously, and synthesizes the result.",
  },
  {
    q: "Why a council instead of a single model?",
    a: "No single model is best at everything. A council surfaces disagreement, shows you where the consensus is, and gives you a synthesis weighted by how confident each model is after it has seen the others' work.",
  },
  {
    q: "Do the models know who they're critiquing?",
    a: "No. Peer review is anonymous. Models see each other's answers with identities stripped so their critique is about the argument, not the brand.",
  },
  {
    q: "Is my data private?",
    a: "Your queries are processed through the council you select. Hexal doesn't train on your conversations or sell data. Full details live on the about page.",
  },
  {
    q: "Does it work on mobile?",
    a: "Yes. Every mode — Council, Oracle, Relay, Workflow — is built mobile-first. The hex grid reflows to fit a phone, and streaming is smooth over cellular.",
  },
  {
    q: "When will Workflow ship?",
    a: "Workflow is coming. Today you can run Council and Oracle; Relay, Scout, Prompt Lens and full Workflow are rolling out through the next few releases.",
  },
];

export function Faq() {
  const sectionRef = useRef<HTMLElement | null>(null);
  const itemRefs = useRef<Array<HTMLDetailsElement | null>>([]);

  const setItemRef = useMemo(
    () => (i: number) => (el: HTMLDetailsElement | null) => {
      itemRefs.current[i] = el;
    },
    [],
  );

  useLayoutEffect(() => {
    const { gsap } = ensureGsap();
    const items = itemRefs.current.filter(
      (el): el is HTMLDetailsElement => el !== null,
    );
    if (items.length === 0) return;
    if (prefersReducedMotion()) return;

    const ctx = gsap.context(() => {
      items.forEach((item) => {
        gsap.fromTo(
          item,
          { opacity: 0, y: 24 },
          {
            opacity: 1,
            y: 0,
            duration: 0.5,
            ease: "power3.out",
            scrollTrigger: {
              trigger: item,
              start: "top 88%",
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
      id="faq"
      className="relative mx-auto max-w-4xl px-5 py-24 sm:px-8 sm:py-36"
    >
      <div className="mb-12 text-center sm:mb-16">
        <p className="font-mono text-xs tracking-[0.28em] uppercase text-[color:var(--color-accent)]">
          FAQ
        </p>
        <h2 className="mt-3 text-balance text-3xl font-semibold tracking-tight sm:text-5xl">
          Questions, answered.
        </h2>
      </div>

      <div className="space-y-3">
        {FAQ.map((item, i) => (
          <details
            key={item.q}
            ref={setItemRef(i)}
            className="group rounded-2xl border border-white/5 bg-[color:var(--color-surface)]/5 px-6 py-5 transition-[background,border-color] duration-300 open:border-[color:var(--color-accent)]/30 open:bg-[color:var(--color-surface)]/10 sm:px-7 sm:py-6"
            style={{ transitionTimingFunction: "var(--ease-hexal)" }}
          >
            <summary className="flex cursor-pointer list-none items-start justify-between gap-6 text-left">
              <span className="text-base font-semibold tracking-tight text-[color:var(--color-surface)] sm:text-lg">
                {item.q}
              </span>
              <span
                aria-hidden
                className="mt-1 inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-[color:var(--color-muted)]/30 text-[color:var(--color-accent)] transition-transform duration-300 group-open:rotate-45"
                style={{ transitionTimingFunction: "var(--ease-hexal)" }}
              >
                <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                  <path
                    d="M5 1V9M1 5H9"
                    stroke="currentColor"
                    strokeWidth="1.6"
                    strokeLinecap="round"
                  />
                </svg>
              </span>
            </summary>
            <p className="mt-4 text-sm leading-relaxed text-[color:var(--color-muted)] sm:text-base">
              {item.a}
            </p>
          </details>
        ))}
      </div>
    </section>
  );
}

export default Faq;
