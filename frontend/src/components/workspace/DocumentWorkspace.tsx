"use client";

import { useMemo } from "react";
import type { DocumentArtifact } from "~/lib/api/types";

interface Props {
  streamingText: string;
  artifact: DocumentArtifact | null;
  isStreaming: boolean;
}

interface Heading {
  id: string;
  level: number;
  text: string;
}

export function DocumentWorkspace({ streamingText, artifact, isStreaming }: Props) {
  const markdown = artifact?.markdown ?? streamingText;

  const headings = useMemo<Heading[]>(() => extractHeadings(markdown), [markdown]);
  const html = useMemo(() => renderMarkdown(markdown), [markdown]);

  return (
    <div className="flex flex-1 overflow-hidden">
      <div className="flex-1 overflow-y-auto px-8 py-8">
        <article
          className="max-w-[780px] mx-auto text-[0.92rem] leading-[1.75] prose-doc"
          style={{ color: "var(--color-surface)" }}
          dangerouslySetInnerHTML={{ __html: html }}
        />
        {isStreaming && (
          <div
            className="max-w-[780px] mx-auto mt-6 text-[0.65rem] uppercase tracking-[0.12em] font-bold"
            style={{ color: "var(--color-mode)" }}
          >
            ◉ Apex · writing
          </div>
        )}
      </div>

      {headings.length > 0 && (
        <aside
          className="hidden lg:flex flex-col w-[220px] border-l flex-shrink-0 p-4 overflow-y-auto"
          style={{ borderColor: "var(--color-border)", background: "var(--color-panel)" }}
        >
          <div
            className="text-[0.6rem] font-bold uppercase tracking-[0.12em] mb-3"
            style={{ color: "var(--color-muted)" }}
          >
            On this page
          </div>
          <ul className="flex flex-col gap-1.5">
            {headings.map((h) => (
              <li key={h.id}>
                <a
                  href={`#${h.id}`}
                  className="block text-[0.72rem] no-underline hover:opacity-70"
                  style={{
                    color: "var(--color-muted)",
                    paddingLeft: `${(h.level - 1) * 10}px`,
                  }}
                >
                  {h.text}
                </a>
              </li>
            ))}
          </ul>
        </aside>
      )}

      <style>{`
        .prose-doc h1 { font-size: 1.75rem; font-weight: 800; margin: 1.4em 0 0.6em; letter-spacing: -0.02em; }
        .prose-doc h2 { font-size: 1.3rem; font-weight: 700; margin: 1.6em 0 0.5em; letter-spacing: -0.01em; }
        .prose-doc h3 { font-size: 1.05rem; font-weight: 700; margin: 1.4em 0 0.4em; }
        .prose-doc p  { margin: 0.8em 0; }
        .prose-doc ul, .prose-doc ol { margin: 0.6em 0 0.6em 1.4em; }
        .prose-doc li { margin: 0.25em 0; }
        .prose-doc code { background: var(--color-card); padding: 2px 5px; border-radius: 4px; font-size: 0.85em; }
        .prose-doc pre { background: var(--color-card); padding: 12px 16px; border-radius: 8px; overflow-x: auto; margin: 0.9em 0; }
        .prose-doc pre code { background: none; padding: 0; }
        .prose-doc a { color: var(--color-mode); }
      `}</style>
    </div>
  );
}

function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, "")
    .trim()
    .replace(/\s+/g, "-");
}

function extractHeadings(md: string): Heading[] {
  const out: Heading[] = [];
  for (const line of md.split("\n")) {
    const match = /^(#{1,3})\s+(.+)/.exec(line);
    if (!match) continue;
    const text = match[2]!.trim();
    out.push({ id: slugify(text), level: match[1]!.length, text });
  }
  return out;
}

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderInline(s: string): string {
  let out = escapeHtml(s);
  out = out.replace(/`([^`]+)`/g, "<code>$1</code>");
  out = out.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  out = out.replace(/(^|[^*])\*([^*]+)\*/g, "$1<em>$2</em>");
  out = out.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noreferrer">$1</a>');
  return out;
}

function renderMarkdown(md: string): string {
  const lines = md.split("\n");
  const html: string[] = [];
  let inCode = false;
  let codeBuf: string[] = [];
  let inList = false;
  let inOrdered = false;

  const closeList = () => {
    if (inList) { html.push(inOrdered ? "</ol>" : "</ul>"); inList = false; inOrdered = false; }
  };

  for (const line of lines) {
    if (line.trimStart().startsWith("```")) {
      if (inCode) {
        html.push(`<pre><code>${escapeHtml(codeBuf.join("\n"))}</code></pre>`);
        inCode = false;
        codeBuf = [];
      } else {
        closeList();
        inCode = true;
      }
      continue;
    }
    if (inCode) { codeBuf.push(line); continue; }

    const heading = /^(#{1,3})\s+(.+)/.exec(line);
    if (heading) {
      closeList();
      const level = heading[1]!.length;
      const text = heading[2]!.trim();
      html.push(`<h${level} id="${slugify(text)}">${renderInline(text)}</h${level}>`);
      continue;
    }

    const ul = /^\s*[-*]\s+(.+)/.exec(line);
    const ol = /^\s*\d+\.\s+(.+)/.exec(line);
    if (ul) {
      if (!inList || inOrdered) { closeList(); html.push("<ul>"); inList = true; inOrdered = false; }
      html.push(`<li>${renderInline(ul[1]!)}</li>`);
      continue;
    }
    if (ol) {
      if (!inList || !inOrdered) { closeList(); html.push("<ol>"); inList = true; inOrdered = true; }
      html.push(`<li>${renderInline(ol[1]!)}</li>`);
      continue;
    }

    if (!line.trim()) { closeList(); continue; }

    closeList();
    html.push(`<p>${renderInline(line)}</p>`);
  }

  if (inCode) html.push(`<pre><code>${escapeHtml(codeBuf.join("\n"))}</code></pre>`);
  closeList();

  return html.join("\n");
}
