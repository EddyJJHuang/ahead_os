/**
 * Loads PM OS panels from POST /api/pm/analysis (+ GET /api/pm/sources),
 * falls back to demoData.ts when the backend is unreachable.
 */

import { getHealth, getPmSources, postPmAnalysis } from "../api/client";
import type {
  AnalysisResponse,
  EvidenceRef,
  RiskLevel,
} from "../api/pm_types";
import {
  DEMO_ACTIONS,
  DEMO_EVIDENCE,
  DEMO_EXECUTIVE,
} from "../mock/demoData";
import type {
  ActionItem,
  EvidenceItem,
  ExecutiveDecisionData,
  PanelLoadState,
} from "../types";

const SOURCE_LABELS: Record<string, string> = {
  jira: "Jira",
  github: "GitHub",
  email: "Email",
  emails: "Email",
  calendar: "Calendar",
  task: "Tasks",
  tasks: "Tasks",
  slack: "Slack",
  doc: "Docs",
};

function severityFromRisk(level: RiskLevel): EvidenceItem["severity"] {
  switch (level) {
    case "Critical":
      return "critical";
    case "High":
      return "high";
    case "Medium":
      return "medium";
    default:
      return "low";
  }
}

function sourceLabel(type: string): string {
  return SOURCE_LABELS[type.toLowerCase()] ?? type;
}

function refKey(ref: EvidenceRef): string {
  return `${ref.type}:${ref.id}`;
}

function mapExecutive(analysis: AnalysisResponse): ExecutiveDecisionData {
  const { ship_readiness, executive_summary } = analysis;
  return {
    headline: executive_summary.headline,
    ship_readiness: ship_readiness.decision,
    recommendation: ship_readiness.recommended_action,
    risk_level: ship_readiness.risk_level,
    evidence_strength: ship_readiness.evidence_strength,
    evidence_sources: ship_readiness.based_on,
    summary: executive_summary.narrative,
  };
}

function mapActions(analysis: AnalysisResponse): ActionItem[] {
  return analysis.actions.slice(0, 3).map((action) => ({
    id: action.id,
    title: action.title,
    impact: action.impact,
    effort: action.effort,
    rationale: action.rationale,
    draft_kind: action.draft_kind,
    context: action.context,
  }));
}

function refToEvidence(
  ref: EvidenceRef,
  severity: EvidenceItem["severity"],
  snippet: string,
  detail: string
): EvidenceItem {
  return {
    id: refKey(ref),
    source: sourceLabel(ref.type),
    title: `${ref.id} — ${ref.title}`,
    snippet,
    detail,
    severity,
    origin: "live",
  };
}

function mapEvidence(analysis: AnalysisResponse): EvidenceItem[] {
  const seen = new Set<string>();
  const items: EvidenceItem[] = [];

  for (const risk of analysis.risks) {
    const sev = severityFromRisk(risk.severity);
    for (const ref of risk.evidence) {
      const key = refKey(ref);
      if (seen.has(key)) continue;
      seen.add(key);
      items.push(
        refToEvidence(
          ref,
          sev,
          risk.risk,
          `${risk.mitigation}\n\nSource: ${ref.type}/${ref.id}${ref.ref ? ` (${ref.ref})` : ""}`
        )
      );
    }
  }

  for (const criterion of analysis.criteria) {
    for (const ref of criterion.evidence) {
      const key = refKey(ref);
      if (seen.has(key)) continue;
      seen.add(key);
      items.push(
        refToEvidence(
          ref,
          criterion.ok ? "low" : "high",
          criterion.detail,
          `${criterion.name}: ${criterion.detail}`
        )
      );
    }
  }

  return items;
}

export async function loadPanelData(): Promise<PanelLoadState> {
  const health = await getHealth();
  const backendReachable = health?.status === "ok";
  const modelReady = health?.vllm === true;

  if (!backendReachable) {
    return {
      executive: DEMO_EXECUTIVE,
      actions: DEMO_ACTIONS,
      evidence: DEMO_EVIDENCE,
      backendReachable: false,
      modelReady: false,
      usingMockPanels: true,
    };
  }

  const analysis = await postPmAnalysis();
  if (!analysis?.ship_readiness) {
    return {
      executive: DEMO_EXECUTIVE,
      actions: DEMO_ACTIONS,
      evidence: DEMO_EVIDENCE,
      backendReachable: true,
      modelReady,
      usingMockPanels: true,
    };
  }

  // Touch sources endpoint so Evidence Explorer reflects connected sources.
  await getPmSources();

  return {
    executive: mapExecutive(analysis),
    actions: mapActions(analysis),
    evidence: mapEvidence(analysis),
    backendReachable: true,
    modelReady,
    usingMockPanels: false,
  };
}
