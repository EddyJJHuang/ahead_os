# Roadmap — H1 2026 (Commerce)

## Q2 (current)
- **Enterprise Checkout v2** — multi-seat + PO billing. **In flight; launch targeted 2026-06-19.** Highest priority.
- Payment reliability hardening — Amex coverage in regression suite (CHK-104), structured capture logging (PR-91).
- EU tax correctness — multi-currency VAT (CHK-103).

## Q3 (next)
- Usage-based billing for enterprise.
- Self-serve seat management portal.
- Checkout analytics dashboard for account managers.

## Dependencies & sequencing
Enterprise Checkout v2 must land cleanly before usage-based billing — billing builds on the v2 checkout primitives. A slip in v2 cascades into Q3. This is why launch *quality* matters more than hitting the exact Friday date: a 2-day delay is contained, but shipping a broken v2 would force a rollback and a multi-week reset.

## Themes
1. Move upmarket (enterprise reliability).
2. Payments trust (zero double-charge, high auth success).
3. Local-first internal operations.
