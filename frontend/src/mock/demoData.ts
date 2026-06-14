/**
 * Offline fallback ONLY. The live demo renders /api/pm/* (computed on the GB10).
 * This data is shown when the backend is unreachable, so it MUST tell the same
 * Enterprise Checkout story as the real engine (pm_agent.py + mock_data/pm_os):
 * P0 bugs CHK-101/102/103, unreviewed launch PR-88, Globex/Amex escalation,
 * no QA sign-off (TASK-2), stakeholder comms not sent (TASK-4) -> delay to 06-23.
 */

import type {
  ActionItem,
  DraftContent,
  EvidenceItem,
  ExecutiveDecisionData,
} from "../types";

export const DEMO_EXECUTIVE: ExecutiveDecisionData = {
  headline: "Enterprise Checkout launch is AT RISK",
  ship_readiness: "NO",
  recommendation: "Delay launch from 2026-06-19 to 2026-06-23",
  risk_level: "Critical",
  evidence_strength: "Strong",
  evidence_sources: ["Jira", "GitHub", "Email", "Calendar", "Tasks"],
  summary:
    "No — 2 open P0 payment bugs (CHK-101 Amex failure, CHK-102 double-charge), an unreviewed launch PR-88, and no scheduled QA sign-off mean the launch criteria are not met. Recommend slipping to 2026-06-23 and clearing the blockers.",
};

export const DEMO_ACTIONS: ActionItem[] = [
  {
    id: "act-qa",
    title: "Schedule checkout QA review",
    impact: "High",
    effort: "5 min",
    rationale: "QA sign-off is a hard launch gate and nothing is on the calendar (TASK-2).",
    draft_kind: "slack_update",
    context:
      "Ask Sarah (QA Lead) to book a full-day Enterprise Checkout QA pass before the Go/No-Go on 2026-06-18. Covers Amex, multi-currency VAT, payment retry, PO billing. Blocks TASK-2.",
  },
  {
    id: "act-pr",
    title: "Request review on PR-88",
    impact: "High",
    effort: "2 min",
    rationale: "PR-88 is the launch PR (CHK-110) and has had no review.",
    draft_kind: "slack_update",
    context:
      "Ping the requested reviewers to review PR-88 today — it blocks the Enterprise Checkout launch story.",
  },
  {
    id: "act-cust",
    title: "Reply to Globex escalation",
    impact: "High",
    effort: "5 min",
    rationale: "Churn-sensitive enterprise account escalating on the Amex failure (CHK-101).",
    draft_kind: "stakeholder_email",
    context:
      "Reply re: the Amex checkout failure (CHK-101). Acknowledge the issue, commit to a fix timeline, and reassure on the double-charge safeguard. Account: Globex.",
  },
];

export const DEMO_EVIDENCE: EvidenceItem[] = [
  {
    id: "demo-jira-101",
    source: "Jira",
    title: "CHK-101 — Amex checkout failure (HTTP 500)",
    snippet: "2 open P0 payment bug(s) block the launch",
    detail:
      "Why it matters: Amex transactions fail at checkout with a 500. Open P0.\n\nMitigation: Resolve CHK-101 before shipping; never ship payments with open P0s.",
    severity: "critical",
    origin: "demo",
  },
  {
    id: "demo-jira-102",
    source: "Jira",
    title: "CHK-102 — Double-charge on payment retry",
    snippet: "2 open P0 payment bug(s) block the launch",
    detail:
      "Why it matters: Retried payments can charge the customer twice. Open P0.\n\nMitigation: Resolve CHK-102 and verify the idempotency safeguard before shipping.",
    severity: "critical",
    origin: "demo",
  },
  {
    id: "demo-github-88",
    source: "GitHub",
    title: "PR-88 — Enterprise Checkout launch PR (unreviewed)",
    snippet: "Launch PR-88 unreviewed and blocking the launch story",
    detail:
      "Why it matters: PR-88 implements the launch story (CHK-110) and has had no review.\n\nMitigation: Request review and merge; it blocks the launch.",
    severity: "high",
    origin: "demo",
  },
  {
    id: "demo-email-globex",
    source: "Email",
    title: "EM-2001 — Globex escalation on Amex failures",
    snippet: "Escalating enterprise customer: Globex",
    detail:
      "Why it matters: Globex is a churn-sensitive enterprise account escalating on CHK-101.\n\nMitigation: Reply today tying resolution to CHK-101.",
    severity: "high",
    origin: "demo",
  },
  {
    id: "demo-calendar-gap",
    source: "Calendar",
    title: "GAP — No 'Checkout QA Review' scheduled",
    snippet: "QA sign-off cannot happen — no QA review scheduled",
    detail:
      "Why it matters: QA sign-off is a launch gate and nothing is on the calendar before the Go/No-Go.\n\nMitigation: Schedule a full-day checkout QA review before 2026-06-18.",
    severity: "high",
    origin: "demo",
  },
  {
    id: "demo-tasks-4",
    source: "Tasks",
    title: "TASK-4 — Send stakeholder launch update",
    snippet: "Stakeholder launch communication not sent",
    detail:
      "Why it matters: Stakeholder comms is a launch checklist item and not started.\n\nMitigation: Send a status update to affected accounts and internal stakeholders.",
    severity: "medium",
    origin: "demo",
  },
];

export const DEMO_DRAFTS: Record<string, DraftContent> = {
  "act-qa": {
    action_id: "act-qa",
    action_title: "Schedule checkout QA review",
    subject: "QA review needed before Go/No-Go (06-18)",
    body:
      "@sarah Can we book a full-day Enterprise Checkout QA pass before the Go/No-Go on 2026-06-18?\n\n• Scope: Amex, multi-currency VAT, payment retry, PO billing\n• Blocks: TASK-2 (QA sign-off) and the launch decision\n\n— PM",
  },
  "act-pr": {
    action_id: "act-pr",
    action_title: "Request review on PR-88",
    subject: "PR-88 needs review today",
    body:
      "Heads up — PR-88 (the Enterprise Checkout launch PR, CHK-110) has had no review and is blocking the launch story. Can a reviewer take a look today?\n\n— PM",
  },
  "act-cust": {
    action_id: "act-cust",
    action_title: "Reply to Globex escalation",
    subject: "Re: Enterprise Checkout — Amex failures",
    body:
      "Hi,\n\nThanks for flagging the Amex checkout failures. We've reproduced the issue (CHK-101) and are prioritizing a fix; I'll follow up with a firm timeline. We've also added a safeguard against double-charges on retries.\n\nWe'd rather slip the launch a couple of days than ship a payment regression — I'll keep you posted.\n\n— PM",
  },
};

export const DEMO_CHAT_OFFLINE =
  "Backend unreachable — start the API with `bash serve.sh`, then set VITE_API_URL=http://<host>:8100.";

export const DEMO_CHAT_FALLBACK: Record<string, string> = {
  "can we ship friday":
    "No — 2 P0 payment bugs are open (CHK-101 Amex failure, CHK-102 double-charge), launch PR-88 is unreviewed, and there's no QA sign-off scheduled. Recommend delaying from 2026-06-19 to 2026-06-23.",
  "what changed overnight":
    "Globex escalated again on the Amex checkout failure (CHK-101), and the launch PR-88 has still had no review. The 2 P0 payment bugs remain open with the launch this week.",
  "what is blocking launch":
    "Three blockers: (1) open P0 payment bugs CHK-101/CHK-102, (2) unreviewed launch PR-88, (3) no QA sign-off scheduled (TASK-2). Stakeholder comms (TASK-4) is also not sent.",
};

export const LOADING_TRACE = [
  "Scanning Jira",
  "Checking GitHub",
  "Matching customer emails",
  "Reviewing calendar",
  "Generating action plan",
];
