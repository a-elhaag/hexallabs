"use client";

import { useEffect, useRef, useState } from "react";
import { type Mode, type Theme, type ChatState, type Message, MODELS } from "~/components/chat/types";
import { ChatNav } from "~/components/chat/ChatNav";
import { Sidebar } from "~/components/chat/Sidebar";
import { MessageList } from "~/components/chat/MessageList";
import { ModelGrid } from "~/components/chat/ModelGrid";
import { PromptForge } from "~/components/chat/PromptForge";
import { ChatInput } from "~/components/chat/ChatInput";

function uid() {
  return Math.random().toString(36).slice(2);
}

const IMPROVED_PROMPT =
  "Explain the transformer architecture — focus on the self-attention mechanism, positional encoding, and how it differs from RNN-based sequence models. Include a comparison of encoder-only, decoder-only, and encoder-decoder variants.";

export function ChatShell() {
  const [theme, setTheme]                 = useState<Theme>("dark");
  const [sidebarOpen, setSidebarOpen]     = useState(true);
  const [activeMode, setActiveMode]       = useState<Mode>("council");
  const [chatState, setChatState]         = useState<ChatState>("empty");
  const [messages, setMessages]           = useState<Message[]>([]);
  const [selectedModels, setSelectedModels] = useState<string[]>(
    MODELS.slice(0, 5).map((m) => m.id),
  );
  const [scoutOn, setScoutOn]             = useState(false);
  const [primalOn, setPrimalOn]           = useState(false);
  const [inputValue, setInputValue]       = useState("");
  const [forgeOriginal, setForgeOriginal] = useState("");
  const [activePhase, setActivePhase]     = useState(0);

  const phaseTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Restore preferences from localStorage
  useEffect(() => {
    if (typeof window === "undefined") return;
    const savedTheme = localStorage.getItem("hexallabs-theme") as Theme | null;
    if (savedTheme) setTheme(savedTheme);

    const savedSidebar = localStorage.getItem("hexallabs-sidebar");
    if (savedSidebar !== null) setSidebarOpen(savedSidebar === "true");
    else setSidebarOpen(window.innerWidth >= 1024);
  }, []);

  // Persist theme
  useEffect(() => {
    localStorage.setItem("hexallabs-theme", theme);
  }, [theme]);

  // Persist sidebar state
  useEffect(() => {
    localStorage.setItem("hexallabs-sidebar", String(sidebarOpen));
  }, [sidebarOpen]);

  function handleThemeToggle() {
    setTheme((t) => (t === "dark" ? "light" : "dark"));
  }

  function handleSidebarToggle() {
    setSidebarOpen((o) => !o);
  }

  function handleSubmit(text: string) {
    setForgeOriginal(text);
    setChatState("forge");
  }

  function handleSuggestion(text: string) {
    setInputValue(text);
  }

  function startRunning(promptText: string) {
    const userMsg: Message = { id: uid(), role: "user", text: promptText };
    setMessages((prev) => [...prev, userMsg]);
    setChatState("running");
    setActivePhase(0);

    // Simulate phase progression
    phaseTimerRef.current = setTimeout(() => setActivePhase(1), 600);
    phaseTimerRef.current = setTimeout(() => setActivePhase(2), 3500);
    phaseTimerRef.current = setTimeout(() => setActivePhase(3), 5500);
    phaseTimerRef.current = setTimeout(() => {
      setChatState("done");
      const assistantMsg: Message = {
        id: uid(),
        role: "assistant",
        text: `The transformer architecture, introduced in <em>"Attention is All You Need"</em> (Vaswani et al., 2017), fundamentally replaced recurrence with self-attention — all tokens interact in parallel.<br><br><strong>Three key mechanisms:</strong><br>1. Self-attention — Q·Kᵀ/√d scores, weighted-sum values<br>2. Positional encoding — sinusoidal vectors preserve order<br>3. Feed-forward sublayers — per-token non-linear transformation`,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    }, 7000);
  }

  function handleUseOriginal() {
    const text = forgeOriginal;
    setChatState("running");
    startRunning(text);
  }

  function handleUseImproved() {
    setChatState("running");
    startRunning(IMPROVED_PROMPT);
  }

  function handleStop() {
    if (phaseTimerRef.current) clearTimeout(phaseTimerRef.current);
    setChatState("done");
  }

  function handleNewQuery() {
    if (phaseTimerRef.current) clearTimeout(phaseTimerRef.current);
    setMessages([]);
    setChatState("empty");
    setActivePhase(0);
    setInputValue("");
  }

  // Mobile: close sidebar on small screens when clicking outside
  // (handled via lg: breakpoint visibility pattern)

  return (
    <div
      data-theme={theme}
      data-mode={activeMode}
      className="flex flex-col h-screen overflow-hidden"
      style={{ background: "var(--color-bg)", color: "var(--color-surface)" }}
    >
      {/* Nav */}
      <ChatNav
        mode={activeMode}
        theme={theme}
        scoutOn={scoutOn}
        primalOn={primalOn}
        sidebarOpen={sidebarOpen}
        onModeChange={setActiveMode}
        onThemeToggle={handleThemeToggle}
        onScoutToggle={() => setScoutOn((v) => !v)}
        onPrimalToggle={() => setPrimalOn((v) => !v)}
        onSidebarToggle={handleSidebarToggle}
      />

      {/* Body: sidebar + main */}
      <div className="flex flex-1 overflow-hidden">

        {/* Sidebar */}
        <Sidebar
          open={sidebarOpen}
          activeSession={messages.length > 0 ? "Quantum computing ELI5" : undefined}
          onNewQuery={handleNewQuery}
        />

        {/* Mobile sidebar backdrop */}
        {sidebarOpen && (
          <div
            className="lg:hidden fixed inset-0 z-40 bg-black/50"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Main */}
        <div className="flex flex-col flex-1 overflow-hidden">
          {chatState === "running" ? (
            <ModelGrid activePhase={activePhase} mode={activeMode} />
          ) : (
            <MessageList
              messages={messages}
              activeMode={activeMode}
              selectedModels={selectedModels}
              scoutOn={scoutOn}
              primalOn={primalOn}
              onModeChange={setActiveMode}
              onModelsChange={setSelectedModels}
              onScoutChange={setScoutOn}
              onPrimalChange={setPrimalOn}
              onSuggestion={handleSuggestion}
            />
          )}

          <ChatInput
            mode={activeMode}
            chatState={chatState}
            selectedModels={selectedModels}
            scoutOn={scoutOn}
            onSubmit={handleSubmit}
            onStop={handleStop}
            inputValue={inputValue}
            onInputChange={setInputValue}
          />
        </div>
      </div>

      {/* Prompt Forge overlay */}
      {chatState === "forge" && (
        <PromptForge
          original={forgeOriginal}
          improved={IMPROVED_PROMPT}
          onUseOriginal={handleUseOriginal}
          onUseImproved={handleUseImproved}
        />
      )}

      {/* Global blink animation */}
      <style>{`
        @keyframes blink {
          0%, 100% { opacity: 1; }
          50%       { opacity: 0; }
        }
      `}</style>
    </div>
  );
}
