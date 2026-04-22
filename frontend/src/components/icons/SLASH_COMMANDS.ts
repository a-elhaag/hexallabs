// Slash command definitions for chat interface.
// Each entry maps a command to its icon, label, and description.

export interface SlashCommand {
  command: string;
  label: string;
  description: string;
  icon: "council" | "oracle" | "relay" | "workflow" | "scout";
}

export const SLASH_COMMANDS: SlashCommand[] = [
  {
    command: "/council",
    label: "The Council",
    description: "Run query across all models in parallel",
    icon: "council",
  },
  {
    command: "/oracle",
    label: "Oracle",
    description: "Single model, direct response",
    icon: "oracle",
  },
  {
    command: "/relay",
    label: "The Relay",
    description: "Chain models with mid-generation handoff",
    icon: "relay",
  },
  {
    command: "/workflow",
    label: "Workflow",
    description: "Build a custom node pipeline",
    icon: "workflow",
  },
  {
    command: "/scout",
    label: "Scout",
    description: "Web search injected as context",
    icon: "scout",
  },
];
