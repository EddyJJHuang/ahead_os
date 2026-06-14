// Matches examples/pm_types.ts — Local PM OS contract (api_server.py :8100)

export type Decision = "YES" | "NO";
export type RiskLevel = "Low" | "Medium" | "High" | "Critical";
export type SourceName =
  | "jira"
  | "github"
  | "emails"
  | "slack"
  | "calendar"
  | "tasks";
export type DraftKind =
  | "jira_comment"
  | "slack_update"
  | "decision_memo"
  | "stakeholder_email"
  | "followup_task";

export interface EvidenceRef {
  type: "jira" | "github" | "email" | "calendar" | "task" | "doc";
  id: string;
  title: string;
  ref: string | null;
}

export interface ShipReadiness {
  decision: Decision;
  recommended_action: string;
  risk_level: RiskLevel;
  evidence_strength: string;
  based_on: string[];
  target_date: string;
}

export interface ExecutiveSummary {
  headline: string;
  what_changed: string[];
  whats_blocked: string[];
  recommended_decision: string;
  narrative: string;
}

export interface Criterion {
  name: string;
  ok: boolean;
  detail: string;
  evidence: EvidenceRef[];
}

export interface Risk {
  risk: string;
  severity: RiskLevel;
  evidence: EvidenceRef[];
  mitigation: string;
}

export interface PmActionItem {
  id: string;
  title: string;
  impact: "High" | "Medium" | "Low";
  effort: string;
  draft_kind: DraftKind;
  rationale: string;
  context: string;
  evidence: EvidenceRef[];
}

export interface AnalysisResponse {
  ship_readiness: ShipReadiness;
  executive_summary: ExecutiveSummary;
  criteria: Criterion[];
  risks: Risk[];
  actions: PmActionItem[];
  stats: Record<string, number>;
  generated_at: string;
}

export interface ChatMessage {
  role: "user" | "assistant" | "tool";
  content: string;
}

export type TraceStep =
  | { type: "tool_call"; name: string; args: Record<string, unknown> }
  | { type: "tool_result"; name: string; result: unknown };

export interface AskResponse {
  answer: string;
  trace: TraceStep[];
}

export type AskStreamEvent =
  | { type: "token"; text: string }
  | { type: "tool_call"; name: string; args: Record<string, unknown> }
  | { type: "tool_result"; name: string; result: unknown }
  | { type: "error"; message: string }
  | { type: "done" };

export interface DraftRequest {
  kind: DraftKind;
  context: string;
}

export interface DraftResponse {
  kind: DraftKind;
  draft: string;
}

export interface SourceResponse {
  source: SourceName;
  count: number;
  meta: Record<string, unknown>;
  records: Array<Record<string, unknown>>;
}

export type SourceCounts = Record<SourceName, number>;
