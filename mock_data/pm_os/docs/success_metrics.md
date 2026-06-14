# Enterprise Checkout — Success Metrics

## Launch Health Gates (first 72 hours)
- **Payment success rate ≥ 98.5%** across all card types, including Amex. Below this, treat as an incident.
- **Checkout completion rate ≥ 70%** for enterprise carts.
- **Zero double-charge events.** Any double charge is a Sev-1 and triggers rollback.
- **Checkout p95 latency < 1200ms.**

## North-Star & Business Metrics
- Enterprise checkout-attributed revenue (monthly).
- Average order value for multi-seat PO purchases.
- Reduction in sales-assisted manual orders (self-serve adoption).

## Guardrail Metrics
- Refund/chargeback rate must not increase vs. v1 baseline.
- Support ticket volume for "checkout" must not increase week-over-week post launch.

## Why Amex matters
Several of our largest accounts (e.g., Globex) pay exclusively on corporate Amex. An Amex capture failure (CHK-101) directly blocks revenue from top accounts and is therefore a launch blocker, not a cosmetic bug.
