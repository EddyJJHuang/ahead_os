# Meridian Robotics — IT Troubleshooting & Service Guide

> Owner: IT Service Desk. Version 2026.1. SLA targets are listed per category.

## Service Levels (SLA)
| Priority | Description | First response | Resolution target |
|----------|-------------|----------------|-------------------|
| P1 | Outage blocking >25 users or production | 15 min | 4 hours |
| P2 | Single user fully blocked | 1 hour | 1 business day |
| P3 | Degraded / workaround exists | 4 hours | 3 business days |
| P4 | Request / how-to | 1 business day | 5 business days |

## 1. VPN Connection Issues
Symptoms: "Authentication failed" or client hangs at "Connecting...".
1. Confirm MFA token is current; tokens expire every 30 seconds.
2. Verify you are on a supported client version (>= 7.2). Older clients fail
   silently after the 2026-01 gateway upgrade.
3. Flush DNS: `sudo dscacheutil -flushcache` (macOS) and reconnect.
4. If error code `VPN-503` appears, the regional gateway is saturated — switch to
   the secondary gateway in the client dropdown.
5. Still failing after 10 minutes: open a P2 ticket (`create_ticket`, category
   `network`).

## 2. Password Reset / Account Lockout
- Accounts lock after 6 failed attempts for 15 minutes.
- Self-service reset is available via the People Ops tool (`reset_password`).
- A reset invalidates all active sessions; you must re-enroll MFA if the device
  was wiped.
- Repeated lockouts (3+ in a day) usually indicate a stale saved credential on a
  phone mail client — remove and re-add the account.

## 3. Laptop Provisioning for New Hires
- IT ships a pre-imaged laptop to arrive on or before the start date.
- Day-1 setup: connect to corporate Wi-Fi `MeridianCorp`, sign in with the
  temporary password from the welcome email, then complete MFA enrollment.
- Full-disk encryption and endpoint protection are pre-installed; do not disable.
- Software requests beyond the standard image go through `create_ticket`
  (category `software`, priority P4).

## 4. Common Error Codes
| Code | Meaning | Fix |
|------|---------|-----|
| VPN-503 | Gateway saturated | Switch to secondary gateway |
| AUTH-119 | Expired MFA enrollment | Re-enroll MFA in the identity portal |
| MAIL-42 | Mailbox over quota | Archive or request quota increase (P4) |
| REPO-401 | Git credential expired | Regenerate token; tokens last 90 days |
| PRINT-7 | Printer offline | Power-cycle; if persists, P3 ticket |

## 5. Escalation Matrix
- Tier 1 (Service Desk) handles P3/P4 and triages everything.
- Tier 2 (Systems) handles P2 network/identity issues.
- Tier 3 (Infrastructure on-call) handles P1 outages and `security_incident`.
- Anything tagged `security_incident` is auto-escalated to Tier 3 with a 1-hour SLA.

## 6. How the Service Desk Agent Should Behave
- Always classify the request priority (P1–P4) before acting.
- For known issues, provide the documented fix first, then offer to open a ticket.
- Never reset a password or create a ticket without confirming the employee's
  identity via the `lookup_employee` tool.
