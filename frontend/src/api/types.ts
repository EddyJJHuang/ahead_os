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
  capabilities: string[];
  tools: string[];
}

// --- Local PM OS endpoints (/api/pm/*) ------------------------------------

/** One node in a cross-linked evidence chain (risk -> Jira/PR/email/...). */
export interface PmEvidenceRef {
  type: string; // jira | github | email | calendar | task
  id: string;
  title: string;
  ref?: string | null;
}

export interface PmCriterion {
  name: string;
  ok: boolean;
  detail: string;
  evidence: PmEvidenceRef[];
}

export interface PmRisk {
  risk: string;
  severity: string; // Critical | High | Medium
  evidence: PmEvidenceRef[];
  mitigation: string;
}

export interface PmAction {
  id: string;
  title: string;
  impact: string;
  effort: string;
  draft_kind: string;
  rationale: string;
  context: string;
  evidence: PmEvidenceRef[];
}

export interface PmAnalysisResponse {
  ship_readiness: {
    decision: string; // NO | YES
    recommended_action: string;
    risk_level: string;
    evidence_strength: string;
    based_on: string[];
    target_date: string;
  };
  executive_summary: {
    headline: string;
    what_changed: string[];
    whats_blocked: string[];
    recommended_decision: string;
    narrative: string;
  };
  criteria: PmCriterion[];
  risks: PmRisk[];
  actions: PmAction[];
  stats: Record<string, number>;
  generated_at: string;
}

export interface PmDraftRequest {
  kind: string;
  context: string;
}

export interface PmDraftResponse {
  kind?: string;
  draft?: string;
  error?: string;
}

export interface PmAskRequest {
  messages: ChatMessage[];
  max_rounds?: number;
}

export interface PmAskResponse {
  answer: string;
  trace: unknown[];
}
