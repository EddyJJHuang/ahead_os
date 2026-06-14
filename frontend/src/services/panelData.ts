/**
 * Derives PM OS panel data from :8100 API where possible, falls back to demoData.ts.
 * TODO: POST /api/triage | GET /api/evidence
 */

import { getConfig, getHealth, postRag } from "../api/client";
import type { RagHit } from "../api/types";
import {
  DEMO_ACTIONS,
  DEMO_EVIDENCE,
  DEMO_EXECUTIVE,
} from "../mock/demoData";
import type {
  EvidenceItem,
  ExecutiveDecisionData,
  PanelLoadState,
} from "../types";

const RAG_QUERIES = [
  "VPN-503 error troubleshooting launch blocker",
  "security incident password reset policy",
  "PTO request approval process",
];

function ragHitToEvidence(hit: RagHit, index: number): EvidenceItem | null {
  if (hit.error || !hit.text) return null;
  const sourceLabel =
    hit.source?.replace(/\.md$/, "").replace(/_/g, " ") ?? "Knowledge";
  return {
    id: `rag-${hit.source}-${hit.chunk_index ?? index}`,
    source: "Knowledge",
    title: `${sourceLabel} #${hit.chunk_index ?? index + 1}`,
    snippet:
      hit.text.slice(0, 140) + (hit.text.length > 140 ? "…" : ""),
    detail: hit.text,
    severity: (hit.score ?? 0) > 0.7 ? "high" : "medium",
    origin: "live",
  };
}

function strengthFromHits(hits: RagHit[]): string {
  const scores = hits.filter((h) => h.score != null).map((h) => h.score!);
  if (scores.length === 0) return DEMO_EXECUTIVE.evidence_strength;
  const avg = scores.reduce((a, b) => a + b, 0) / scores.length;
  if (avg > 0.75) return "Strong";
  if (avg > 0.5) return "Moderate";
  return "Weak";
}

async function fetchRagHits(): Promise<RagHit[]> {
  const all: RagHit[] = [];
  for (const query of RAG_QUERIES) {
    const res = await postRag({ query, k: 2 });
    if (res?.hits) all.push(...res.hits.filter((h) => !h.error));
  }
  const seen = new Set<string>();
  return all.filter((h) => {
    const key = `${h.source}-${h.chunk_index}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function mergeEvidence(liveHits: RagHit[]): EvidenceItem[] {
  const live = liveHits
    .map((h, i) => ragHitToEvidence(h, i))
    .filter((x): x is EvidenceItem => x != null);
  const demo = DEMO_EVIDENCE.filter(
    (d) =>
      !live.some((l) =>
        l.title.toLowerCase().includes(d.source.toLowerCase())
      )
  );
  return [...live, ...demo];
}

function deriveExecutive(
  liveHits: RagHit[],
  tools: string[]
): ExecutiveDecisionData {
  const base = { ...DEMO_EXECUTIVE };
  if (liveHits.length === 0) return base;

  base.evidence_strength = strengthFromHits(liveHits);
  base.live_enriched = true;
  const liveSources = ["Knowledge Base"];
  if (tools.length)
    liveSources.push(...tools.slice(0, 2).map((t) => t.replace(/_/g, " ")));
  base.evidence_sources = [
    ...new Set([
      ...liveSources,
      ...DEMO_EXECUTIVE.evidence_sources.slice(0, 2),
    ]),
  ];
  return base;
}

export async function loadPanelData(): Promise<PanelLoadState> {
  const [health, config] = await Promise.all([getHealth(), getConfig()]);
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

  const liveHits = await fetchRagHits();
  return {
    executive: deriveExecutive(liveHits, config?.tools ?? []),
    actions: DEMO_ACTIONS,
    evidence: mergeEvidence(liveHits),
    backendReachable: true,
    modelReady,
    usingMockPanels: liveHits.length === 0,
  };
}
