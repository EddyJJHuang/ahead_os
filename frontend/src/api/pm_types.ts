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


export interface AutonomyActionOption {
  id: string;
  title: string;
  impact: "High" | "Medium" | "Low";
  effort: string;
  rationale?: string;
  draft_kind?: DraftKind;
  context?: string;
  evidence: EvidenceRef[];
}

export interface AutonomySuggestion {
  id: string;
  title: string;
  severity: RiskLevel;
  urgent: boolean;
  changed_since_last_scan: boolean;
  decision: Decision;
  summary: string;
  why_now: string;
  detected_at: string;
  trigger: string;
  task_id: string | null;
  task_prompt: string | null;
  source_scope: SourceName[];
  evidence: EvidenceRef[];
  action_options: AutonomyActionOption[];
  analysis_generated_at: string | null;
  fingerprint: string;
  runtime: string;
}

export interface NemoClawRuntimeStatus {
  installed: boolean;
  name: string;
  phase: string;
  ok: boolean;
  model?: string;
  provider?: string;
  gateway_state?: string;
  openshell_driver?: string;
  openshell_version?: string;
  sandbox_gpu_enabled?: boolean;
  policies?: string[];
  detail?: string;
}

export interface AutonomyTask {
  id: string;
  title: string;
  prompt: string;
  cadence_minutes: number;
  source_scope: SourceName[];
  task_type: "monitor" | "creative";
  output_format: string | null;
  enabled: boolean;
  created_from: string;
  created_at: string;
  last_run_at: string | null;
  next_run_at: string | null;
  last_result: {
    ran_at?: string;
    suggestion_id?: string;
    urgent?: boolean;
    task_type?: "monitor" | "creative";
    output?: string;
    output_error?: string;
    error?: string;
  } | null;
}

export interface AutonomyStatusResponse {
  status: string;
  runtime: NemoClawRuntimeStatus;
  scheduler: {
    running: boolean;
    poll_seconds: number;
    task_count: number;
  };
  tasks: AutonomyTask[];
  latest_suggestion: AutonomySuggestion | null;
  last_scan_at: string | null;
  monitor_runs: number;
}

export interface AutonomyRunResponse {
  status: string;
  trigger: string;
  source_counts: Partial<SourceCounts>;
  suggestion: AutonomySuggestion;
  runtime: NemoClawRuntimeStatus;
}

export interface AutonomyTaskRequest {
  request: string;
}

export interface TaskPreview {
  request: string;
  title: string;
  cadence_minutes: number;
  source_scope: SourceName[];
  task_type: "monitor" | "creative";
  output_format: string | null;
}

export interface CreateAutonomyTaskResponse {
  status: string;
  task: AutonomyTask;
  result: {
    status: string;
    task: AutonomyTask;
    result: AutonomyRunResponse;
    output?: string | null;
    output_error?: string | null;
  } | null;
  latest_suggestion: AutonomySuggestion | null;
  runtime: NemoClawRuntimeStatus;
}

export interface DemoContextItem {
  id: string;
  source: string;
  title: string;
  snippet: string;
  detail: string;
  severity: "critical" | "high" | "medium" | "low";
  origin: "live" | "demo";
}

export interface DemoStatusResponse {
  emergency_active: boolean;
  pending_peacetime_signals: number;
  ingested_peacetime_signals: number;
}

export interface DemoIngestResponse {
  ingested: boolean;
  reason?: string;
  signal?: {
    source: string;
    record_key: string;
    record: Record<string, unknown>;
    context_item: DemoContextItem;
    remaining: number;
  } | null;
  status: DemoStatusResponse;
}

export interface EmergencyToggleResponse {
  emergency_active: boolean;
  suggestion?: AutonomySuggestion;
  runtime?: NemoClawRuntimeStatus;
}
