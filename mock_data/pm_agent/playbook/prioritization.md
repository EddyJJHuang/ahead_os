# PM Prioritization Playbook

Prioritize by customer impact, launch criticality, reversibility, confidence, and effort. P0 launch blockers outrank polish work. Enterprise renewal blockers outrank generic adoption improvements when dates are close and commitments are explicit.

## Triage Rules

1. Fix launch-critical reliability issues before documentation polish.
2. Resolve failing CI and requested changes before merging dependent infrastructure changes.
3. Prefer feature flags and staged rollout when a feature is valuable but not fully proven.
4. Escalate legal or security sign-off when enterprise commitments depend on formal evidence.

## Priority Template

For each candidate action, capture user impact, business impact, risk if delayed, owner, deadline, and dependency. The output should make tradeoffs clear enough for engineering, design, support, customer success, and executives.
