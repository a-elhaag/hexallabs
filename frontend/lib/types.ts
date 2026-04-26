// lib/types.ts

export type Mode = 'oracle' | 'council' | 'relay'

export type ScoutMode = 'off' | 'auto' | 'force'

export const MODELS = [
  'Apex', 'Swift', 'Prism', 'Depth', 'Atlas', 'Horizon', 'Pulse',
  'Bolt', 'Craft', 'Flux', 'Spark'
] as const

export type ModelName = typeof MODELS[number]

export const MODEL_DISPLAY: Record<ModelName, string> = {
  Apex:    'Apex',
  Swift:   'Swift',
  Prism:   'Prism',
  Depth:   'Depth',
  Atlas:   'Atlas',
  Horizon: 'Horizon',
  Pulse:   'Pulse',
  Bolt:    'Bolt',
  Craft:   'Craft',
  Flux:    'Flux',
  Spark:   'Spark',
}

export const MODEL_SUBTITLE: Record<ModelName, string> = {
  Apex:    'Claude Opus 4.7',
  Pulse:   'Claude Sonnet 4.6',
  Swift:   'Claude Haiku 4.5',
  Prism:   'Grok 4 Reasoning',
  Bolt:    'Grok 4 Fast',
  Craft:   'GPT-5.4 Mini',
  Flux:    'GPT-5.3',
  Spark:   'GPT-5.4 Nano',
  Depth:   'DeepSeek V3.2',
  Atlas:   'Llama 4 Maverick',
  Horizon: 'Kimi K2.5',
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  model?: ModelName
  isStreaming?: boolean
}

// SSE event payloads — mirrors backend sse/events.py
export interface SseSession    { session_id: string; mode: string }
export interface SseToken      { hex: string; delta: string }
export interface SseSynthToken { delta: string }
export interface SsePeerReview { from: string; to: string; critique: string }
export interface SseDone       { session_id: string; duration_ms: number }
export interface SseError      { hex: string; code: string; message: string }
export interface SseHexStart   { hex: string }
export interface SseHexDone    { hex: string; tokens: number; cached_tokens: number }
export interface SseSynthStart { }
export interface SseSynthDone  { tokens: number }
export interface SseConfidence { hex: string; score: number; stage: 'initial' | 'post_review' }
export interface SseRelayHandoff { from: string; to: string; trigger: string; reason: string; partial_chars: number }
export interface SseToolCall   { hex: string; id: string; name: string; input: Record<string, unknown>; forced?: boolean }
export interface SseToolResult { hex: string; id: string; name: string; summary: string; urls: string[]; result_count: number; error?: string }

export type SseEventMap = {
  session:        SseSession
  token:          SseToken
  synth_token:    SseSynthToken
  synth_start:    SseSynthStart
  synth_done:     SseSynthDone
  peer_review:    SsePeerReview
  done:           SseDone
  error:          SseError
  hex_start:      SseHexStart
  hex_done:       SseHexDone
  confidence:     SseConfidence
  relay_handoff:  SseRelayHandoff
  tool_call:      SseToolCall
  tool_result:    SseToolResult
  primal:         { text: string }
  lens:           { hex: string; interpretation: string }
  prompt_forge:   { original: string; improved: string }
  quota_warning:  { percentage_used: number; resets_at: string }
}

export interface QueryRequest {
  mode: Mode
  query: string
  models: ModelName[]
  relay_chain?: ModelName[]
  workflow_nodes?: Record<string, unknown>[]
  primal_protocol?: boolean
  scout?: ScoutMode
  session_id?: string
  force_relay_demo?: boolean
}

export interface ForgeResponse {
  improved_query: string
}

export interface QuotaStatus {
  percentage_used: number
  window_started: boolean
  window_start: string | null
  resets_at: string | null
}
