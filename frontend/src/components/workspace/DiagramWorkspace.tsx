"use client";

import dynamic from "next/dynamic";
import type { DiagramArtifact } from "~/lib/api/types";

const MermaidRenderer = dynamic(() => import("./MermaidRenderer"), {
  ssr: false,
  loading: () => (
    <div className="text-[0.72rem]" style={{ color: "var(--color-muted)" }}>
      Loading diagram engine…
    </div>
  ),
});

interface Props {
  artifact: DiagramArtifact | null;
  isStreaming: boolean;
}

export function DiagramWorkspace({ artifact, isStreaming }: Props) {
  if (!artifact) {
    return (
      <div
        className="flex-1 flex items-center justify-center text-[0.85rem]"
        style={{ color: "var(--color-muted)" }}
      >
        {isStreaming ? "◉ Apex is sketching your diagram…" : "No diagram yet."}
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-auto p-6">
      <div
        className="rounded-[12px] border p-6"
        style={{ background: "var(--color-card)", borderColor: "var(--color-border)" }}
      >
        <MermaidRenderer source={artifact.diagram} />
      </div>
    </div>
  );
}
