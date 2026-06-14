# Launch Decision Framework

Use this framework to produce a Go, Conditional Go, or Hold recommendation. The answer should be decisive and should cite evidence.

## Hold

Recommend Hold when any of the following are true:

- Any P0 launch blocker is open.
- Any pull request linked to a P0 blocker is in Changes Requested.
- Any launch-critical CI or end-to-end test is failing.
- A customer pilot, renewal, or executive commitment is blocked.
- QA sign-off is missing for a required launch criterion.
- Payment, billing, tax, security, or data integrity risk remains unverified.
- A rollback owner or rollback plan is missing for a risky launch.

## Conditional Go

Recommend Conditional Go only when:

- All P0 launch blockers are closed or explicitly descoped.
- Remaining P1/P2 issues have named owners and due dates.
- Risks are isolated behind feature flags, staged rollout, or clear customer opt-in.
- Rollback plan and support/customer comms are ready.
- The customer-facing promise is honest about what is enabled and what is not.

## Go

Recommend Go only when:

- Required launch criteria are met.
- Launch-critical PRs are merged or approved with passing checks.
- QA, support, docs, and customer success sign-off exist.
- Enterprise customer blockers are resolved.
- No missing evidence would change the decision.

## Output Contract

Always include:

- Decision.
- Confidence.
- Why this decision.
- Evidence.
- Customer impact.
- Top risks with score.
- Recommended actions with owner and due date.
- Stakeholder update.

If the evidence is incomplete, say what is missing and how it affects confidence.
