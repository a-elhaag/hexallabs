"use client";

import { useEffect, useRef } from "react";
import { type Message, type Mode, SUGGESTIONS } from "~/components/chat/types";
import { MessageBubble } from "~/components/chat/MessageBubble";
import { ModeSelector } from "~/components/chat/inline/ModeSelector";

interface Props {
  messages: Message[];
  activeMode: Mode;
  selectedModels: string[];
  scoutOn: boolean;
  primalOn: boolean;
  onModeChange: (m: Mode) => void;
  onModelsChange: (ids: string[]) => void;
  onScoutChange: (v: boolean) => void;
  onPrimalChange: (v: boolean) => void;
  onSuggestion: (text: string) => void;
}

export function MessageList({
  messages,
  activeMode,
  selectedModels,
  scoutOn,
  primalOn,
  onModeChange,
  onModelsChange,
  onScoutChange,
  onPrimalChange,
  onSuggestion,
}: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-8 px-6 py-12">
        <div className="text-center">
          <div
            className="text-[2rem] font-extrabold tracking-[-0.03em] mb-1"
            style={{ color: "var(--color-surface)" }}
          >
            hexallabs
          </div>
          <div className="text-[0.85rem]" style={{ color: "var(--color-muted)" }}>
            What do you want to know?
          </div>
        </div>

        <div className="w-full max-w-2xl">
          <div
            className="text-[0.62rem] font-bold uppercase tracking-[0.12em] mb-3"
            style={{ color: "var(--color-muted)" }}
          >
            Choose a mode
          </div>
          <ModeSelector activeMode={activeMode} onSelect={onModeChange} />
        </div>

        <div className="w-full max-w-2xl">
          <div
            className="text-[0.62rem] font-bold uppercase tracking-[0.12em] mb-3"
            style={{ color: "var(--color-muted)" }}
          >
            Try asking
          </div>
          <div className="flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => onSuggestion(s)}
                className="px-4 py-2 rounded-full text-[0.74rem] border transition-all duration-200 cursor-pointer hover:border-[var(--color-mode)]"
                style={{
                  background:  "var(--color-card)",
                  borderColor: "var(--color-border)",
                  color:       "var(--color-muted)",
                }}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6">
      <div className="max-w-3xl mx-auto flex flex-col gap-4">
        {messages.map((msg) => (
          <MessageBubble
            key={msg.id}
            message={msg}
            activeMode={activeMode}
            selectedModels={selectedModels}
            scoutOn={scoutOn}
            primalOn={primalOn}
            onModeChange={onModeChange}
            onModelsChange={onModelsChange}
            onScoutChange={onScoutChange}
            onPrimalChange={onPrimalChange}
          />
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
