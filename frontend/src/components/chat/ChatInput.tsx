"use client";

import { useRef, type KeyboardEvent } from "react";
import { type Mode, type ChatState, MODELS } from "~/components/chat/types";

interface Props {
  mode: Mode;
  chatState: ChatState;
  selectedModels: string[];
  scoutOn: boolean;
  onSubmit: (text: string) => void;
  onStop: () => void;
  inputValue: string;
  onInputChange: (v: string) => void;
}

export function ChatInput({
  mode,
  chatState,
  selectedModels,
  scoutOn,
  onSubmit,
  onStop,
  inputValue,
  onInputChange,
}: Props) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const running = chatState === "running";

  function handleInput() {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = `${Math.min(ta.scrollHeight, 120)}px`;
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  function submit() {
    const val = inputValue.trim();
    if (!val || running) return;
    onSubmit(val);
    onInputChange("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }

  const modelLabels =
    mode === "council"
      ? selectedModels
          .map((id) => MODELS.find((m) => m.id === id)?.label)
          .filter(Boolean)
          .join(", ")
      : null;

  return (
    <div
      className="px-4 pb-4 pt-2 border-t"
      style={{ borderColor: "var(--color-border)", background: "var(--color-panel)" }}
    >
      {/* Input box */}
      <div
        className="flex items-end gap-2 rounded-[16px] px-4 py-3 transition-all duration-200"
        style={{
          background:  "var(--color-card)",
          border:      "1.5px solid var(--color-border)",
        }}
        onFocus={(e) => {
          (e.currentTarget as HTMLDivElement).style.borderColor = "var(--color-mode)";
        }}
        onBlur={(e) => {
          (e.currentTarget as HTMLDivElement).style.borderColor = "var(--color-border)";
        }}
      >
        <textarea
          ref={textareaRef}
          rows={1}
          value={inputValue}
          onChange={(e) => onInputChange(e.target.value)}
          onInput={handleInput}
          onKeyDown={handleKeyDown}
          placeholder={running ? "Follow-up or stop…" : "Ask anything…"}
          className="flex-1 resize-none bg-transparent border-none outline-none text-[0.85rem] leading-[1.55] font-sans"
          style={{
            color:       "var(--color-surface)",
            maxHeight:   "120px",
            overflowY:   "auto",
          }}
        />
        {running ? (
          <button
            type="button"
            onClick={onStop}
            className="w-9 h-9 rounded-[10px] flex items-center justify-center flex-shrink-0 transition-opacity hover:opacity-80 cursor-pointer"
            style={{ background: "#c05454" }}
          >
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
              <rect x="2" y="2" width="8" height="8" rx="1" fill="#fff" />
            </svg>
          </button>
        ) : (
          <button
            type="button"
            onClick={submit}
            disabled={!inputValue.trim()}
            className="w-9 h-9 rounded-[10px] flex items-center justify-center flex-shrink-0 transition-opacity hover:opacity-80 disabled:opacity-30 cursor-pointer"
            style={{ background: "var(--color-mode)" }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
              <path d="M2 21l21-9L2 3v7l15 2-15 2z" fill="#fff" />
            </svg>
          </button>
        )}
      </div>

      {/* Tags row */}
      <div className="flex items-center gap-2 mt-2 flex-wrap">
        <span
          className="text-[0.65rem] font-bold uppercase tracking-[0.1em] px-3 py-1 rounded-full"
          style={{
            background:  "rgba(98,144,195,0.1)",
            color:       "var(--color-mode)",
            border:      "1px solid rgba(98,144,195,0.25)",
          }}
        >
          {mode.charAt(0).toUpperCase() + mode.slice(1)}
        </span>

        {scoutOn && (
          <span
            className="text-[0.65rem] font-semibold px-3 py-1 rounded-full"
            style={{
              background:  "var(--color-card)",
              color:       "var(--color-muted)",
              border:      "1px solid var(--color-border)",
            }}
          >
            Scout on
          </span>
        )}

        {modelLabels && (
          <span
            className="text-[0.65rem] font-semibold px-3 py-1 rounded-full ml-auto"
            style={{
              background:  "var(--color-card)",
              color:       "var(--color-muted)",
              border:      "1px solid var(--color-border)",
            }}
          >
            {modelLabels}
          </span>
        )}
      </div>
    </div>
  );
}
