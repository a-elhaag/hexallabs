"use client";

import type { ReactNode } from "react";
import type {
  ArtifactPayload,
  CodeArtifact,
  DiagramArtifact,
  DocumentArtifact,
  SpreadsheetArtifact,
  WorkspaceKind,
} from "~/lib/api/types";
import { CodeWorkspace } from "./CodeWorkspace";
import { DocumentWorkspace } from "./DocumentWorkspace";
import { SpreadsheetWorkspace } from "./SpreadsheetWorkspace";
import { DiagramWorkspace } from "./DiagramWorkspace";
import { WORKSPACE_LABEL } from "./types";

interface Props {
  kind: WorkspaceKind;
  streamingText: string;
  artifact: ArtifactPayload | null;
  isStreaming: boolean;
  classifierReason?: string;
  chatFallback: ReactNode;
}

export function WorkspaceHost({
  kind,
  streamingText,
  artifact,
  isStreaming,
  classifierReason,
  chatFallback,
}: Props) {
  if (kind === "chat") return <>{chatFallback}</>;

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      <WorkspaceHeader kind={kind} reason={classifierReason} />
      {kind === "code" && (
        <CodeWorkspace
          streamingText={streamingText}
          artifact={(artifact as CodeArtifact | null) ?? null}
          isStreaming={isStreaming}
        />
      )}
      {kind === "document" && (
        <DocumentWorkspace
          streamingText={streamingText}
          artifact={(artifact as DocumentArtifact | null) ?? null}
          isStreaming={isStreaming}
        />
      )}
      {kind === "spreadsheet" && (
        <SpreadsheetWorkspace
          artifact={(artifact as SpreadsheetArtifact | null) ?? null}
          isStreaming={isStreaming}
        />
      )}
      {kind === "diagram" && (
        <DiagramWorkspace
          artifact={(artifact as DiagramArtifact | null) ?? null}
          isStreaming={isStreaming}
        />
      )}
    </div>
  );
}

function WorkspaceHeader({ kind, reason }: { kind: WorkspaceKind; reason?: string }) {
  return (
    <div
      className="flex items-center gap-3 h-9 px-4 border-b flex-shrink-0"
      style={{
        background: "var(--color-panel)",
        borderColor: "var(--color-border)",
      }}
    >
      <span
        className="text-[0.6rem] font-bold uppercase tracking-[0.12em]"
        style={{ color: "var(--color-mode)" }}
      >
        {WORKSPACE_LABEL[kind]} workspace
      </span>
      {reason && (
        <span
          className="text-[0.65rem] truncate"
          style={{ color: "var(--color-muted)" }}
          title={reason}
        >
          — {reason}
        </span>
      )}
    </div>
  );
}
