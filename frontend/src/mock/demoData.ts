/**
 * Client-side demo fallback when /api/pm/* is unreachable.
 */

import type {
  ActionItem,
  ActivityFeedItem,
  EvidenceItem,
  ExecutionArtifact,
  ExecutiveDecisionData,
} from "../types";

export const DEMO_EXECUTIVE: ExecutiveDecisionData = {
  headline: "Can we ship Friday?",
  ship_readiness: "NO",
  recommendation: "Delay launch 2 days",
  risk_level: "Critical",
  evidence_strength: "Strong",
  evidence_sources: ["Jira", "GitHub", "Email", "Calendar"],
  summary:
    "No — 2 open P0 payment bugs (CHK-101 Amex failure, CHK-102 double-charge), an unreviewed launch PR-88, and no scheduled QA sign-off block the launch. Recommend slipping to 2026-06-23.",
};

export const DEMO_ACTIONS: ActionItem[] = [
  {
    id: "act-qa",
    title: "Schedule Checkout QA Review",
    impact: "High",
    effort: "5 min",
    explanation:
      "QA signoff is missing from the launch criteria. Schedule a review to unblock the launch decision.",
    ctaLabel: "Generate Meeting",
    artifactType: "meeting",
    draft_kind: "slack_update",
    context:
      "Ask Sarah (QA Lead) to book a full-day Enterprise Checkout QA pass before the Go/No-Go on 2026-06-18.",
  },
  {
    id: "act-globex",
    title: "Notify Globex",
    impact: "High",
    effort: "5 min",
    explanation:
      "Globex has escalated checkout issues and represents $480K ARR. Send a proactive launch-risk update.",
    ctaLabel: "Generate Email",
    artifactType: "email",
    draft_kind: "stakeholder_email",
    context:
      "Reply to Globex re: Amex checkout failure (CHK-101). Acknowledge the issue, commit to a fix timeline, and reassure on the double-charge safeguard.",
  },
  {
    id: "act-pr88",
    title: "Request PR-88 Review",
    impact: "High",
    effort: "2 min",
    explanation:
      "PR-88 has been waiting for review and blocks checkout readiness. Ask the reviewer to prioritize it.",
    ctaLabel: "Generate Review Request",
    artifactType: "review",
    draft_kind: "slack_update",
    context:
      "Ping Alex Kim to review PR-88 ('Enterprise Checkout launch PR') today — it blocks the launch.",
  },
];

export const DEMO_EVIDENCE: EvidenceItem[] = [
  {
    id: "demo-jira-1",
    source: "Jira",
    title: "CHK-101 — Amex checkout failure (HTTP 500)",
    snippet:
      "Open P0 payment bug. Amex transactions fail at checkout with a 500 — blocks the launch.",
    detail:
      "CHK-101 is an open P0: Amex checkout returns HTTP 500. CHK-102 (double-charge on retry) is also open. Never ship payments with open P0s.",
    severity: "critical",
    origin: "demo",
  },
  {
    id: "demo-github-1",
    source: "GitHub",
    title: "PR-88 — Enterprise Checkout launch PR (unreviewed)",
    snippet:
      "The launch PR (CHK-110) has had no review and blocks the launch story.",
    detail:
      "Pull Request #88 implements the launch story (CHK-110) and is still unreviewed. Request review from Alex Kim and merge before the Go/No-Go.",
    severity: "high",
    origin: "demo",
  },
  {
    id: "demo-email-1",
    source: "Email",
    title: "EM-2001 — Globex escalation on Amex failures",
    snippet:
      "Globex (churn-sensitive enterprise, $480K ARR) escalating on the Amex failure (CHK-101).",
    detail:
      "Globex emailed about repeated Amex checkout failures tied to CHK-101. Reply today with a fix timeline; the account is churn-sensitive.",
    severity: "high",
    origin: "demo",
  },
  {
    id: "demo-calendar-1",
    source: "Calendar",
    title: "Launch Go/No-Go — Friday 10:00 AM",
    snippet:
      "Stakeholder meeting scheduled. Agenda: ship decision, risk review, comms plan.",
    detail:
      "Launch Go/No-Go Meeting — Friday 10:00 AM with VP Product, VP Eng, QA Lead.",
    severity: "medium",
    origin: "demo",
  },
  {
    id: "demo-tasks-1",
    source: "Tasks",
    title: "Update launch comms template",
    snippet:
      "Draft stakeholder email pending PM review. Blocked on ship decision.",
    detail:
      "Task blocked — waiting on ship/no-ship decision. Need both ship and delay versions.",
    severity: "low",
    origin: "demo",
  },
];

export const DEMO_ARTIFACTS: Record<string, ExecutionArtifact> = {
  "act-qa": {
    type: "meeting",
    action_id: "act-qa",
    title: "Enterprise Checkout QA Review",
    datetime: "Wed, Jun 18 · 10:00 AM – 12:00 PM PT",
    attendees: "Sarah Chen (QA Lead), Alex Kim (Eng), You",
    agenda:
      "Full checkout regression pass before Go/No-Go.\n\n• Amex payment capture (CHK-101)\n• Multi-currency VAT (CHK-103)\n• Payment retry / double-charge safeguard (CHK-102)\n• Sign-off criteria vs launch checklist",
  },
  "act-globex": {
    type: "email",
    action_id: "act-globex",
    to: "vp-ops@globex.com",
    subject: "Enterprise Checkout launch — proactive update on Amex issue",
    body:
      "Hi team,\n\nThank you for flagging the Amex checkout failures. We’ve prioritized CHK-101 and are targeting a fix ahead of our revised launch window (Jun 23).\n\nWe’re delaying the Enterprise Checkout launch by 2 days to protect payment quality and complete QA sign-off. I’ll follow up with a concrete timeline once QA review is scheduled.\n\nBest,\nNikkie",
  },
  "act-pr88": {
    type: "review",
    action_id: "act-pr88",
    target: "PR-88 · github.com/meridian/checkout#88",
    reviewer: "@alex-kim",
    message:
      "@alex-kim — PR-88 is the launch-blocking checkout PR and has been waiting 5 days for review. Can you prioritize a review today? Happy to walk through the Amex capture changes and linked Jira items (CHK-110).",
  },
  "act-pr": {
    type: "review",
    action_id: "act-pr",
    target: "PR-88 · github.com/meridian/checkout#88",
    reviewer: "@alex-kim",
    message:
      "@alex-kim — PR-88 is the launch-blocking checkout PR and has been waiting 5 days for review. Can you prioritize a review today?",
  },
  "act-cust": {
    type: "email",
    action_id: "act-cust",
    to: "vp-ops@globex.com",
    subject: "Enterprise Checkout launch — proactive update on Amex issue",
    body:
      "Hi team,\n\nThank you for escalating the Amex checkout failures. We’ve prioritized CHK-101 and are delaying launch to Jun 23 to complete QA sign-off.\n\nBest,\nNikkie",
  },
};

export const DEMO_CHAT_OFFLINE =
  "Backend unreachable — start the API with `bash serve.sh`, then set VITE_API_URL=http://<host>:8100.";

export const DEMO_CHAT_FALLBACK: Record<string, string> = {
  "can we ship friday":
    "No — 2 P0 payment bugs are open (CHK-101 Amex failure, CHK-102 double-charge), launch PR-88 is unreviewed, and no QA sign-off is scheduled. Recommend delaying from 2026-06-19 to 2026-06-23.",
  "what changed overnight":
    "Globex escalated again on the Amex checkout failure (CHK-101), and launch PR-88 still has no review. The 2 P0 payment bugs remain open with the launch this week.",
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

export const DEMO_ACTIVITY_FEED: ActivityFeedItem[] = [
  {
    id: "demo-1",
    time: "6:57 PM",
    text: "Enterprise escalation received",
    icon: "alert",
  },
  {
    id: "demo-2",
    time: "6:57 PM",
    text: "Launch risk recalculated",
    icon: "scan",
  },
  {
    id: "demo-3",
    time: "6:58 PM",
    text: "PR-88 blocker matched to Jira-142",
    icon: "link",
  },
  {
    id: "demo-4",
    time: "6:58 PM",
    text: "QA review gap detected",
    icon: "gap",
  },
  {
    id: "demo-5",
    time: "6:59 PM",
    text: "Stakeholder update drafted",
    icon: "draft",
  },
  {
    id: "demo-6",
    time: "6:59 PM",
    text: "Recommended decision updated",
    icon: "decision",
  },
];
