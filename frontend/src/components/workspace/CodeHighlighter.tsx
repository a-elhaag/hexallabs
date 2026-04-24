"use client";

import { useEffect, useRef, useState } from "react";
import type { Highlighter } from "shiki";

interface Props {
  code: string;
  language: string;
}

const THEME = "github-dark-dimmed";
const LANGS = [
  "typescript", "tsx", "javascript", "jsx", "python",
  "go", "rust", "sql", "bash", "json", "markdown", "yaml", "html", "css",
] as const;

let highlighterPromise: Promise<Highlighter> | null = null;

function getHighlighter() {
  if (!highlighterPromise) {
    highlighterPromise = import("shiki").then((mod) =>
      mod.createHighlighter({ themes: [THEME], langs: LANGS as unknown as string[] })
    );
  }
  return highlighterPromise;
}

function normalize(lang: string): string {
  const key = (lang || "").toLowerCase();
  const map: Record<string, string> = {
    ts: "typescript",
    js: "javascript",
    py: "python",
    rs: "rust",
    sh: "bash",
    shell: "bash",
    md: "markdown",
    yml: "yaml",
  };
  const out = map[key] ?? key;
  return (LANGS as readonly string[]).includes(out) ? out : "text";
}

export default function CodeHighlighter({ code, language }: Props) {
  const [html, setHtml] = useState<string>("");
  const prevRef = useRef<string>("");

  useEffect(() => {
    let cancelled = false;
    getHighlighter()
      .then((hl) => {
        const lang = normalize(language);
        const rendered = hl.codeToHtml(code || " ", { lang, theme: THEME });
        if (!cancelled) {
          prevRef.current = rendered;
          setHtml(rendered);
        }
      })
      .catch(() => {
        if (!cancelled && !prevRef.current) setHtml("");
      });
    return () => {
      cancelled = true;
    };
  }, [code, language]);

  if (!html) {
    return (
      <pre
        className="m-0 p-6 text-[0.78rem] leading-[1.6] font-mono whitespace-pre"
        style={{ background: "var(--color-bg)", color: "var(--color-surface)" }}
      >
        <code>{code}</code>
      </pre>
    );
  }

  return (
    <div
      className="shiki-host text-[0.78rem] leading-[1.6]"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
