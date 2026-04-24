"use client";

import { useState, useRef } from "react";
import { gsap } from "gsap";

const faqs = [
  {
    q: "What is The Council?",
    a: "The Council runs 2–7 models in parallel on your query. Each model answers independently, then anonymously reviews its peers. Apex synthesizes a final answer weighted by each model's confidence score.",
  },
  {
    q: "How does peer review work?",
    a: "After each model answers, responses are shuffled and anonymized. Every model then critiques the others — rating clarity, accuracy, and completeness. Confidence scores update based on peer feedback before Apex synthesizes.",
  },
  {
    q: "What is Oracle mode?",
    a: "Oracle routes your query to a single model for a direct, fast response. No peer review, no synthesis overhead. Best when you know which model fits the task or when speed matters more than consensus.",
  },
  {
    q: "What is Primal Protocol?",
    a: "A toggle available on any mode. When active, Apex rewrites the final synthesis in maximally compressed form — dense, signal-heavy, zero filler. Useful when you want the answer without the explanation.",
  },
  {
    q: "How does Scout work?",
    a: "Scout injects live web search results as context before the models respond. Every model answers with access to current data — not just training knowledge. Results are grounded, not hallucinated.",
  },
  {
    q: "What is The Relay?",
    a: "The Relay hands off generation mid-stream. One model starts the response; when a trigger condition is met, another model takes over with full context including the partial output. Seamless from the user's perspective.",
  },
];

export function Faq() {
  const [openIdx, setOpenIdx] = useState<number | null>(null);

  const wrapperRefs = useRef<(HTMLDivElement | null)[]>([]);
  const contentRefs = useRef<(HTMLDivElement | null)[]>([]);
  const tlRefs = useRef<(gsap.core.Timeline | null)[]>([]);

  function openItem(i: number) {
    const wrapper = wrapperRefs.current[i];
    const content = contentRefs.current[i];
    if (!wrapper || !content) return;

    // Kill any in-progress timeline for this item
    tlRefs.current[i]?.kill();

    const tl = gsap.timeline();
    tl.to(wrapper, { height: content.scrollHeight, duration: 0.5, ease: "power3.inOut" }, 0);
    tl.fromTo(
      content,
      { clipPath: "inset(50% 0 50% 0)" },
      { clipPath: "inset(0% 0 0% 0)", duration: 0.5, ease: "power3.inOut" },
      0,
    );
    tlRefs.current[i] = tl;
  }

  function closeItem(i: number) {
    const wrapper = wrapperRefs.current[i];
    const content = contentRefs.current[i];
    if (!wrapper || !content) return;

    tlRefs.current[i]?.kill();

    const tl = gsap.timeline();
    tl.to(wrapper, { height: 0, duration: 0.42, ease: "power3.inOut" }, 0);
    tl.to(content, { clipPath: "inset(50% 0 50% 0)", duration: 0.42, ease: "power3.inOut" }, 0);
    tlRefs.current[i] = tl;
  }

  function handleToggle(i: number) {
    if (openIdx === i) {
      // Close current item
      closeItem(i);
      setOpenIdx(null);
    } else {
      // Close previously open item simultaneously
      if (openIdx !== null) {
        closeItem(openIdx);
      }
      openItem(i);
      setOpenIdx(i);
    }
  }

  return (
    <section className="py-24">
      <div className="max-w-285 mx-auto px-14">

        {/* Heading block */}
        <div className="flex items-center gap-2 mb-4">
          <span className="text-[0.63rem] font-bold uppercase tracking-[0.18em] text-muted">
            FAQ
          </span>
          <div className="w-10 h-px bg-[rgba(168,144,128,0.2)]" />
        </div>
        <h2 className="text-[2.4rem] font-extrabold text-surface tracking-tight leading-[1.08] mb-10">
          Common questions.
        </h2>

        {/* Accordion stack */}
        <div>
          {faqs.map((faq, i) => {
            const isOpen = openIdx === i;
            return (
              <div
                key={i}
                className="mb-3 bg-[#faf7f4] rounded-[20px] border border-[rgba(168,144,128,0.14)]"
              >
                {/* Question row */}
                <button
                  type="button"
                  onClick={() => handleToggle(i)}
                  className="flex w-full items-center justify-between px-7 py-5 cursor-pointer text-left"
                >
                  <span className="text-[0.95rem] font-bold text-black">
                    {faq.q}
                  </span>

                  {/* Plus / × icon */}
                  <div
                    className={isOpen ? "text-accent" : "text-muted"}
                    style={{
                      transform: isOpen ? "rotate(45deg)" : "rotate(0deg)",
                      transition: "transform 0.35s cubic-bezier(0.16,1,0.3,1)",
                      flexShrink: 0,
                    }}
                  >
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                      <rect x="7" y="0" width="2" height="16" rx="1" fill="currentColor" />
                      <rect x="0" y="7" width="16" height="2" rx="1" fill="currentColor" />
                    </svg>
                  </div>
                </button>

                {/* Expand wrapper — height animated by GSAP */}
                <div
                  ref={(el) => { wrapperRefs.current[i] = el; }}
                  style={{ overflow: "hidden", height: 0 }}
                >
                  {/* Inner content — clip-path animated by GSAP */}
                  <div
                    ref={(el) => { contentRefs.current[i] = el; }}
                    className="px-7 pb-6 pt-2 text-[0.82rem] text-[#7a6a62] leading-[1.75]"
                    style={{ clipPath: "inset(50% 0 50% 0)" }}
                  >
                    {faq.a}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
