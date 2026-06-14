# PM Risk Scoring Playbook

Use this playbook when ranking launch risks. The goal is to explain why one issue changes the launch decision while another issue is only follow-up work.

## Score Dimensions

Score each risk from 1 to 10 using five dimensions:

- Severity: customer, revenue, compliance, payment, trust, or safety impact.
- Urgency: how close the deadline is and whether the issue blocks a scheduled launch review.
- Confidence: whether evidence is direct, current, and cited from Jira, GitHub, customers, email, Slack, calendar, or tasks.
- Reversibility: whether feature flags, rollback plans, or staged rollout can contain the risk.
- Ownership: whether a named owner and due date exist.

## Scoring Rules

- 9-10: P0 blocker, enterprise customer blocked, launch-critical PR failing, no safe rollback, or no owner.
- 7-8: P1 or critical P0 dependency with owner, but evidence or validation is incomplete.
- 4-6: Material launch risk with workaround, feature flag, or staged rollout path.
- 1-3: Non-blocking polish, documentation, or follow-up work that does not affect launch criteria.

## Required Explanation

For each top risk, include:

- Risk score.
- Severity reason.
- Urgency reason.
- Evidence IDs.
- Owner and due date.
- Mitigation or reason mitigation is insufficient.

Never average away one P0 launch blocker. One 10/10 risk can make the overall recommendation a hold.
