"use client";

import { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

const steps = [
  { num: "01", title: "Submit",       text: "Prompt Forge sharpens your query before it reaches the models.",   above: true  },
  { num: "02", title: "Parallel run", text: "All models stream simultaneously. Each scores its own confidence.", above: false },
  { num: "03", title: "Peer review",  text: "Models critique anonymous peers and adjust confidence scores.",     above: true  },
  { num: "04", title: "Synthesis",    text: "Apex weighs final scores and writes one definitive answer.",        above: false },
];

const STEP_COUNT = steps.length;
const VH_PER_STEP = 85;

// Center of each step slot as % of bar width
function slotCenter(i: number) {
  return (i / STEP_COUNT + 1 / (STEP_COUNT * 2)) * 100;
}

export function HowItWorks() {
  const outerRef   = useRef<HTMLDivElement>(null);
  const barRef     = useRef<HTMLDivElement>(null);
  const pillRef    = useRef<HTMLDivElement>(null);
  const titleRefs  = useRef<HTMLDivElement[]>([]);
  const textRefs   = useRef<HTMLDivElement[]>([]);
  const dashRefs   = useRef<HTMLDivElement[]>([]);
  const prevStep    = useRef(-1);
  const stepStates  = useRef<boolean[]>(steps.map(() => false));

  function movePill(i: number) {
    if (!pillRef.current || !barRef.current) return;
    const barW    = barRef.current.offsetWidth;
    const pillW   = pillRef.current.offsetWidth;
    const centerX = (slotCenter(i) / 100) * barW - pillW / 2;
    gsap.to(pillRef.current, {
      x: centerX,
      duration: 0.65,
      ease: "power3.inOut",
    });
    // Update pill label
    const label = pillRef.current.querySelector("span");
    if (label) label.textContent = steps[i]!.num;
  }

  function activateStep(i: number) {
    if (stepStates.current[i]) return;
    stepStates.current[i] = true;
    const title = titleRefs.current[i];
    const text  = textRefs.current[i];
    const dash  = dashRefs.current[i];
    if (!title || !text || !dash) return;
    gsap.to(dash,  { borderColor: "var(--color-accent)", opacity: 1, duration: 0.35 });
    gsap.to(title, { color: "var(--color-surface)", opacity: 1, y: 0, duration: 0.4, ease: "power2.out" });
    gsap.to(text,  { color: "var(--color-surface)", opacity: 0.65, y: 0, duration: 0.45, ease: "power2.out" });
  }

  function deactivateStep(i: number) {
    if (!stepStates.current[i]) return;
    stepStates.current[i] = false;
    const title = titleRefs.current[i];
    const text  = textRefs.current[i];
    const dash  = dashRefs.current[i];
    if (!title || !text || !dash) return;
    gsap.to(dash,  { borderColor: "rgba(168,144,128,0.25)", opacity: 0.5, duration: 0.3 });
    gsap.to(title, { color: "var(--color-muted)", opacity: 0.35, y: steps[i]!.above ? 10 : -10, duration: 0.3 });
    gsap.to(text,  { color: "var(--color-muted)", opacity: 0.2, y: steps[i]!.above ? 10 : -10, duration: 0.3 });
  }

  useEffect(() => {
    // Set initial dim state
    steps.forEach((step, i) => {
      const title = titleRefs.current[i]; const text = textRefs.current[i]; const dash = dashRefs.current[i];
      if (!title || !text || !dash) return;
      gsap.set(dash,  { borderColor: "rgba(168,144,128,0.25)", opacity: 0.5 });
      gsap.set(title, { color: "var(--color-muted)", opacity: 0.35, y: step.above ? 10 : -10 });
      gsap.set(text,  { color: "var(--color-muted)", opacity: 0.2,  y: step.above ? 10 : -10 });
    });

    // Position pill at step 0 immediately (no animation on mount)
    if (pillRef.current && barRef.current) {
      const barW  = barRef.current.offsetWidth;
      const pillW = pillRef.current.offsetWidth;
      gsap.set(pillRef.current, { x: (slotCenter(0) / 100) * barW - pillW / 2 });
    }

    const st = ScrollTrigger.create({
      trigger: outerRef.current,
      start:   "top top",
      end:     "bottom bottom",
      onUpdate(self) {
        const activeStep = Math.min(STEP_COUNT - 1, Math.floor(self.progress * STEP_COUNT * 1.02));
        if (activeStep === prevStep.current) return;
        prevStep.current = activeStep;
        movePill(activeStep);
        steps.forEach((_, i) => {
          if (i <= activeStep) activateStep(i);
          else deactivateStep(i);
        });
      },
    });

    return () => { st.kill(); stepStates.current = steps.map(() => false); prevStep.current = -1; };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div ref={outerRef} style={{ height: `${STEP_COUNT * VH_PER_STEP}vh` }} className="relative">
      <div className="sticky top-0 h-screen flex flex-col items-center justify-center px-14">

        {/* Heading */}
        <div className="self-start w-full max-w-285 mx-auto mb-20">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-[0.63rem] font-bold uppercase tracking-[0.18em] text-muted">How it works</span>
            <div className="w-10 h-px bg-[rgba(168,144,128,0.2)]" />
          </div>
          <h2 className="text-[2.4rem] font-extrabold text-surface tracking-tight leading-[1.08] mb-3">
            From query to answer.
          </h2>
          <p className="text-[0.88rem] text-muted font-medium">
            Four stages. Every model accountable. One definitive synthesis.
          </p>
        </div>

        {/* Timeline */}
        <div className="w-full max-w-285 mx-auto">

          {/* Above-bar row */}
          <div className="grid" style={{ gridTemplateColumns: `repeat(${STEP_COUNT}, 1fr)` }}>
            {steps.map((step, i) => (
              <div key={`above-${i}`} className="flex flex-col items-center px-4">
                {step.above ? (
                  <>
                    <div ref={el => { if (el) titleRefs.current[i] = el; }} className="text-[1rem] font-extrabold mb-2 leading-snug text-center">{step.title}</div>
                    <div ref={el => { if (el) textRefs.current[i] = el; }} className="text-[0.75rem] font-medium leading-[1.7] max-w-40 text-center">{step.text}</div>
                    <div ref={el => { if (el) dashRefs.current[i] = el; }} className="mt-5" style={{ width: 0, height: "52px", borderLeft: "1.5px dashed rgba(168,144,128,0.25)" }} />
                  </>
                ) : (
                  <div style={{ height: "calc(52px + 1rem + 2rem + 2.4rem)" }} />
                )}
              </div>
            ))}
          </div>

          {/* Bar */}
          <div
            ref={barRef}
            className="relative mx-2"
            style={{
              height: "52px",
              background: "#f5f1ed",
              border: "1.5px solid rgba(168,144,128,0.22)",
              borderRadius: "50px",
              overflow: "hidden",
            }}
          >
            {/* Static dim step labels */}
            <div className="absolute inset-0 flex">
              {steps.map((step, i) => (
                <div key={i} className="flex-1 flex items-center justify-center">
                  <span className="text-[0.72rem] font-bold tracking-wide" style={{ color: "var(--color-accent)", opacity: 0.45 }}>{step.num}</span>
                </div>
              ))}
            </div>

            {/* Sliding active pill */}
            <div
              ref={pillRef}
              className="absolute top-1/2 -translate-y-1/2 flex items-center justify-center"
              style={{
                background: "var(--color-accent)",
                borderRadius: "50px",
                padding: "0.35rem 1.2rem",
                boxShadow: "0 4px 20px rgba(98,144,195,0.4)",
                minWidth: "64px",
              }}
            >
              <span className="text-[0.78rem] font-bold text-white tracking-wide">{steps[0]!.num}</span>
            </div>
          </div>

          {/* Below-bar row */}
          <div className="grid" style={{ gridTemplateColumns: `repeat(${STEP_COUNT}, 1fr)` }}>
            {steps.map((step, i) => (
              <div key={`below-${i}`} className="flex flex-col items-center px-4">
                {!step.above ? (
                  <>
                    <div ref={el => { if (el) dashRefs.current[i] = el; }} className="mb-5" style={{ width: 0, height: "52px", borderLeft: "1.5px dashed rgba(168,144,128,0.25)" }} />
                    <div ref={el => { if (el) titleRefs.current[i] = el; }} className="text-[1rem] font-extrabold mb-2 leading-snug text-center">{step.title}</div>
                    <div ref={el => { if (el) textRefs.current[i] = el; }} className="text-[0.75rem] font-medium leading-[1.7] max-w-40 text-center">{step.text}</div>
                  </>
                ) : (
                  <div style={{ height: "calc(52px + 1rem + 2rem + 2.4rem)" }} />
                )}
              </div>
            ))}
          </div>

        </div>
      </div>
    </div>
  );
}
