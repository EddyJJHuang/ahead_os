/** PM OS dashboard view models (not part of the :8100 API contract). */

export interface ExecutiveDecisionData {
  headline: string;
  ship_readiness: string;
  recommendation: string;
  risk_level: string;
  evidence_strength: string;
  evidence_sources: string[];
  summary: string;
  live_enriched?: boolean;
}

export interface ActionItem {
  id: string;
  title: string;
  impact: string;
  effort: string;
  rationale?: string;
}

export interface DraftContent {
  action_id: string;
  action_title: string;
  subject: string;
  body: string;
}

export interface EvidenceItem {
  id: string;
  source: string;
  title: string;
  snippet: string;
  detail: string;
  severity: "critical" | "high" | "medium" | "low";
  origin: "live" | "demo";
}

export interface PanelLoadState {
  executive: ExecutiveDecisionData;
  actions: ActionItem[];
  evidence: EvidenceItem[];
  backendReachable: boolean;
  modelReady: boolean;
  usingMockPanels: boolean;
}
