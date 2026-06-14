/** PM OS dashboard view models (mapped from /api/pm/* responses). */

import type { DraftKind } from "./api/pm_types";

export interface ExecutiveDecisionData {
  headline: string;
  ship_readiness: string;
  recommendation: string;
  risk_level: string;
  evidence_strength: string;
  evidence_sources: string[];
  summary: string;
}

export type ArtifactType = "email" | "meeting" | "review";

export interface ActionItem {
  id: string;
  title: string;
  impact: string;
  effort: string;
  rationale?: string;
  explanation?: string;
  ctaLabel?: string;
  artifactType?: ArtifactType;
  draft_kind?: DraftKind;
  context?: string;
}

export interface EmailArtifact {
  type: "email";
  action_id: string;
  to: string;
  subject: string;
  body: string;
}

export interface MeetingArtifact {
  type: "meeting";
  action_id: string;
  title: string;
  datetime: string;
  attendees: string;
  agenda: string;
}

export interface ReviewArtifact {
  type: "review";
  action_id: string;
  target: string;
  message: string;
  reviewer: string;
}

export type ExecutionArtifact = EmailArtifact | MeetingArtifact | ReviewArtifact;

export type CompletedActionStatus = "Sent" | "Scheduled" | "Posted";

export interface CompletedAction {
  id: string;
  title: string;
  status: CompletedActionStatus;
}

/** @deprecated Use ExecutionArtifact */
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

export type ActivityFeedIcon =
  | "alert"
  | "scan"
  | "link"
  | "gap"
  | "draft"
  | "decision"
  | "tool";

export interface ActivityFeedItem {
  id: string;
  time: string;
  text: string;
  icon: ActivityFeedIcon;
  live?: boolean;
}
