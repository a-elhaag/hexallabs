"use client";

import { useEffect, useState } from "react";
import type { SpreadsheetArtifact } from "~/lib/api/types";

interface Props {
  artifact: SpreadsheetArtifact | null;
  isStreaming: boolean;
}

export function SpreadsheetWorkspace({ artifact, isStreaming }: Props) {
  const [rows, setRows] = useState<string[][]>([]);

  useEffect(() => {
    if (artifact) setRows(artifact.rows.map((r) => [...r]));
  }, [artifact]);

  if (!artifact) {
    return (
      <div
        className="flex-1 flex items-center justify-center text-[0.85rem]"
        style={{ color: "var(--color-muted)" }}
      >
        {isStreaming ? "◉ Apex is preparing your sheet…" : "No data yet."}
      </div>
    );
  }

  const updateCell = (r: number, c: number, v: string) => {
    setRows((prev) => {
      const next = prev.map((row) => [...row]);
      next[r]![c] = v;
      return next;
    });
  };

  return (
    <div className="flex-1 overflow-auto p-4">
      <table
        className="min-w-full border-collapse text-[0.8rem]"
        style={{ background: "var(--color-card)", color: "var(--color-surface)" }}
      >
        <thead>
          <tr>
            {artifact.columns.map((col) => (
              <th
                key={col}
                className="px-3 py-2 text-left font-semibold border"
                style={{ borderColor: "var(--color-border)", background: "var(--color-panel)" }}
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, r) => (
            <tr key={r}>
              {row.map((cell, c) => (
                <td
                  key={c}
                  className="border p-0"
                  style={{ borderColor: "var(--color-border)" }}
                >
                  <input
                    className="w-full px-3 py-2 bg-transparent outline-none focus:bg-[var(--color-panel)]"
                    value={cell}
                    onChange={(e) => updateCell(r, c, e.target.value)}
                  />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
