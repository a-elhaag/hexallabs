"use client";

import { useState } from "react";

interface CodeBlockProps {
  code: string;
  language?: string;
}

export function CodeBlock({ code, language }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  function handleCopy() {
    void navigator.clipboard.writeText(code).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <div
      className="relative rounded-[14px] border overflow-hidden"
      style={{
        background: "#1e1e1e",
        borderColor: "var(--color-border)",
      }}
    >
      {/* Header bar */}
      {language && (
        <div
          className="flex items-center justify-between px-5 py-2 border-b"
          style={{ borderColor: "var(--color-border)" }}
        >
          <span
            className="text-[0.68rem] font-semibold uppercase tracking-widest"
            style={{ color: "var(--color-muted)" }}
          >
            {language}
          </span>
        </div>
      )}

      {/* Copy button */}
      <button
        onClick={handleCopy}
        aria-label="Copy code"
        className="absolute top-[0.6rem] right-[0.75rem] flex items-center gap-1.5 px-3 py-1 rounded-[8px] text-[0.68rem] font-semibold transition-all duration-[180ms] cursor-pointer"
        style={{
          background: copied ? "rgba(98,144,195,0.18)" : "rgba(168,144,128,0.10)",
          color: copied ? "#6290c3" : "var(--color-muted)",
          border: `1px solid ${copied ? "rgba(98,144,195,0.3)" : "rgba(168,144,128,0.15)"}`,
        }}
      >
        {copied ? (
          <>
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="20 6 9 17 4 12" />
            </svg>
            Copied!
          </>
        ) : (
          <>
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
            </svg>
            Copy
          </>
        )}
      </button>

      {/* Code */}
      <pre
        className="overflow-x-auto"
        style={{
          padding: "1.25rem 1.5rem",
          margin: 0,
          fontFamily: "var(--font-mono), ui-monospace, monospace",
          fontSize: "0.82rem",
          lineHeight: 1.65,
          color: "#d4c8be",
          whiteSpace: "pre",
        }}
      >
        <code>{code}</code>
      </pre>
    </div>
  );
}
