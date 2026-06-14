// pm_types.ts — TypeScript contract for Local PM OS (api_server.py, port 8100).
// Matches the /api/pm/* endpoints. Generated alternative:
//   npx openapi-typescript http://<GB10_HOST>:8100/openapi.json -o src/api.d.ts

export type Decision = "YES" | "NO";
export type RiskLevel = "Low" | "Medium" | "High" | "Critical";
export type SourceName = "jira" | "github" | "emails" | "slack" | "calendar" | "tasks";
export type DraftKind =
  | "jira_comment" | "slack_update" | "decision_memo" | "stakeholder_email" | "followup_task";

export interface EvidenceRef {
  type: "jira" | "github" | "email" | "calendar" | "task" | "doc";
  id: string;        // e.g. "CHK-101", "PR-88", "EM-2001", "TASK-2"
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
  narrative: string; // LLM-generated
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

export interface ActionItem {
  id: string;
  title: string;
  impact: "High" | "Medium" | "Low";
  effort: string;          // e.g. "5 min"
  draft_kind: DraftKind;   // pass to POST /api/pm/draft
  rationale: string;
  context: string;         // pass as `context` to POST /api/pm/draft
  evidence: EvidenceRef[];
}

export interface AnalysisResponse {
  ship_readiness: ShipReadiness;
  executive_summary: ExecutiveSummary;
  criteria: Criterion[];
  risks: Risk[];
  actions: ActionItem[];
  stats: Record<SourceName, number>;
  generated_at: string;
}

export interface ChatMessage { role: "user" | "assistant" | "tool"; content: string; }

export type TraceStep =
  | { type: "tool_call"; name: string; args: Record<string, unknown> }
  | { type: "tool_result"; name: string; result: unknown };

export interface AskResponse { answer: string; trace: TraceStep[]; }

export type AskStreamEvent =
  | { type: "token"; text: string }
  | { type: "tool_call"; name: string; args: Record<string, unknown> }
  | { type: "tool_result"; name: string; result: unknown }
  | { type: "error"; message: string }
  | { type: "done" };

export interface DraftRequest { kind: DraftKind; context: string; }
export interface DraftResponse { kind: DraftKind; draft: string; }

export interface SourceResponse {
  source: SourceName;
  count: number;
  meta: Record<string, unknown>;
  records: Array<Record<string, unknown>>;
}

// --- tiny typed client (copy/adapt) ----------------------------------------
export class PMClient {
  constructor(private base = "http://localhost:8100") {}
  private post(b: unknown): RequestInit {
    return { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b) };
  }
  health() { return fetch(`${this.base}/health`).then((r) => r.json()); }
  analysis(): Promise<AnalysisResponse> { return fetch(`${this.base}/api/pm/analysis`, this.post({})).then((r) => r.json()); }
  draft(b: DraftRequest): Promise<DraftResponse> { return fetch(`${this.base}/api/pm/draft`, this.post(b)).then((r) => r.json()); }
  ask(messages: ChatMessage[]): Promise<AskResponse> { return fetch(`${this.base}/api/pm/ask`, this.post({ messages })).then((r) => r.json()); }
  sources(): Promise<Record<SourceName, number>> { return fetch(`${this.base}/api/pm/sources`).then((r) => r.json()); }
  source(s: SourceName): Promise<SourceResponse> { return fetch(`${this.base}/api/pm/sources/${s}`).then((r) => r.json()); }

  async askStream(messages: ChatMessage[], onEvent: (e: AskStreamEvent) => void): Promise<void> {
    const res = await fetch(`${this.base}/api/pm/ask/stream`, this.post({ messages }));
    const reader = res.body!.getReader();
    const dec = new TextDecoder();
    let buf = "";
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      const frames = buf.split("\n\n");
      buf = frames.pop() ?? "";
      for (const f of frames) {
        const line = f.split("\n").find((l) => l.startsWith("data:"));
        if (line) onEvent(JSON.parse(line.slice(5).trim()) as AskStreamEvent);
      }
    }
  }
}
