export type Mode = "council" | "oracle" | "relay" | "workflow" | "scout";
export type Theme = "dark" | "light";
export type ChatState = "empty" | "forge" | "running" | "done";

export type Message =
  | { id: string; role: "user"; text: string }
  | { id: string; role: "assistant"; text: string }
  | { id: string; role: "system"; component: "mode-selector" | "model-selector" | "toggle-row" };

export const MODES: { id: Mode; label: string; icon: string; desc: string }[] = [
  { id: "council",  label: "Council",  icon: "⬡",  desc: "2–7 models, peer review, Apex synthesis" },
  { id: "oracle",   label: "Oracle",   icon: "◎",  desc: "Single model, direct response" },
  { id: "relay",    label: "Relay",    icon: "⇢",  desc: "Mid-generation handoff between models" },
  { id: "workflow", label: "Workflow", icon: "⬡⬡", desc: "Node-based model pipeline" },
  { id: "scout",    label: "Scout",    icon: "⌕",  desc: "Web search injected as context" },
];

export const MODELS = [
  { id: "swift",   label: "Swift" },
  { id: "prism",   label: "Prism" },
  { id: "depth",   label: "Depth" },
  { id: "atlas",   label: "Atlas" },
  { id: "horizon", label: "Horizon" },
  { id: "pulse",   label: "Pulse" },
];

export const SUGGESTIONS = [
  "Explain the transformer architecture",
  "Compare top LLMs for code generation",
  "What is RAG and when should I use it",
  "Best practices for prompt engineering",
];
