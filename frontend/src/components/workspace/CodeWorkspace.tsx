"use client";

import { useMemo, useState } from "react";
import dynamic from "next/dynamic";
import type { CodeArtifact } from "~/lib/api/types";

const CodeHighlighter = dynamic(() => import("./CodeHighlighter"), {
  ssr: false,
  loading: () => null,
});

interface Props {
  streamingText: string;
  artifact: CodeArtifact | null;
  isStreaming: boolean;
}

export function CodeWorkspace({ streamingText, artifact, isStreaming }: Props) {
  const [copied, setCopied] = useState(false);

  const { code, language, filename } = useMemo(() => {
    if (artifact) return artifact;
    const extracted = extractFencedCode(streamingText);
    return {
      code: extracted.code || streamingText,
      language: extracted.lang || "text",
      filename: guessFilename(extracted.lang || "text"),
    };
  }, [artifact, streamingText]);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    } catch {
      // no-op
    }
  }

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      <div
        className="flex items-center gap-2 px-4 h-10 border-b flex-shrink-0"
        style={{ background: "var(--color-panel)", borderColor: "var(--color-border)" }}
      >
        <div
          className="px-3 py-1 rounded-t-[6px] text-[0.7rem] font-semibold"
          style={{
            background: "var(--color-card)",
            color: "var(--color-surface)",
            border: "1px solid var(--color-border)",
            borderBottom: "none",
          }}
        >
          {filename}
        </div>
        <span
          className="text-[0.6rem] uppercase tracking-[0.12em] font-bold"
          style={{ color: "var(--color-muted)" }}
        >
          {language}
        </span>
        <div className="flex-1" />
        {isStreaming && (
          <span
            className="text-[0.6rem] uppercase tracking-[0.12em] font-bold"
            style={{ color: "var(--color-mode)" }}
          >
            ◉ Apex · streaming
          </span>
        )}
        <button
          type="button"
          onClick={handleCopy}
          disabled={!code}
          className="px-3 py-1 rounded-[6px] text-[0.65rem] font-semibold cursor-pointer transition-opacity hover:opacity-80 disabled:opacity-40"
          style={{
            background: "var(--color-card)",
            border: "1px solid var(--color-border)",
            color: "var(--color-surface)",
          }}
        >
          {copied ? "Copied" : "Copy"}
        </button>
      </div>

      <div
        className="flex-1 overflow-auto code-pane"
        style={{ background: "var(--color-bg)" }}
      >
        {code ? (
          <div className="p-6">
            <CodeHighlighter code={code} language={language} />
          </div>
        ) : (
          <pre
            className="m-0 p-6 text-[0.78rem] leading-[1.6] font-mono whitespace-pre"
            style={{ color: "var(--color-muted)" }}
          >
            <code>{isStreaming ? "◉ Apex is preparing code…" : ""}</code>
          </pre>
        )}
      </div>
      <style>{`
        .code-pane .shiki-host pre { margin: 0; background: transparent !important; }
        .code-pane .shiki-host code { background: transparent; padding: 0; }
      `}</style>
    </div>
  );
}

function extractFencedCode(text: string): { code: string; lang: string } {
  const lines = text.split("\n");
  let inside = false;
  let lang = "";
  const buf: string[] = [];
  for (const line of lines) {
    if (line.trimStart().startsWith("```")) {
      if (inside) break;
      inside = true;
      lang = line.trimStart().slice(3).trim();
      continue;
    }
    if (inside) buf.push(line);
  }
  return { code: buf.join("\n"), lang };
}

function guessFilename(lang: string): string {
  const map: Record<string, string> = {
    python: "main.py", py: "main.py",
    typescript: "main.ts", ts: "main.ts", tsx: "main.tsx",
    javascript: "main.js", js: "main.js", jsx: "main.jsx",
    go: "main.go", rust: "main.rs", rs: "main.rs",
    sql: "query.sql", bash: "script.sh", sh: "script.sh",
  };
  return map[lang.toLowerCase()] ?? `snippet.${lang || "txt"}`;
}
