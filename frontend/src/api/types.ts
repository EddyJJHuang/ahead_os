/** Types matching api_server.py on port 8100 (ahead_os contract). */

export type Role = "user" | "assistant" | "tool";

export interface ChatMessage {
  role: Role;
  content: string;
}

export interface ChatRequest {
  messages: ChatMessage[];
  max_rounds?: number;
}

export type TraceStep =
  | { type: "tool_call"; name: string; args: Record<string, unknown> }
  | { type: "tool_result"; name: string; result: unknown }
  | { type: "assistant"; content: string };

export interface ChatResponse {
  answer: string;
  trace: TraceStep[];
}

export type ChatStreamEvent =
  | { type: "token"; text: string }
  | { type: "tool_call"; name: string; args: Record<string, unknown> }
  | { type: "tool_result"; name: string; result: unknown }
  | { type: "error"; message: string }
  | { type: "done" };

export interface SqlRequest {
  question: string;
  max_rows?: number;
}

export interface SqlResponse {
  sql?: string;
  columns?: string[];
  rows?: Array<Array<string | number | null>>;
  error?: string;
  raw?: string;
}

export interface RagRequest {
  query: string;
  k?: number;
}

export interface RagHit {
  rank?: number;
  score?: number;
  source?: string;
  chunk_index?: number;
  text?: string;
  error?: string;
}

export interface RagResponse {
  hits: RagHit[];
}

export interface HealthResponse {
  status: string;
  model_id: string;
  vllm: boolean;
  mock: boolean;
}

export interface ConfigResponse {
  model_id: string;
  openai_base_url: string;
  mock_base_url: string;
  capabilities: Array<"chat" | "sql" | "rag">;
  tools: string[];
}
