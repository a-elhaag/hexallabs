"use client";

import { type Mode } from "~/components/chat/types";

const PHASES = ["Prompt Forge", "Streaming", "Peer review", "Synthesis"] as const;

interface ModelCard {
  id: string;
  label: string;
  conf?: number;
  text: string;
  done: boolean;
}

const DEMO_CARDS: ModelCard[] = [
  { id: "swift",   label: "Swift",   conf: 8.2, text: "The transformer architecture replaces recurrence with self-attention. Each token attends to all others simultaneously…",                               done: true  },
  { id: "prism",   label: "Prism",   conf: 7.6, text: "Breaking this into three parts: (1) self-attention computes Q·Kᵀ/√d scores, (2) positional encoding adds order info…",                           done: true  },
  { id: "depth",   label: "Depth",   conf: 9.1, text: 'Transformers were introduced in "Attention is All You Need" (Vaswani et al., 2017). The key innovation was parallel self-attention over sequential…', done: true  },
  { id: "atlas",   label: "Atlas",   conf: 7.0, text: "Encoder-only (BERT) use bidirectional attention. Decoder-only (GPT) use causal masking.",                                                          done: false },
  { id: "horizon", label: "Horizon", conf: 8.8, text: "For long-context applications, transformers face O(n²) attention complexity. Variants like Longformer and Flash Attention address",               done: false },
];

interface Props {
  activePhase: number;
  mode: Mode;
}

export function ModelGrid({ activePhase, mode: _ }: Props) {
  return (
    <div className="flex-1 overflow-y-auto px-4 py-6">
      <div className="max-w-3xl mx-auto flex flex-col gap-5">

        {/* Phase bar */}
        <div
          className="flex items-center gap-2 self-center px-4 py-2 rounded-full text-[0.72rem]"
          style={{ background: "var(--color-card)", border: "1px solid var(--color-border)" }}
        >
          {PHASES.map((phase, i) => (
            <div key={phase} className="flex items-center gap-2">
              {i > 0 && <span style={{ color: "var(--color-border)" }}>·</span>}
              <div
                className="w-2 h-2 rounded-full flex-shrink-0 transition-all duration-500"
                style={{
                  background:  i < activePhase  ? "rgba(98,144,195,0.5)"
                             : i === activePhase ? "var(--color-mode)"
                             : "var(--color-border)",
                  boxShadow:   i === activePhase ? "0 0 8px var(--color-mode)" : "none",
                }}
              />
              <span
                style={{
                  color:      i === activePhase ? "var(--color-surface)" : "var(--color-muted)",
                  fontWeight: i === activePhase ? 600 : 400,
                }}
              >
                {phase}
              </span>
            </div>
          ))}
        </div>

        {/* Model cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {DEMO_CARDS.map((card) => (
            <div
              key={card.id}
              className="relative rounded-[16px] p-4 flex flex-col gap-2 min-h-[130px] border transition-all duration-500"
              style={{
                background:   "var(--color-card)",
                borderColor:  card.done ? "rgba(98,144,195,0.3)" : "var(--color-border)",
              }}
            >
              <div className="flex items-center justify-between">
                <span
                  className="text-[0.62rem] font-bold uppercase tracking-[0.1em]"
                  style={{ color: "var(--color-muted)" }}
                >
                  {card.label}
                </span>
                {card.conf !== undefined && card.done && (
                  <span
                    className="text-[0.62rem] font-bold px-2 py-0.5 rounded-full"
                    style={{
                      color:      "var(--color-mode)",
                      background: "rgba(98,144,195,0.1)",
                    }}
                  >
                    {card.conf}
                  </span>
                )}
              </div>

              <p
                className="text-[0.76rem] leading-[1.6] flex-1"
                style={{ color: "rgba(245,241,237,0.65)" }}
              >
                {card.text}
                {!card.done && <BlinkCursor />}
              </p>

              {card.done && (
                <p
                  className="text-[0.62rem] pt-2 border-t"
                  style={{ color: "var(--color-muted)", borderColor: "var(--color-border)" }}
                >
                  Response complete · awaiting peer review
                </p>
              )}
            </div>
          ))}
        </div>

        {/* Apex */}
        <div
          className="rounded-[16px] p-5 border col-span-full"
          style={{
            background:  "rgba(98,144,195,0.05)",
            borderColor: activePhase >= 3 ? "var(--color-mode)" : "rgba(98,144,195,0.2)",
          }}
        >
          <div
            className="text-[0.6rem] font-bold uppercase tracking-[0.12em] mb-3"
            style={{ color: "var(--color-mode)" }}
          >
            ◉ Apex · Synthesis
          </div>
          {activePhase >= 3 ? (
            <p className="text-[0.85rem] leading-[1.75]" style={{ color: "var(--color-surface)" }}>
              The transformer architecture, introduced in <em>"Attention is All You Need"</em> (Vaswani et al., 2017), replaces recurrence with self-attention — all tokens interact in parallel rather than sequentially.
              <br /><br />
              Three key mechanisms: (1) self-attention computes Q·Kᵀ/√d similarity scores, (2) positional encoding preserves order, (3) feed-forward sublayers add non-linear transformation per token.
            </p>
          ) : (
            <p className="text-[0.82rem] italic" style={{ color: "rgba(168,144,128,0.4)" }}>
              Waiting for all models and peer review to complete…
            </p>
          )}
        </div>

        {/* Confidence row (when synthesis done) */}
        {activePhase >= 3 && (
          <div className="flex flex-wrap gap-2 justify-center">
            {DEMO_CARDS.map((c) => (
              <span
                key={c.id}
                className="text-[0.67rem] font-semibold px-3 py-1 rounded-full"
                style={{
                  background: "var(--color-card)",
                  color:      "var(--color-muted)",
                  border:     "1px solid var(--color-border)",
                }}
              >
                {c.label} · {c.conf}
              </span>
            ))}
          </div>
        )}

      </div>
    </div>
  );
}

function BlinkCursor() {
  return (
    <span
      className="inline-block w-0.5 h-3 ml-0.5 align-middle"
      style={{
        background: "var(--color-mode)",
        animation:  "blink 1s step-end infinite",
      }}
    />
  );
}
