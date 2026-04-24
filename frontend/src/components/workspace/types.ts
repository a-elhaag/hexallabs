import type {
  WorkspaceKind,
  ArtifactPayload,
  CodeArtifact,
  SpreadsheetArtifact,
  DiagramArtifact,
  DocumentArtifact,
} from "~/lib/api/types";

export type { WorkspaceKind, ArtifactPayload, CodeArtifact, SpreadsheetArtifact, DiagramArtifact, DocumentArtifact };

export const WORKSPACE_KINDS: WorkspaceKind[] = [
  "chat",
  "code",
  "document",
  "spreadsheet",
  "diagram",
];

export const WORKSPACE_LABEL: Record<WorkspaceKind, string> = {
  chat:        "Chat",
  code:        "Code",
  document:    "Document",
  spreadsheet: "Sheet",
  diagram:     "Diagram",
};

export const WORKSPACE_ICON: Record<WorkspaceKind, string> = {
  chat:        "◎",
  code:        "⟨⟩",
  document:    "¶",
  spreadsheet: "▦",
  diagram:     "◇",
};
