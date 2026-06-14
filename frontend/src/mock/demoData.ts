/**
 * Client-side demo data for PM OS panels.
 * TODO: POST /api/triage | POST /api/draft | GET /api/evidence
 */

import type {
  ActionItem,
  DraftContent,
  EvidenceItem,
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
    "No — 3 P1 bugs block QA sign-off, PR-88 needs security re-review, and an enterprise customer requires 48h compliance review.",
};

export const DEMO_ACTIONS: ActionItem[] = [
  {
    id: "action-1",
    title: "Schedule QA review",
    impact: "High",
    effort: "Low",
  },
  {
    id: "action-2",
    title: "Request PR-88 re-review",
    impact: "Critical",
    effort: "Medium",
  },
  {
    id: "action-3",
    title: "Send stakeholder update",
    impact: "High",
    effort: "Low",
  },
];

export const DEMO_EVIDENCE: EvidenceItem[] = [
  {
    id: "demo-jira-1",
    source: "Jira",
    title: "PROJ-442 — QA sign-off blocked",
    snippet:
      "Regression suite failed on checkout flow. 3 P1 bugs open. QA lead marked release as blocked.",
    detail:
      "Issue PROJ-442 was updated 2 hours ago by Sarah Chen (QA Lead). Status: Blocked. P1 bugs: PROJ-438, 439, 441.",
    severity: "critical",
    origin: "demo",
  },
  {
    id: "demo-github-1",
    source: "GitHub",
    title: "PR #88 — Auth refactor (changes requested)",
    snippet:
      "Security review flagged token refresh logic. Reviewer requested re-review before merge.",
    detail:
      "Pull Request #88 has changes requested from security review. Blocks hotfix PR-91.",
    severity: "critical",
    origin: "demo",
  },
  {
    id: "demo-email-1",
    source: "Email",
    title: "Re: Friday launch — Enterprise customer concern",
    snippet:
      "Acme Corp VP asking for SLA guarantee on new auth flow. Needs written confirmation.",
    detail:
      "Acme Corp needs 48 hours minimum for SOC2 compliance review before approving upgrade.",
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

export const DEMO_DRAFTS: Record<string, DraftContent> = {
  "action-1": {
    action_id: "action-1",
    action_title: "Schedule QA review",
    subject: "QA War Room — Today 2 PM",
    body:
      "Team,\n\nWe need a focused QA session today at 2 PM to triage the 3 remaining P1 bugs blocking release sign-off.\n\n— PM",
  },
  "action-2": {
    action_id: "action-2",
    action_title: "Request PR-88 re-review",
    subject: "PR-88 Security Re-Review Request",
    body:
      "@alex-kim @security-bot\n\nPR-88 needs a security re-review before we can merge.\n\n— PM",
  },
  "action-3": {
    action_id: "action-3",
    action_title: "Send stakeholder update",
    subject: "Launch Update — Revised Timeline",
    body:
      "Hi team,\n\nAfter reviewing overnight signals, we've decided to delay the launch by 2 days to ensure quality and compliance.\n\n— Product",
  },
};

export const DEMO_CHAT_OFFLINE =
  "Backend unreachable — start the API with `bash serve.sh`, then set VITE_API_URL=http://<host>:8100.";

export const DEMO_CHAT_FALLBACK: Record<string, string> = {
  "can we ship friday":
    "No — QA sign-off is blocked (3 P1 bugs), PR-88 needs security re-review, and Acme Corp requires 48h compliance review. Recommend delaying 2 days.",
  "what changed overnight":
    "Overnight: PROJ-442 marked Blocked, PR-88 received changes requested, Acme Corp emailed about SOC2, QA War Room scheduled for 2 PM.",
  "what is blocking launch":
    "Three blockers: (1) 3 P1 checkout bugs blocking QA signoff, (2) PR-88 security re-review, (3) enterprise compliance review.",
};

export const LOADING_TRACE = [
  "Scanning Jira",
  "Checking GitHub",
  "Matching customer emails",
  "Reviewing calendar",
  "Generating action plan",
];
