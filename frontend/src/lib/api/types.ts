export type ScoutMode = "off" | "auto" | "force";
export type QueryMode = "council" | "oracle" | "relay" | "workflow";

export interface QueryRequest {
  mode: QueryMode;
  query: string;
  models?: string[];
  relay_chain?: string[];
  workflow_nodes?: Record<string, unknown>[];
  primal_protocol?: boolean;
  scout?: ScoutMode;
  session_id?: string | null;
}

export interface SseEvent<T = unknown> {
  event: string;
  data: T;
}

// Per-event data shapes
export interface SessionData { session_id: string }
export interface HexStartData { hex: string }
export interface HexTokenData { hex: string; token: string }
export interface ConfidenceData { hex: string; score: number }
export interface HexDoneData { hex: string }
export interface ApexTokenData { token: string }
export interface PrimalData { text: string }
export interface ToolCallData { name: string; input: unknown }
export interface ToolResultData { name: string; output: unknown }
export interface ErrorData { code: string; message: string }

export type WorkspaceKind = "chat" | "code" | "spreadsheet" | "diagram" | "document";
export interface WorkspaceData { kind: WorkspaceKind; reason: string }

export interface CodeArtifact { language: string; code: string; filename: string }
export interface SpreadsheetArtifact { columns: string[]; rows: string[][] }
export interface DiagramArtifact { diagram: string; format: string }
export interface DocumentArtifact { markdown: string }
export type ArtifactPayload =
  | CodeArtifact
  | SpreadsheetArtifact
  | DiagramArtifact
  | DocumentArtifact
  | Record<string, unknown>;
export interface ArtifactData { kind: WorkspaceKind; payload: ArtifactPayload }
