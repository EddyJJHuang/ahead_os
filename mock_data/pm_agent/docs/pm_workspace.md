# Generated PM Workspace Snapshot

Generated from `mock_data/pm_agent/raw/` for local PM launch-readiness retrieval.

## Calender

- Item 1: id: cal_001; type: calendar_event; title: Dell x NVIDIA Hackathon Architecture Review; start: 2026-06-12T16:00:00; end: 2026-06-12T16:30:00; attendees: jiawen | alex | maya | priya; description: Review BriefOS architecture and identify which layers can be swapped to Nemotron, OpenClaw, and OpenShell during the hackathon.; project: BriefOS; tags: architecture | hackathon | nvidia | dell
- Item 2: id: cal_002; type: calendar_event; title: Demo Dry Run; start: 2026-06-12T19:00:00; end: 2026-06-12T19:45:00; attendees: jiawen | alex | maya; description: Run the 90-second demo flow: daily brief, meeting prep, ask a decision question, generate follow-up draft.; project: BriefOS; tags: demo | dry-run | pitch

## Customers

- accounts: id: cust_acme; name: Acme Commerce; segment: Enterprise; arr: 180000; stage: Pilot; health: At Risk; owner: Daniel Kim; contract_deadline: 2026-06-20; primary_contact: name: Rachel Morgan; title: VP Operations; email: rachel.morgan@acmecommerce.example; use_case: Acme wants to roll out mobile checkout to 40 regional storefronts after pilot approval.; success_criteria: Mobile checkout works on iOS Safari | No duplicate charge risk | QA sign-off shared before pilot start; linked_jira: JIRA-142 | JIRA-151 | JIRA-160 | JIRA-166; linked_prs: PR-88 | PR-92; urgency: Critical; revenue_at_risk: 180000 | id: cust_beta_bio; name: BetaBio Labs; segment: Mid-Market; arr: 45000; stage: Launch Campaign; health: Caution; owner: Jiawen Zhang; contract_deadline: 2026-06-24; primary_contact: name: Nina Patel; title: Growth Lead; email: nina.patel@betabio.example; use_case: BetaBio plans to launch a WELCOME20 promo campaign tied to checkout release.; success_criteria: Promo code WELCOME20 calculates correct subtotal and tax | Order summary matches payment amount | Customer support macro ready for launch; linked_jira: JIRA-148 | JIRA-160; linked_prs: PR-93; urgency: High; revenue_at_risk: 45000 | id: cust_omnicart; name: OmniCart; segment: Growth; arr: 25000; stage: A/B Test; health: Caution; owner: Maya Lee; contract_deadline: 2026-06-28; primary_contact: name: Leo Grant; title: Product Manager; email: leo.grant@omnicart.example; use_case: OmniCart wants to run a mobile checkout conversion A/B test after launch.; success_criteria: Recoverable payment failure state | Clean funnel analytics | Mobile web conversion tracking enabled; linked_jira: JIRA-142 | JIRA-167; linked_prs: PR-88 | PR-94; urgency: Medium; revenue_at_risk: 25000 | id: cust_northstar; name: Northstar Retail; segment: Enterprise; arr: 120000; stage: Discovery; health: Healthy; owner: Daniel Kim; contract_deadline: 2026-07-15; primary_contact: name: Erin Cho; title: Director of Digital; email: erin.cho@northstar.example; use_case: Interested in PM Agent's launch readiness summaries for internal product teams.; success_criteria: Demo can show launch risk across Jira, GitHub, and customer impact | Agent cites evidence | Local-first deployment story is clear; linked_jira: JIRA-173; linked_prs: PR-85; urgency: Low; revenue_at_risk: 0
- escalations: id: esc_001; customer_id: cust_acme; timestamp: 2026-06-14T07:30:00-07:00; source: customer_email; severity: Critical; subject: Acme pilot cannot proceed until mobile checkout is stable; body: We cannot approve the enterprise pilot while iOS checkout is failing and there is still duplicate charge risk. Please send a clear launch decision and QA sign-off by Tuesday morning.; linked_jira: JIRA-142 | JIRA-151 | JIRA-166 | JIRA-160; linked_prs: PR-88 | PR-92; requested_action: Delay launch or provide verified fix and QA sign-off.; business_impact: Blocks $180K enterprise pilot. | id: esc_002; customer_id: cust_beta_bio; timestamp: 2026-06-13T16:05:00-07:00; source: slack_connect; severity: High; subject: Promo campaign depends on correct tax calculation; body: Our WELCOME20 launch campaign is scheduled for next week. We need confirmation that discounts and tax calculations are correct before enabling checkout traffic.; linked_jira: JIRA-148 | JIRA-160; linked_prs: PR-93; requested_action: Confirm tax calculation fix and share test evidence.; business_impact: Risks $45K launch campaign. | id: esc_003; customer_id: cust_omnicart; timestamp: 2026-06-13T11:45:00-07:00; source: customer_call; severity: Medium; subject: Mobile checkout A/B test needs reliable error states; body: If failed payments show a spinner forever, conversion data will be noisy. This is not a launch blocker for us, but we need a timeline.; linked_jira: JIRA-167; linked_prs: PR-94; requested_action: Share ETA for recoverable payment failure state.; business_impact: May delay $25K A/B test.
- customer_impact_summary: total_revenue_at_risk: 250000; critical_accounts: Acme Commerce; highest_urgency_issue: JIRA-142; recommended_customer_message: We recommend delaying checkout launch by 2 days to complete P0 fixes and QA sign-off. We will provide Acme with a verified fix status and updated pilot timeline by Tuesday morning.

## Emails

- Item 1: id: email_001; type: email; timestamp: 2026-06-12T09:15:00; from: priya@dellnvidia.dev; to: jiawen@novaworks.ai; subject: Hackathon environment and agent runtime notes; body: For the Dell x NVIDIA hackathon, teams will have access to the provided agent environment. You do not need to install OpenClaw or NemoClaw before arrival. Focus on building a modular product architecture where the model layer, agent runtime, and tool execution layer can be swapped during the hackathon.; project: BriefOS; tags: dell | nvidia | openclaw | nemotron | openshell; importance: high
- Item 2: id: email_002; type: email; timestamp: 2026-06-12T10:40:00; from: alex@novaworks.ai; to: jiawen@novaworks.ai; subject: Chroma ingestion status; body: I finished the first version of the ingestion script for emails, Slack messages, tasks, and notes. The current blocker is that meeting prep sometimes retrieves unrelated task items. We may need better metadata filters by project, date, and participant.; project: BriefOS; tags: chroma | retrieval | backend | blocker; importance: medium
- Item 3: id: email_003; type: email; timestamp: 2026-06-12T13:20:00; from: daniel@arcstudio.ai; to: jiawen@novaworks.ai; subject: Use case feedback: local chief of staff; body: The most compelling part of BriefOS is that it can summarize sensitive workspace context locally. For founders, the value is not another chatbot, but a system that remembers investor conversations, customer asks, calendar context, and open follow-ups.; project: BriefOS; tags: customer-feedback | privacy | local-ai | chief-of-staff; importance: high

## Github

- repository: name: novaworks/pm-agent; default_branch: main; current_release_branch: release/checkout-readiness-v1
- pull_requests: id: PR-88; number: 88; title: Fix mobile checkout Apple Pay return state and add idempotency key; status: Changes Requested; branch: fix/mobile-apple-pay-idempotency; author: Alex Chen; created_at: 2026-06-12T16:45:00-07:00; updated_at: 2026-06-14T10:25:00-07:00; linked_jira: JIRA-142 | JIRA-151; reviewers: name: Priya Shah; state: changes_requested | name: Maya Lee; state: commented; checks: name: unit-tests; status: passed | name: integration-tests; status: failed; details: idempotency retry test fails on timeout path | name: lint; status: passed | name: mobile-e2e; status: failed; details: iOS Safari checkout submit remains disabled in 1/5 runs; files_changed: apps/web/components/checkout/SubmitButton.tsx | apps/web/hooks/useApplePayReturn.ts | backend/api/checkout.py | backend/services/idempotency.py | backend/tests/test_checkout_idempotency.py; summary: Attempts to fix Apple Pay return state and add idempotency key support. Still blocked by failing integration tests and reviewer concerns.; risk: high; merge_blocked_reason: Integration test failure and changes requested by Priya on retry semantics.; comments: author: Priya Shah; timestamp: 2026-06-14T09:40:00-07:00; body: The endpoint should return the existing order when the same idempotency key is reused after timeout. Current implementation may create a second pending order. | author: Maya Lee; timestamp: 2026-06-14T10:02:00-07:00; body: UI state reset looks better, but e2e still flakes on iOS Safari.; commits: c7a91f2 | e4b2a19 | a19c3d0 | id: PR-93; number: 93; title: Correct tax calculation for discounted checkout totals; status: Open; branch: fix/discount-tax-calculation; author: Priya Shah; created_at: 2026-06-13T13:10:00-07:00; updated_at: 2026-06-14T08:55:00-07:00; linked_jira: JIRA-148; reviewers: name: Daniel Kim; state: approved | name: Alex Chen; state: pending; checks: name: unit-tests; status: failed; details: CA percentage promo tax case failing | name: integration-tests; status: pending | name: lint; status: passed; files_changed: backend/services/pricing.py | backend/services/tax.py | backend/tests/test_discount_tax.py; summary: Updates pricing pipeline so tax uses discounted subtotal. Unit test still failing for CA percentage discount case.; risk: medium; merge_blocked_reason: Unit test failure and one pending reviewer.; comments: author: Daniel Kim; timestamp: 2026-06-13T17:20:00-07:00; body: Logic is directionally right. Please fix CA promo case before merge.; commits: f4d2c08 | 19bc0a3 | id: PR-94; number: 94; title: Add recoverable error state for failed payment intent; status: Draft; branch: ui/failed-payment-error-state; author: Maya Lee; created_at: 2026-06-13T18:14:00-07:00; updated_at: 2026-06-14T09:05:00-07:00; linked_jira: JIRA-167; reviewers: ; checks: name: unit-tests; status: pending | name: storybook; status: passed; files_changed: apps/web/components/checkout/PaymentErrorState.tsx | apps/web/components/checkout/CheckoutPage.tsx; summary: Adds visible retry state when payment intent fails. Not a hard launch blocker if P0s are resolved.; risk: low; merge_blocked_reason: Draft PR; needs tests before review.; comments: ; commits: 72ac8f0 | id: PR-85; number: 85; title: Generate PM launch readiness brief from local workspace memory; status: Merged; branch: feature/launch-brief; author: Jiawen Zhang; created_at: 2026-06-11T12:12:00-07:00; updated_at: 2026-06-13T21:00:00-07:00; merged_at: 2026-06-13T21:00:00-07:00; linked_jira: JIRA-173; reviewers: name: Alex Chen; state: approved | name: Maya Lee; state: approved; checks: name: unit-tests; status: passed | name: rag-smoke-test; status: passed | name: lint; status: passed; files_changed: backend/brief_agent.py | backend/retriever.py | apps/web/components/LaunchBrief.tsx; summary: Core demo feature. Generates decision, confidence, reasons, evidence, and recommended actions from Jira/GitHub/customer/docs context.; risk: low; merge_blocked_reason: None; comments: author: Priya Shah; timestamp: 2026-06-13T20:43:00-07:00; body: This is the main demo. Make the output feel like an executive decision, not a search result.; commits: 8f2db10 | 94bb25e | 0bd7a11 | id: PR-81; number: 81; title: Ingest Jira, GitHub, customers, and product docs into Chroma; status: Merged; branch: feature/workspace-ingestion; author: Alex Chen; created_at: 2026-06-10T09:30:00-07:00; updated_at: 2026-06-12T18:00:00-07:00; merged_at: 2026-06-12T18:00:00-07:00; linked_jira: JIRA-173; reviewers: name: Jiawen Zhang; state: approved; checks: name: unit-tests; status: passed | name: embedding-smoke-test; status: passed | name: lint; status: passed; files_changed: backend/ingest.py | backend/memory.py | backend/schemas.py; summary: Adds local ingestion pipeline for fake workspace data. Supports metadata filters by project, source, priority, customer, Jira key, and PR id.; risk: low; merge_blocked_reason: None; comments: ; commits: d41e9b2 | 52ca710 | id: PR-92; number: 92; title: Backend idempotency service for order creation; status: Open; branch: backend/idempotency-service; author: Alex Chen; created_at: 2026-06-13T08:40:00-07:00; updated_at: 2026-06-14T09:44:00-07:00; linked_jira: JIRA-151; reviewers: name: Priya Shah; state: changes_requested; checks: name: unit-tests; status: passed | name: integration-tests; status: failed; details: duplicate idempotency key with payment timeout returns 500; files_changed: backend/services/idempotency.py | backend/db/migrations/20260613_idempotency_keys.sql | backend/tests/test_idempotency.py; summary: Adds idempotency persistence but still fails payment timeout path.; risk: high; merge_blocked_reason: Integration test failure and reviewer changes requested.; comments: author: Priya Shah; timestamp: 2026-06-14T09:48:00-07:00; body: This blocks PR-88 and the launch readiness decision.; commits: a19c3d0
- commits: sha: c7a91f2; message: Reset checkout submit state after Apple Pay return; author: Alex Chen; timestamp: 2026-06-12T17:05:00-07:00; linked_pr: PR-88; linked_jira: JIRA-142; files: apps/web/hooks/useApplePayReturn.ts | sha: e4b2a19; message: Add mobile checkout e2e coverage for wallet return; author: Alex Chen; timestamp: 2026-06-13T09:20:00-07:00; linked_pr: PR-88; linked_jira: JIRA-142; files: apps/web/tests/mobile_checkout.spec.ts | sha: a19c3d0; message: Persist idempotency keys for checkout order creation; author: Alex Chen; timestamp: 2026-06-13T11:15:00-07:00; linked_pr: PR-92; linked_jira: JIRA-151; files: backend/services/idempotency.py | backend/db/migrations/20260613_idempotency_keys.sql | sha: f4d2c08; message: Apply promo discount before tax calculation; author: Priya Shah; timestamp: 2026-06-13T13:42:00-07:00; linked_pr: PR-93; linked_jira: JIRA-148; files: backend/services/pricing.py | backend/services/tax.py | sha: 19bc0a3; message: Add tax regression tests for fixed amount promo code; author: Priya Shah; timestamp: 2026-06-13T14:18:00-07:00; linked_pr: PR-93; linked_jira: JIRA-148; files: backend/tests/test_discount_tax.py | sha: 8f2db10; message: Generate launch readiness brief with source evidence; author: Jiawen Zhang; timestamp: 2026-06-12T20:15:00-07:00; linked_pr: PR-85; linked_jira: JIRA-173; files: backend/brief_agent.py | sha: 94bb25e; message: Render executive launch recommendation in dashboard; author: Jiawen Zhang; timestamp: 2026-06-13T16:44:00-07:00; linked_pr: PR-85; linked_jira: JIRA-173; files: apps/web/components/LaunchBrief.tsx | sha: 72ac8f0; message: Add payment failure retry UI state; author: Maya Lee; timestamp: 2026-06-14T08:52:00-07:00; linked_pr: PR-94; linked_jira: JIRA-167; files: apps/web/components/checkout/PaymentErrorState.tsx

## Jira

- project: name: PM Agent; product_area: AI product management copilot; release: Checkout Launch Readiness v1; launch_date_target: 2026-06-17; current_date: 2026-06-14; timezone: America/Los_Angeles
- issues: id: jira_142; key: JIRA-142; type: Bug; title: Mobile checkout submit button freezes after Apple Pay authorization; status: In Progress; priority: P0; severity: Blocker; component: mobile-checkout; assignee: Alex Chen; reporter: Maya Lee; created_at: 2026-06-12T09:18:00-07:00; updated_at: 2026-06-14T10:34:00-07:00; due_date: 2026-06-14; sprint: Launch Sprint 24; labels: checkout-launch | mobile | apple-pay | release-blocker; description: On iOS Safari, the checkout submit button becomes unresponsive after Apple Pay authorization returns to the checkout page. User sees no confirmation and may retry payment.; repro_steps: Open checkout on iOS Safari | Select Apple Pay | Authorize payment | Return to checkout screen | Tap Submit Order; expected_behavior: Submit Order triggers order creation within 2 seconds and navigates to confirmation page.; actual_behavior: Submit Order button remains disabled. No order is created. No error is shown.; acceptance_criteria: iOS Safari Apple Pay checkout succeeds in staging | Button state resets correctly after wallet authorization | Order creation idempotency prevents duplicate charge attempts | QA signs off on iPhone 14, iPhone 15, and iPhone SE test matrix; linked_prs: PR-88; linked_commits: c7a91f2 | e4b2a19; blocked_by: JIRA-151; blocks: JIRA-160 | JIRA-167; customer_impact: customer_id: cust_acme; impact: Enterprise pilot blocked | customer_id: cust_omnicart; impact: Mobile conversion test cannot start; business_impact: estimated_revenue_at_risk: 180000; impact_window: This week; risk_note: Acme cannot start enterprise pilot until mobile checkout works on iOS.; launch_criteria_blocker: True; evidence: Sentry event checkout.mobile.applepay.button_frozen increased from 0 to 47 events in staging | QA video uploaded by Maya on 2026-06-13 | PR-88 still in Changes Requested; comments: author: Maya Lee; timestamp: 2026-06-13T15:42:00-07:00; body: Reproduced on iPhone 15 Pro and iPhone SE. This should block launch. | author: Alex Chen; timestamp: 2026-06-14T09:21:00-07:00; body: Fix is in PR-88, but review found idempotency edge case when users double-tap after wallet return. | id: jira_148; key: JIRA-148; type: Bug; title: Promo code discount not reflected in final tax calculation; status: To Do; priority: P0; severity: Critical; component: pricing; assignee: Priya Shah; reporter: Daniel Kim; created_at: 2026-06-12T11:04:00-07:00; updated_at: 2026-06-14T08:02:00-07:00; due_date: 2026-06-15; sprint: Launch Sprint 24; labels: checkout-launch | pricing | tax | release-blocker; description: When a user applies a percentage promo code, the displayed subtotal updates but tax calculation still uses the pre-discount subtotal.; acceptance_criteria: Tax calculation uses discounted subtotal | Order summary and payment intent amount match | Regression test added for percentage and fixed promo codes; linked_prs: PR-93; linked_commits: ; blocked_by: ; blocks: JIRA-160; customer_impact: customer_id: cust_beta_bio; impact: Launch campaign uses promo code WELCOME20; business_impact: estimated_revenue_at_risk: 45000; impact_window: Launch week; risk_note: Incorrect tax could trigger support tickets and refund requests.; launch_criteria_blocker: True; evidence: Unit test added in PR-93 fails for CA tax case | Customer launch campaign depends on promo code; comments: author: Daniel Kim; timestamp: 2026-06-13T12:35:00-07:00; body: This is a compliance and customer trust issue. Please keep P0. | id: jira_151; key: JIRA-151; type: Task; title: Add idempotency key to checkout order creation endpoint; status: Changes Requested; priority: P0; severity: Critical; component: checkout-api; assignee: Alex Chen; reporter: Jiawen Zhang; created_at: 2026-06-12T14:18:00-07:00; updated_at: 2026-06-14T10:11:00-07:00; due_date: 2026-06-14; sprint: Launch Sprint 24; labels: checkout-launch | backend | idempotency | release-blocker; description: Order creation endpoint needs idempotency support before mobile checkout can be released. Required to prevent duplicate orders or duplicate payment captures when users retry.; acceptance_criteria: Client sends idempotency_key for each checkout attempt | Server returns previous order for duplicate idempotency_key | Payment provider capture is not retried for completed order | Integration tests cover retry and timeout scenarios; linked_prs: PR-88 | PR-92; linked_commits: a19c3d0; blocked_by: ; blocks: JIRA-142; customer_impact: customer_id: cust_acme; impact: Required for enterprise pilot risk approval; business_impact: estimated_revenue_at_risk: 180000; impact_window: This week; risk_note: Without idempotency, checkout launch violates launch criteria.; launch_criteria_blocker: True; evidence: PR-88 code review requested changes on idempotency behavior | Product docs require zero duplicate charge risk for launch; comments: author: Priya Shah; timestamp: 2026-06-14T09:56:00-07:00; body: Do not ship mobile checkout until this is merged and QA verified. | id: jira_160; key: JIRA-160; type: Release; title: Checkout Launch Readiness decision; status: Blocked; priority: P0; severity: Blocker; component: release; assignee: Jiawen Zhang; reporter: Priya Shah; created_at: 2026-06-13T08:00:00-07:00; updated_at: 2026-06-14T10:46:00-07:00; due_date: 2026-06-14; sprint: Launch Sprint 24; labels: checkout-launch | release-decision | exec-brief; description: PM needs to make final launch readiness recommendation for mobile checkout.; acceptance_criteria: All P0 issues closed | QA review scheduled and completed | Enterprise pilot account unblocked | Launch checklist completed | Rollback owner assigned; linked_prs: PR-88 | PR-93; linked_commits: ; blocked_by: JIRA-142 | JIRA-148 | JIRA-151 | JIRA-166; blocks: ; customer_impact: customer_id: cust_acme; impact: Pilot cannot proceed | customer_id: cust_beta_bio; impact: Launch campaign at risk; business_impact: estimated_revenue_at_risk: 225000; impact_window: Next 7 days; risk_note: Launch should be delayed 2 days unless all blockers resolve by EOD.; launch_criteria_blocker: True; evidence: 3 P0 blockers remain open | QA review missing | PR-88 in Changes Requested | Acme escalation unresolved; comments: author: Jiawen Zhang; timestamp: 2026-06-14T10:44:00-07:00; body: PM Agent should recommend launch delay unless QA review is scheduled and PR-88 is approved. | id: jira_166; key: JIRA-166; type: Task; title: Schedule QA review for mobile checkout launch; status: Blocked; priority: P0; severity: Critical; component: qa; assignee: Unassigned; reporter: Maya Lee; created_at: 2026-06-13T09:22:00-07:00; updated_at: 2026-06-14T07:48:00-07:00; due_date: 2026-06-14; sprint: Launch Sprint 24; labels: qa | launch-checklist | release-blocker; description: Final QA review is required for checkout launch but no reviewer has accepted the calendar invite.; acceptance_criteria: QA owner assigned | iOS Safari, Android Chrome, desktop Chrome test matrix completed | Regression report attached to release ticket; linked_prs: ; linked_commits: ; blocked_by: ; blocks: JIRA-160; customer_impact: customer_id: cust_acme; impact: Pilot risk review cannot be completed without QA sign-off; business_impact: estimated_revenue_at_risk: 180000; impact_window: This week; risk_note: QA sign-off is mandatory launch criterion.; launch_criteria_blocker: True; evidence: Calendar invite has no accepted QA reviewer | Launch checklist still marks QA review incomplete; comments: author: Maya Lee; timestamp: 2026-06-14T07:48:00-07:00; body: I can help test, but we need an official QA owner. | id: jira_167; key: JIRA-167; type: Bug; title: Checkout loading spinner continues after failed payment intent; status: To Do; priority: P1; severity: Major; component: checkout-ui; assignee: Maya Lee; reporter: Jiawen Zhang; created_at: 2026-06-13T10:18:00-07:00; updated_at: 2026-06-13T18:09:00-07:00; due_date: 2026-06-16; sprint: Launch Sprint 24; labels: checkout-launch | ui | error-state; description: If payment provider returns a failed intent, checkout UI sometimes keeps spinner visible instead of showing recoverable error.; acceptance_criteria: Failed payment intent shows recoverable error state | User can retry payment without refreshing page | Telemetry event emitted for failed intent; linked_prs: PR-94; linked_commits: ; blocked_by: JIRA-142; blocks: ; customer_impact: customer_id: cust_omnicart; impact: May affect A/B test quality; business_impact: estimated_revenue_at_risk: 25000; impact_window: Launch week; risk_note: Not a hard launch blocker if JIRA-142 and JIRA-151 are fixed.; launch_criteria_blocker: False; evidence: Observed 8 times in staging replay sessions; comments:  | id: jira_173; key: JIRA-173; type: Story; title: PM Agent generates launch readiness summary from Jira, GitHub, customers, and docs; status: Done; priority: P1; severity: Normal; component: pm-agent; assignee: Jiawen Zhang; reporter: Jiawen Zhang; created_at: 2026-06-10T13:00:00-07:00; updated_at: 2026-06-13T21:12:00-07:00; due_date: 2026-06-13; sprint: Hackathon Prep; labels: pm-agent | briefing | rag; description: PM Agent should combine engineering status, product criteria, and customer impact into one launch recommendation.; acceptance_criteria: Reads Jira blockers | Reads GitHub PR status | Reads customer impact | Reads launch criteria from product_docs.md | Outputs decision, confidence, reasons, and recommended actions; linked_prs: PR-81 | PR-85; linked_commits: 8f2db10 | 94bb25e; blocked_by: ; blocks: ; customer_impact: ; business_impact: estimated_revenue_at_risk: 0; impact_window: Demo; risk_note: Core hackathon demo feature.; launch_criteria_blocker: False; evidence: Local demo returns SHIP READINESS: NO for checkout launch; comments: author: Priya Shah; timestamp: 2026-06-13T20:00:00-07:00; body: This is the clearest demo moment. Keep it as one giant answer, not a dashboard of cards. | id: jira_176; key: JIRA-176; type: Task; title: Replace cloud LLM adapter with local Nemotron adapter at hackathon; status: To Do; priority: P2; severity: Normal; component: ai-runtime; assignee: Alex Chen; reporter: Jiawen Zhang; created_at: 2026-06-14T08:30:00-07:00; updated_at: 2026-06-14T08:30:00-07:00; due_date: 2026-06-15; sprint: Hackathon Prep; labels: nemotron | adapter | local-ai; description: Current LLM adapter supports Ollama/OpenAI. At hackathon, replace model implementation with local Nemotron endpoint while keeping PM Agent logic unchanged.; acceptance_criteria: LLMClient interface unchanged | Nemotron adapter passes daily brief smoke test | Fallback adapter available if local model endpoint is unavailable; linked_prs: ; linked_commits: ; blocked_by: ; blocks: ; customer_impact: ; business_impact: estimated_revenue_at_risk: 0; impact_window: Hackathon; risk_note: Sponsor integration demo point.; launch_criteria_blocker: False; evidence: Architecture isolates LLM provider behind llm/base.py; comments:

# BriefOS Product Notes

BriefOS is a local-first AI chief of staff for workspace context.

## Core idea

Most AI assistants are reactive. They wait for the user to ask a question.

BriefOS is proactive. It continuously reads workspace data such as emails, Slack messages, calendar events, tasks, and notes, then prepares daily briefings, meeting prep, and follow-up drafts.

## Why local-first matters

Workspace data is sensitive. Founders, operators, and technical teams often have confidential information in their emails, calendars, customer notes, and internal Slack messages.

BriefOS should be able to run locally so that private context does not need to leave the user's machine.

## Hackathon architecture

Current local development stack:

- Next.js frontend
- FastAPI backend
- Chroma vector database
- Ollama or OpenAI for model calls
- Local JSON and Markdown files as fake workspace data

Hackathon swap:

- Replace Ollama with Nemotron
- Replace custom agent loop with OpenClaw
- Replace local Python tool execution with OpenShell

## Demo flow

1. Generate Daily Brief
2. Open Dell x NVIDIA Architecture Review meeting
3. Generate Meeting Prep
4. Ask: "What decision do I need to make before this meeting?"
5. Generate follow-up draft

## Key message

BriefOS is not another chatbot. It is a private, local operating layer for work context.

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

## Sample Expected Brief

SHIP READINESS: NO
Confidence: 92%

Reason:
Mobile checkout remains blocked by multiple P0 issues. PR-88 is still in Changes Requested, idempotency is not verified, and QA review is not scheduled. Acme Commerce cannot proceed with its $180K enterprise pilot until the mobile checkout flow is fixed and QA signs off.

Recommended decision:
Delay launch by 2 days and unblock QA review today.

Why is launch at risk?

1. Mobile checkout broken
   Evidence:
   - JIRA-142: iOS Safari Apple Pay checkout submit button freezes
   - PR-88: Changes Requested, mobile e2e still failing

2. Duplicate charge risk remains
   Evidence:
   - JIRA-151: idempotency required before launch
   - PR-92: integration test fails on payment timeout path

3. Promo code tax calculation is not verified
   Evidence:
   - JIRA-148: P0 pricing/tax bug
   - PR-93: unit test failing for CA percentage promo case

4. Enterprise pilot blocked
   Evidence:
   - Acme escalation: pilot cannot proceed
   - $180K ARR at risk

5. QA review missing
   Evidence:
   - JIRA-166: no QA reviewer assigned
   - launch criteria require QA sign-off

Recommended actions:
1. Assign QA owner before EOD.
2. Fix PR-88 and PR-92 idempotency retry behavior.
3. Fix PR-93 tax test failure.
4. Send Acme a revised pilot timeline.
5. Re-run PM Agent readiness after P0s and QA are resolved.

## Slack

- Item 1: id: slack_001; type: slack; timestamp: 2026-06-12T08:50:00; channel: #briefos; sender: jiawen; text: Main goal today: get daily brief and meeting prep working end to end. UI can be simple, but the demo flow has to be stable.; project: BriefOS; tags: daily-brief | meeting-prep | demo
- Item 2: id: slack_002; type: slack; timestamp: 2026-06-12T11:05:00; channel: #backend; sender: alex; text: Chroma search works, but we need to chunk notes better. Right now long notes bury important action items.; project: BriefOS; tags: chroma | chunking | retrieval
- Item 3: id: slack_003; type: slack; timestamp: 2026-06-12T14:30:00; channel: #design; sender: maya; text: Dashboard v0 is ready: left sidebar for sources, center panel for daily brief, right panel for action items and follow-up draft.; project: BriefOS; tags: ui | dashboard | follow-up
- Item 4: id: slack_004; type: slack; timestamp: 2026-06-12T15:10:00; channel: #briefos; sender: jiawen; text: For the pitch, we should say: most copilots wait for questions, but BriefOS proactively prepares decisions, meetings, and follow-ups from private workspace memory.; project: BriefOS; tags: pitch | positioning | local-ai

## Tasks

- Item 1: id: task_001; type: task; title: Finish workspace data ingestion; description: Load emails, Slack messages, calendar events, tasks, and notes into Chroma with metadata.; owner: alex; status: in_progress; due: 2026-06-12T17:00:00; project: BriefOS; priority: high; tags: backend | chroma | ingestion
- Item 2: id: task_002; type: task; title: Build Daily Brief API; description: Create FastAPI endpoint that retrieves today's relevant context and generates a structured daily brief.; owner: jiawen; status: todo; due: 2026-06-12T18:00:00; project: BriefOS; priority: high; tags: fastapi | daily-brief | agent
- Item 3: id: task_003; type: task; title: Prepare 90-second pitch; description: Explain BriefOS as a local-first AI chief of staff for private workspace memory, designed to run on Dell and NVIDIA agent infrastructure.; owner: jiawen; status: todo; due: 2026-06-12T21:00:00; project: BriefOS; priority: medium; tags: pitch | dell | nvidia | local-ai
- Item 4: id: task_004; type: task; title: Polish dashboard UI; description: Create simple dashboard with daily brief, upcoming meetings, risks, and suggested follow-ups.; owner: maya; status: in_progress; due: 2026-06-12T20:00:00; project: BriefOS; priority: medium; tags: ui | nextjs | dashboard
