# Launch Readiness Playbook

Use this playbook to decide whether a release should launch, hold, or roll out in stages. A launch recommendation must include a decision, the top blockers, mitigations, owners, and a customer communication plan.

## Decision Levels

- Go: all P0 work is complete, launch-critical CI is passing, customer blockers are resolved, and support/docs are ready.
- Conditional go: remaining work is non-critical or can be isolated behind feature flags, and every risk has an owner, rollback, and customer-approved workaround.
- Hold: any P0 blocker is unresolved, a launch-critical PR is failing checks or has requested changes, a top customer dependency is blocked, or legal/security approval is missing for enterprise commitments.

## Minimum Evidence

Check work tracker status, pull request state, customer escalation notes, support runbooks, docs readiness, feature flag state, and rollback plans. Do not average risks together. One unresolved P0 or renewal-critical customer blocker can hold the launch.

## Recommended Output

Start with the decision. Then list launch blockers, conditional rollout candidates, customer impact, immediate next actions, and the stakeholder update. Be explicit about confidence and missing evidence.
