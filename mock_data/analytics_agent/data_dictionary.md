# Analytics Sandbox — Data Dictionary (`company.db`)

Fictional sales/ops data for **Meridian Robotics, Inc.** Use this for Text-to-SQL,
BI, or autonomous "analyst" agents. SQLite file: `company.db` (also exported as CSVs).

## Tables
- **regions**(region_id, name, country) — 5 sales regions.
- **sales_reps**(rep_id, name, region_id→regions, hire_date, quota_usd) — 10 reps.
- **customers**(customer_id, name, segment[SMB|Mid-Market|Enterprise], region_id→regions, signup_date).
- **products**(product_id, sku, name, category[Hardware|Software|Service|Accessory], unit_price).
- **orders**(order_id, customer_id→customers, rep_id→sales_reps, order_date, status[completed|refunded|pending]).
- **order_items**(order_item_id, order_id→orders, product_id→products, quantity, unit_price).
- **support_tickets**(ticket_id, customer_id→customers, opened_date, closed_date[nullable], priority, csat[1..5, nullable]).

Revenue = SUM(order_items.quantity * order_items.unit_price) for orders with
status = 'completed'.

## Suggested demo questions (good for grading a Text-to-SQL agent)
1. What was total completed revenue by product category in 2025?
2. Which sales rep is most over/under their quota this year?
3. Top 10 customers by lifetime revenue, with their segment and region.
4. Monthly revenue trend for the last 12 months (is there a Q4 bump?).
5. Average CSAT by priority; which priority has the worst satisfaction?
6. Refund rate (%) by region.
7. Which customers opened a P1 ticket within 30 days of signup?
8. Median time-to-close for support tickets, by priority.

## Example expected SQL (Q1)
```sql
SELECT p.category,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
FROM order_items oi
JOIN orders o   ON o.order_id = oi.order_id
JOIN products p ON p.product_id = oi.product_id
WHERE o.status = 'completed'
  AND strftime('%Y', o.order_date) = '2025'
GROUP BY p.category
ORDER BY revenue DESC;
```
