"use client";

import { useEffect, useRef, useState } from "react";

interface Props {
  source: string;
}

let mermaidPromise: Promise<typeof import("mermaid").default> | null = null;

function getMermaid() {
  if (!mermaidPromise) {
    mermaidPromise = import("mermaid").then((mod) => {
      const mermaid = mod.default;
      mermaid.initialize({
        startOnLoad: false,
        securityLevel: "strict",
        theme: "base",
        themeVariables: {
          primaryColor: "#6290c3",
          primaryTextColor: "#f5f1ed",
          primaryBorderColor: "#6290c3",
          lineColor: "#a89080",
          secondaryColor: "#2c2c2c",
          tertiaryColor: "#1a1a1a",
          background: "#2c2c2c",
          mainBkg: "#2c2c2c",
          nodeBorder: "#6290c3",
          clusterBkg: "#2c2c2c",
          clusterBorder: "#a89080",
          textColor: "#f5f1ed",
        },
        fontFamily: "inherit",
      });
      return mermaid;
    });
  }
  return mermaidPromise;
}

export default function MermaidRenderer({ source }: Props) {
  const [svg, setSvg] = useState<string>("");
  const [error, setError] = useState<string>("");
  const idRef = useRef<string>(`mmd-${Math.random().toString(36).slice(2)}`);

  useEffect(() => {
    let cancelled = false;
    setError("");
    getMermaid()
      .then(async (mermaid) => {
        try {
          const parsed = await mermaid.parse(source, { suppressErrors: true });
          if (parsed === false) {
            throw new Error("Invalid mermaid syntax");
          }
          const { svg: rendered } = await mermaid.render(idRef.current, source);
          if (!cancelled) setSvg(rendered);
        } catch (err) {
          if (!cancelled) {
            setSvg("");
            setError(err instanceof Error ? err.message : String(err));
          }
        }
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : String(err));
      });

    return () => {
      cancelled = true;
    };
  }, [source]);

  if (error) {
    return (
      <div className="flex flex-col gap-3">
        <div
          className="rounded-[8px] border px-3 py-2 text-[0.72rem]"
          style={{ background: "#3a2020", borderColor: "#c06060", color: "#f5c0c0" }}
        >
          Diagram parse failed — {error}
        </div>
        <pre
          className="m-0 text-[0.78rem] font-mono whitespace-pre-wrap rounded-[8px] border p-3"
          style={{ background: "var(--color-card)", borderColor: "var(--color-border)", color: "var(--color-surface)" }}
        >
          <code>{source}</code>
        </pre>
      </div>
    );
  }

  if (!svg) {
    return (
      <div
        className="text-[0.72rem]"
        style={{ color: "var(--color-muted)" }}
      >
        Rendering diagram…
      </div>
    );
  }

  return (
    <div
      className="w-full overflow-auto flex justify-center"
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}
