/**
 * Loads PM OS panel data from the real triage engine (:8100 /api/pm/analysis).
 * Every conclusion shown is computed live on the GB10 (deterministic facts +
 * Nemotron narrative). demoData.ts is used ONLY when the backend is unreachable.
 */

import { getHealth, postAnalysis } from "../api/client";
import type {
  PmAnalysisResponse,
  PmEvidenceRef,
  PmRisk,
} from "../api/types";
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

// evidence-ref type -> Evidence Drawer source label (must match its filter chips)
const SOURCE_LABEL: Record<string, string> = {
  jira: "Jira",
  github: "GitHub",
  email: "Email",
  calendar: "Calendar",
  task: "Tasks",
};

type Severity = EvidenceItem["severity"];

function severityFrom(risk: string): Severity {
  const s = risk.toLowerCase();
  if (s === "critical") return "critical";
  if (s === "high") return "high";
  if (s === "medium") return "medium";
  return "low";
}

function mapExecutive(a: PmAnalysisResponse): ExecutiveDecisionData {
  const { ship_readiness: sr, executive_summary: es } = a;
  return {
    headline: es.headline || "Enterprise Checkout launch readiness",
    ship_readiness: sr.decision,
    recommendation: sr.recommended_action,
    risk_level: sr.risk_level,
    evidence_strength: sr.evidence_strength,
    evidence_sources: sr.based_on,
    summary: es.narrative,
    live_enriched: true,
  };
}

function mapActions(a: PmAnalysisResponse): ActionItem[] {
  // Panel is "Top 3 Actions" — take the highest-ranked three.
  return a.actions.slice(0, 3).map((act) => ({
    id: act.id,
    title: act.title,
    impact: act.impact,
    effort: act.effort,
    rationale: act.rationale,
    draft_kind: act.draft_kind,
    context: act.context,
  }));
}

/** Flatten the risks' cross-linked evidence chains into Evidence Drawer cards. */
function mapEvidence(a: PmAnalysisResponse): EvidenceItem[] {
  const out: EvidenceItem[] = [];
  const seen = new Set<string>();
  for (const risk of a.risks as PmRisk[]) {
    const severity = severityFrom(risk.severity);
    for (const e of risk.evidence as PmEvidenceRef[]) {
      const key = `${e.type}-${e.id}`;
      if (seen.has(key)) continue;
      seen.add(key);
      out.push({
        id: `ev-${key}`,
        source: SOURCE_LABEL[e.type] ?? "Knowledge",
        title: `${e.id} — ${e.title}`,
        snippet: risk.risk,
        detail: `Why it matters: ${risk.risk}\n\nMitigation: ${risk.mitigation}`,
        severity,
        origin: "live",
      });
    }
  }
  return out;
}

function demoState(reachable: boolean, modelReady: boolean): PanelLoadState {
  return {
    executive: DEMO_EXECUTIVE,
    actions: DEMO_ACTIONS,
    evidence: DEMO_EVIDENCE,
    backendReachable: reachable,
    modelReady,
    usingMockPanels: true,
  };
}

export async function loadPanelData(): Promise<PanelLoadState> {
  const [health, analysis] = await Promise.all([getHealth(), postAnalysis()]);
  const backendReachable = health?.status === "ok";
  const modelReady = health?.vllm === true;

  // The triage engine returns valid deterministic data even if the LLM
  // narrative falls back, so gate on the analysis payload, not modelReady.
  if (!backendReachable || !analysis) {
    return demoState(backendReachable ?? false, modelReady);
  }

  return {
    executive: mapExecutive(analysis),
    actions: mapActions(analysis),
    evidence: mapEvidence(analysis),
    backendReachable: true,
    modelReady,
    usingMockPanels: false,
  };
}
