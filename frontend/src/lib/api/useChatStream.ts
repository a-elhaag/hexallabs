"use client";

import { useCallback, useRef } from "react";
import { streamSSE } from "./fetcher";
import type {
  QueryRequest,
  SessionData,
  HexStartData,
  HexTokenData,
  ConfidenceData,
  HexDoneData,
  ApexTokenData,
  PrimalData,
  ToolCallData,
  ToolResultData,
  ErrorData,
} from "./types";

export interface ChatStreamCallbacks {
  onSession?: (data: SessionData) => void;
  onHexStart?: (data: HexStartData) => void;
  onHexToken?: (data: HexTokenData) => void;
  onConfidence?: (data: ConfidenceData) => void;
  onHexDone?: (data: HexDoneData) => void;
  onApexToken?: (data: ApexTokenData) => void;
  onApexDone?: () => void;
  onPrimal?: (data: PrimalData) => void;
  onToolCall?: (data: ToolCallData) => void;
  onToolResult?: (data: ToolResultData) => void;
  onError?: (data: ErrorData) => void;
  onDone?: () => void;
}

export function useChatStream(callbacks: ChatStreamCallbacks) {
  const abortRef = useRef<AbortController | null>(null);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
  }, []);

  const start = useCallback(
    async (req: QueryRequest) => {
      stop();
      const controller = new AbortController();
      abortRef.current = controller;

      try {
        for await (const { event, data } of streamSSE("/api/query", req, controller.signal)) {
          if (controller.signal.aborted) break;

          switch (event) {
            case "session":
              callbacks.onSession?.(data as SessionData);
              break;
            case "hex_start":
              callbacks.onHexStart?.(data as HexStartData);
              break;
            case "hex_token":
              callbacks.onHexToken?.(data as HexTokenData);
              break;
            case "confidence":
              callbacks.onConfidence?.(data as ConfidenceData);
              break;
            case "hex_done":
              callbacks.onHexDone?.(data as HexDoneData);
              break;
            case "apex_token":
              callbacks.onApexToken?.(data as ApexTokenData);
              break;
            case "apex_done":
              callbacks.onApexDone?.();
              break;
            case "primal":
              callbacks.onPrimal?.(data as PrimalData);
              break;
            case "tool_call":
              callbacks.onToolCall?.(data as ToolCallData);
              break;
            case "tool_result":
              callbacks.onToolResult?.(data as ToolResultData);
              break;
            case "error":
              callbacks.onError?.(data as ErrorData);
              break;
            case "done":
              callbacks.onDone?.();
              break;
          }
        }
      } catch (err) {
        if (err instanceof Error && err.name !== "AbortError") {
          throw err;
        }
      }
    },
    [callbacks, stop],
  );

  return { start, stop };
}
