"use client";

import { type Message, type Mode } from "~/components/chat/types";
import { ModeSelector } from "~/components/chat/inline/ModeSelector";
import { ModelSelector } from "~/components/chat/inline/ModelSelector";
import { ToggleRow } from "~/components/chat/inline/ToggleRow";

interface Props {
  message: Message;
  activeMode: Mode;
  selectedModels: string[];
  scoutOn: boolean;
  primalOn: boolean;
  onModeChange: (m: Mode) => void;
  onModelsChange: (ids: string[]) => void;
  onScoutChange: (v: boolean) => void;
  onPrimalChange: (v: boolean) => void;
}

export function MessageBubble({
  message,
  activeMode,
  selectedModels,
  scoutOn,
  primalOn,
  onModeChange,
  onModelsChange,
  onScoutChange,
  onPrimalChange,
}: Props) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div
          className="max-w-[70%] px-5 py-3 rounded-[18px] text-[0.85rem] leading-[1.65]"
          style={{
            background: "var(--color-card)",
            color:      "var(--color-surface)",
            border:     "1px solid var(--color-border)",
          }}
        >
          {message.text}
        </div>
      </div>
    );
  }

  if (message.role === "assistant") {
    return (
      <div
        className="rounded-[18px] px-6 py-5 text-[0.85rem] leading-[1.75]"
        style={{
          background:  "var(--color-card)",
          borderLeft:  "2.5px solid var(--color-mode)",
          color:       "var(--color-surface)",
          border:      "1px solid var(--color-border)",
          borderLeftColor: "var(--color-mode)",
        }}
      >
        <div
          className="text-[0.6rem] font-bold uppercase tracking-[0.12em] mb-3"
          style={{ color: "var(--color-mode)" }}
        >
          ◉ Apex · Synthesis
        </div>
        <div dangerouslySetInnerHTML={{ __html: message.text }} />
      </div>
    );
  }

  // system — inline component
  return (
    <div className="py-1">
      {message.component === "mode-selector" && (
        <ModeSelector activeMode={activeMode} onSelect={onModeChange} />
      )}
      {message.component === "model-selector" && (
        <ModelSelector selected={selectedModels} onChange={onModelsChange} />
      )}
      {message.component === "toggle-row" && (
        <ToggleRow
          scoutOn={scoutOn}
          primalOn={primalOn}
          onScoutChange={onScoutChange}
          onPrimalChange={onPrimalChange}
        />
      )}
    </div>
  );
}
