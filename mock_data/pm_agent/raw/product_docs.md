# PM Agent Product Docs

## Product

PM Agent is a local-first product management copilot that turns workspace context into executive product decisions.

It reads structured and unstructured work data such as Jira issues, GitHub pull requests, customer escalations, roadmap notes, launch criteria, and product metrics. It then produces a concise recommendation that a PM can act on.

The core demo use case is launch readiness.

---

## Demo Scenario: Checkout Launch Readiness

The PM is preparing to decide whether mobile checkout should launch on June 17, 2026.

The product team wants a direct recommendation:

```txt
SHIP READINESS: YES / NO
Confidence: %
Reason:
Recommended decision:
Evidence:
Recommended actions:
```

The agent should not simply list metrics. It should synthesize product risk, engineering status, customer impact, and launch criteria into one executive answer.

---

## Current Launch Target

- Launch name: Checkout Launch Readiness v1
- Target date: June 17, 2026
- Current date: June 14, 2026
- Product owner: Jiawen Zhang
- Engineering lead: Alex Chen
- Design lead: Maya Lee
- Customer owner: Daniel Kim
- Mentor / reviewer: Priya Shah

---

## Launch Criteria

Mobile checkout may launch only if all criteria below are met.

### Required Criteria

1. Zero open P0 launch blockers.
2. No PR linked to a P0 issue may be in Changes Requested.
3. QA review must be scheduled, accepted, and completed.
4. Enterprise pilot customers must not be blocked.
5. Payment and order creation flows must have idempotency protection.
6. Tax and promo code calculations must match final payment amount.
7. Rollback owner and rollback plan must be documented.

### Soft Criteria

1. P1 bugs may remain open only if they have a customer-safe workaround.
2. Draft PRs may remain open only if they are not linked to required launch criteria.
3. Customer communications must be drafted before launch decision is announced.

---

## Current Decision Policy

If any required criterion is not met, PM Agent should recommend:

```txt
SHIP READINESS: NO
Recommended decision: Delay launch by 2 days and unblock QA review.
```

If only soft criteria are missing, PM Agent may recommend:

```txt
SHIP READINESS: CONDITIONAL YES
Recommended decision: Launch behind feature flag with rollback owner assigned.
```

If all required criteria are met, PM Agent may recommend:

```txt
SHIP READINESS: YES
Recommended decision: Proceed with launch.
```

---

## Known Current Risks

### Risk 1: Mobile checkout remains blocked

JIRA-142 is a P0 blocker. It affects iOS Safari Apple Pay checkout. PR-88 is linked to this issue and is currently in Changes Requested.

Evidence sources:
- JIRA-142
- PR-88
- Acme escalation

### Risk 2: Idempotency is incomplete

JIRA-151 requires idempotency key support for checkout order creation. PR-92 has failing integration tests on payment timeout. Without this, duplicate order or duplicate charge risk remains.

Evidence sources:
- JIRA-151
- PR-92
- Product launch criteria

### Risk 3: Promo code tax calculation is not verified

JIRA-148 is P0 because BetaBio's launch campaign depends on WELCOME20 promo code accuracy. PR-93 is open and unit tests are failing for the California tax case.

Evidence sources:
- JIRA-148
- PR-93
- BetaBio escalation

### Risk 4: QA review is missing

JIRA-166 is a P0 task because launch requires QA sign-off. No QA reviewer has accepted the review yet.

Evidence sources:
- JIRA-166
- Launch checklist

---

## Customer Impact

### Acme Commerce

- Segment: Enterprise
- ARR at risk: $180,000
- Status: Pilot blocked
- Main blocker: Mobile checkout does not work reliably on iOS Safari
- Related Jira: JIRA-142, JIRA-151, JIRA-166, JIRA-160
- Related GitHub: PR-88, PR-92

### BetaBio Labs

- Segment: Mid-Market
- ARR at risk: $45,000
- Status: Launch campaign at risk
- Main blocker: Promo code tax calculation
- Related Jira: JIRA-148, JIRA-160
- Related GitHub: PR-93

### OmniCart

- Segment: Growth
- ARR at risk: $25,000
- Status: A/B test may be delayed
- Main blocker: Payment failure error state
- Related Jira: JIRA-167
- Related GitHub: PR-94

---

## PM Agent Output Style

The agent should produce one direct answer, not a dashboard full of cards.

Preferred format:

```txt
SHIP READINESS: NO
Confidence: 92%

Reason:
Mobile checkout remains blocked by 3 P0 issues.
An enterprise pilot cannot proceed.
QA review is not scheduled.

Recommended decision:
Delay launch 2 days and unblock QA review.

Why is launch at risk?
1. Mobile checkout broken
   Evidence:
   - JIRA-142
   - PR-88

2. Duplicate charge risk remains
   Evidence:
   - JIRA-151
   - PR-92

3. Enterprise pilot blocked
   Evidence:
   - Acme escalation

4. QA review missing
   Evidence:
   - JIRA-166

Recommended actions:
1. Assign QA owner today.
2. Fix PR-88 and PR-92 idempotency path.
3. Resolve JIRA-148 tax calculation test failure.
4. Send Acme updated pilot timeline.
```

---

## Product Metrics

PM Agent should consider these metrics when generating launch decisions:

- Open P0 count
- Open P1 count
- Number of blocked PRs
- Number of failed CI checks
- Number of customers escalated
- Revenue at risk
- Launch date proximity
- QA sign-off status
- Rollback plan status

Current expected interpretation:

- 3+ open P0 issues means launch should not proceed.
- Any failed CI check on a P0-linked PR means launch should not proceed.
- Any enterprise customer blocked by a P0 means launch should not proceed.
- Missing QA sign-off means launch should not proceed.

---

## Roadmap

### v0: Hackathon Demo

- Ingest Jira, GitHub, customers, and product docs from local files.
- Retrieve relevant context with Chroma.
- Generate launch readiness recommendation.
- Show source evidence.
- Generate recommended actions.

### v1: Workspace Connectors

- Jira API connector
- GitHub API connector
- Slack connector
- Google Calendar connector
- Customer CRM connector

### v2: PM Autopilot

- Draft launch updates.
- Create Jira follow-up tasks.
- Generate stakeholder status reports.
- Monitor changes since yesterday.
- Alert PM when launch readiness changes.

---

## Local-First Positioning

PM Agent is designed for sensitive product and customer data.

The local-first story matters because launch decisions often involve:
- Customer revenue
- Security bugs
- Unreleased roadmap
- Internal engineering status
- Executive decision context

The demo should emphasize that the product architecture can run locally and swap model/runtime layers for Dell/NVIDIA infrastructure.
