"use client";

const SESSIONS = {
  Today: [
    "Transformer architecture deep dive",
    "Quantum computing ELI5",
    "Compare React vs Vue 2024",
  ],
  Yesterday: [
    "Best LLM for code tasks",
    "Explain RLHF step by step",
  ],
  "This week": [
    "Startup pitch deck structure",
    "RAG vs fine-tuning tradeoffs",
    "Docker networking guide",
  ],
};

interface Props {
  open: boolean;
  activeSession?: string;
  onNewQuery: () => void;
}

export function Sidebar({ open, activeSession, onNewQuery }: Props) {
  return (
    <div
      className="flex flex-col transition-[width] duration-300 shrink-0"
      style={{
        width:            open ? "220px" : "0",
        overflow:         "hidden",
        background:       "var(--color-panel)",
        borderRight:      open ? "1px solid var(--color-border)" : "none",
        transitionTimingFunction: "cubic-bezier(0.16, 1, 0.3, 1)",
      }}
    >
      <div
        className="flex flex-col flex-1 overflow-y-auto py-3"
        style={{ opacity: open ? 1 : 0, transition: "opacity 0.2s", pointerEvents: open ? "auto" : "none", minWidth: "220px" }}
      >
        {/* New query button */}
        <button
          type="button"
          onClick={onNewQuery}
          className="mx-3 mb-3 px-4 py-2 rounded-[12px] text-[0.78rem] font-bold text-center cursor-pointer transition-opacity hover:opacity-80"
          style={{ background: "var(--color-mode)", color: "#fff" }}
        >
          + New query
        </button>

        {/* Session groups */}
        {Object.entries(SESSIONS).map(([group, items]) => (
          <div key={group}>
            <div
              className="px-4 pt-3 pb-1 text-[0.58rem] font-bold uppercase tracking-[0.12em]"
              style={{ color: "rgba(168,144,128,0.45)" }}
            >
              {group}
            </div>
            {items.map((item) => {
              const isActive = item === activeSession;
              return (
                <button
                  key={item}
                  type="button"
                  className="w-full text-left px-4 py-1.5 mx-0 text-[0.75rem] truncate rounded-[8px] cursor-pointer transition-all duration-150 block"
                  style={{
                    color:      isActive ? "var(--color-surface)" : "rgba(245,241,237,0.45)",
                    background: isActive ? "rgba(98,144,195,0.1)" : "transparent",
                    borderLeft: isActive ? "2px solid var(--color-mode)" : "2px solid transparent",
                  }}
                >
                  {item}
                </button>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}
