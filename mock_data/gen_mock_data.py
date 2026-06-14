#!/usr/bin/env python3
"""
Generates two reusable sandbox mock-data sets for a Dell x NVIDIA GB10 hackathon:

  A) ops_agent/       -> RAG + tool-calling demo (IT/HR/Ops autonomous agent)
  B) analytics_agent/ -> Text-to-SQL + data-analysis agent

All data is fictional. Deterministic (seeded) so it is reproducible.
Fictional company: "Meridian Robotics, Inc."
"""
import os, json, csv, sqlite3, random, datetime, textwrap
from pathlib import Path
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors

random.seed(42)
# Resolve mock_data dir from the script's own location, or honor an explicit MOCK_DATA_ROOT.
ROOT = os.environ.get("MOCK_DATA_ROOT") or str(Path(__file__).resolve().parent)
OPS = os.path.join(ROOT, "ops_agent")
ANA = os.path.join(ROOT, "analytics_agent")
for d in (OPS, ANA):
    os.makedirs(d, exist_ok=True)

# ----------------------------------------------------------------------------
# A) OPS AGENT  — RAG knowledge base (markdown) + tool spec (OpenAPI) + logs
# ----------------------------------------------------------------------------

EMPLOYEE_HANDBOOK_MD = """# Meridian Robotics, Inc. — Employee Handbook (FY2026)

> Internal document. Version 2026.1. Owner: People Operations. Last reviewed: 2026-01-15.

## 1. About This Handbook
This handbook summarizes the policies that apply to all full-time and part-time
employees of Meridian Robotics, Inc. ("Meridian", "the Company"). Where a policy
conflicts with a signed employment agreement, the signed agreement governs.

## 2. Working Hours & Remote Work
- Standard hours are 9:00 AM to 6:00 PM in the employee's local time zone, with a
  one-hour unpaid lunch.
- Core collaboration hours, during which all employees must be reachable, are
  10:00 AM to 3:00 PM Pacific Time.
- Employees may work remotely up to three (3) days per week. Fully remote
  arrangements require VP approval and an approved home-office stipend request.
- Hardware for remote work is provisioned by IT (see the IT Troubleshooting Guide).

## 3. Paid Time Off (PTO)
- Full-time employees accrue 1.67 PTO days per month (20 days/year).
- PTO begins accruing on the first day of employment but may not be used during
  the first 30 days without manager approval.
- Unused PTO carries over up to a maximum of 10 days into the next calendar year.
- PTO requests must be submitted at least five (5) business days in advance through
  the People Ops tool (`request_pto`). Requests of 10+ consecutive days require
  director approval.
- Sick leave is separate from PTO: 8 days/year, no advance notice required.

## 4. Expense & Reimbursement Policy
- Pre-approval is required for any single expense over USD 500.
- Reimbursable: client meals (up to USD 75/person), ground transport, economy
  airfare, conference fees, and home-office equipment up to USD 1,000/year.
- Non-reimbursable: alcohol, personal entertainment, traffic fines, first-class
  airfare.
- Receipts must be submitted within 30 days of the expense. Reimbursements are
  paid in the next payroll cycle after approval.

## 5. Information Security Policy
- All laptops must use full-disk encryption (enabled by default on IT-provisioned
  devices) and auto-lock after 5 minutes of inactivity.
- Multi-factor authentication (MFA) is mandatory for email, VPN, and the code
  repository.
- Customer data classified as "Confidential" or above must never be copied to
  personal devices or non-approved cloud storage.
- Suspected security incidents must be reported within one (1) hour to the
  Security team via the `create_ticket` tool with category `security_incident`.
- Passwords must be at least 14 characters and are rotated every 180 days.

## 6. Code of Conduct
- Meridian is an equal-opportunity employer and prohibits harassment or
  discrimination of any kind.
- Conflicts of interest must be disclosed to People Ops.
- Confidential information remains confidential for two (2) years after separation.

## 7. Benefits Summary
- Medical, dental, and vision coverage effective on the first day of employment.
- 401(k) with a 4% Company match, vesting immediately.
- Annual learning & development budget of USD 1,500 per employee.
- 12 weeks of paid parental leave for all new parents.

## 8. Escalation & Contacts
- People / HR questions: People Ops (peopleops@meridian.example).
- IT / hardware / access: IT Service Desk (see IT Troubleshooting Guide).
- Security incidents: Security on-call (1-hour SLA).
"""

IT_GUIDE_MD = """# Meridian Robotics — IT Troubleshooting & Service Guide

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
"""

PRODUCT_API_MD = """# Meridian Fleet API — Product Documentation (Public, v3)

The Meridian Fleet API lets customers manage autonomous-robot fleets programmatically.
Base URL: `https://api.meridian.example/v3`. All requests require a Bearer token.

## Authentication
Send `Authorization: Bearer <API_KEY>`. Tokens are scoped per project. Rate limit:
600 requests/minute per token; bursts return HTTP 429 with `Retry-After`.

## Resource: Robots
- `GET /robots` — list robots. Query params: `status` (idle|active|charging|fault),
  `site_id`, `page`, `page_size` (max 200).
- `GET /robots/{robot_id}` — fetch one robot, including battery %, firmware, and
  last telemetry timestamp.
- `POST /robots/{robot_id}/commands` — issue a command. Body: `{ "command":
  "recall" | "pause" | "resume", "reason": "<string>" }`.

## Resource: Tasks
- `GET /tasks` — list tasks. Filter by `state` (queued|running|done|failed).
- `POST /tasks` — create a task. Body: `{ "robot_id": "...", "type": "pick" |
  "transport" | "inspect", "payload": { ... } }`.

## Resource: Telemetry
- `GET /telemetry?robot_id=...&since=<iso8601>` — stream of telemetry points.
  Each point has `battery_pct`, `temp_c`, `error_code` (nullable), `position`.

## Error Model
Errors return `{ "error": { "code": "<machine_code>", "message": "<human text>" } }`.
Common codes: `rate_limited` (429), `not_found` (404), `invalid_command` (422),
`robot_in_fault` (409 — robot must be cleared before new commands).

## Webhooks
Register a webhook to receive `robot.fault`, `task.completed`, and `task.failed`
events. Payloads are signed with HMAC-SHA256 in the `X-Meridian-Signature` header.
"""

INTERNAL_TOOLS_OPENAPI = {
    "openapi": "3.1.0",
    "info": {
        "title": "Meridian Internal Ops Tools",
        "version": "2026.1",
        "description": "Internal tools an autonomous IT/HR support agent may call. "
                       "All endpoints are mock and run locally for the hackathon demo."
    },
    "servers": [{"url": "http://localhost:8088"}],
    "paths": {
        "/employees/lookup": {
            "get": {
                "operationId": "lookup_employee",
                "summary": "Look up an employee by email or employee_id to verify identity.",
                "parameters": [
                    {"name": "email", "in": "query", "required": False,
                     "schema": {"type": "string"}},
                    {"name": "employee_id", "in": "query", "required": False,
                     "schema": {"type": "string"}},
                ],
                "responses": {"200": {"description": "Employee record",
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Employee"}}}}}
            }
        },
        "/tickets": {
            "post": {
                "operationId": "create_ticket",
                "summary": "Create an IT/HR/security ticket.",
                "requestBody": {"required": True, "content": {"application/json": {"schema": {
                    "type": "object",
                    "required": ["requester_email", "category", "priority", "summary"],
                    "properties": {
                        "requester_email": {"type": "string"},
                        "category": {"type": "string",
                            "enum": ["network", "software", "hardware", "access",
                                     "hr", "security_incident"]},
                        "priority": {"type": "string", "enum": ["P1", "P2", "P3", "P4"]},
                        "summary": {"type": "string"},
                        "details": {"type": "string"}
                    }}}}},
                "responses": {"201": {"description": "Created ticket",
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Ticket"}}}}}
            }
        },
        "/tickets/{ticket_id}": {
            "get": {
                "operationId": "get_ticket_status",
                "summary": "Get the current status of a ticket.",
                "parameters": [{"name": "ticket_id", "in": "path", "required": True,
                                "schema": {"type": "string"}}],
                "responses": {"200": {"description": "Ticket",
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Ticket"}}}}}
            }
        },
        "/pto/request": {
            "post": {
                "operationId": "request_pto",
                "summary": "Submit a PTO request for an employee.",
                "requestBody": {"required": True, "content": {"application/json": {"schema": {
                    "type": "object",
                    "required": ["employee_id", "start_date", "end_date"],
                    "properties": {
                        "employee_id": {"type": "string"},
                        "start_date": {"type": "string", "format": "date"},
                        "end_date": {"type": "string", "format": "date"},
                        "note": {"type": "string"}
                    }}}}},
                "responses": {"201": {"description": "PTO request submitted"}}
            }
        },
        "/account/reset_password": {
            "post": {
                "operationId": "reset_password",
                "summary": "Trigger a self-service password reset (identity must be verified first).",
                "requestBody": {"required": True, "content": {"application/json": {"schema": {
                    "type": "object",
                    "required": ["employee_id"],
                    "properties": {"employee_id": {"type": "string"}}}}}},
                "responses": {"202": {"description": "Reset link issued"}}
            }
        }
    },
    "components": {
        "schemas": {
            "Employee": {
                "type": "object",
                "properties": {
                    "employee_id": {"type": "string"},
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                    "department": {"type": "string"},
                    "manager_email": {"type": "string"},
                    "pto_balance_days": {"type": "number"}
                }
            },
            "Ticket": {
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string"},
                    "status": {"type": "string",
                               "enum": ["open", "in_progress", "resolved", "closed"]},
                    "category": {"type": "string"},
                    "priority": {"type": "string"},
                    "summary": {"type": "string"},
                    "created_at": {"type": "string", "format": "date-time"}
                }
            }
        }
    }
}

# Incident / server logs the ops agent can analyze (root-cause style)
def gen_incident_logs(path):
    services = ["fleet-api", "auth-gw", "telemetry-ingest", "task-scheduler",
                "billing", "notification"]
    levels_weighted = (["INFO"] * 70) + (["WARN"] * 20) + (["ERROR"] * 8) + (["CRITICAL"] * 2)
    msgs = {
        "INFO": ["request handled", "healthcheck ok", "task dispatched",
                 "cache warmed", "token refreshed"],
        "WARN": ["latency above 800ms", "retrying upstream call",
                 "connection pool 85% used", "rate limit near threshold"],
        "ERROR": ["upstream timeout", "db connection refused",
                  "invalid command rejected", "429 from fleet-api"],
        "CRITICAL": ["service unavailable", "db primary failover",
                     "telemetry ingest backlog > 10k"],
    }
    start = datetime.datetime(2026, 6, 8, 0, 0, 0)
    rows = []
    # inject a correlated incident window: telemetry-ingest backlog -> fleet-api 429s
    for i in range(4000):
        ts = start + datetime.timedelta(seconds=i * 13)
        svc = random.choice(services)
        lvl = random.choice(levels_weighted)
        # incident window 14:00-15:00 on day 1: telemetry + fleet-api degrade
        if datetime.time(14, 0) <= ts.time() <= datetime.time(15, 0) and svc in ("telemetry-ingest", "fleet-api"):
            lvl = random.choice(["ERROR", "ERROR", "CRITICAL", "WARN"])
        msg = random.choice(msgs[lvl])
        latency = random.randint(20, 250)
        if lvl in ("ERROR", "CRITICAL"):
            latency = random.randint(800, 5000)
        rows.append([ts.isoformat(), svc, lvl, msg, latency,
                     f"req-{random.randint(100000,999999)}"])
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["timestamp", "service", "level", "message", "latency_ms", "request_id"])
        w.writerows(rows)

# write ops files
with open(os.path.join(OPS, "employee_handbook.md"), "w") as f:
    f.write(EMPLOYEE_HANDBOOK_MD)
with open(os.path.join(OPS, "it_troubleshooting_guide.md"), "w") as f:
    f.write(IT_GUIDE_MD)
with open(os.path.join(OPS, "product_api_docs.md"), "w") as f:
    f.write(PRODUCT_API_MD)
with open(os.path.join(OPS, "internal_tools_openapi.json"), "w") as f:
    json.dump(INTERNAL_TOOLS_OPENAPI, f, indent=2)
gen_incident_logs(os.path.join(OPS, "incident_logs.csv"))

# Also render the employee handbook + IT guide as a single PDF (RAG often ingests PDF)
def md_to_pdf(md_text, pdf_path, title):
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], spaceBefore=10, spaceAfter=6)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], spaceBefore=8, spaceAfter=4)
    body = ParagraphStyle("body", parent=styles["Normal"], leading=14, spaceAfter=4)
    doc = SimpleDocTemplate(pdf_path, pagesize=LETTER,
                            topMargin=0.8*inch, bottomMargin=0.8*inch,
                            leftMargin=0.9*inch, rightMargin=0.9*inch)
    story = [Paragraph(title, styles["Title"]), Spacer(1, 10)]
    for line in md_text.splitlines():
        s = line.rstrip()
        if not s:
            story.append(Spacer(1, 4)); continue
        if s.startswith("> "):
            story.append(Paragraph("<i>%s</i>" % s[2:].replace("&", "&amp;"), body)); continue
        if s.startswith("# "):
            continue  # title already shown
        if s.startswith("## "):
            story.append(Paragraph(s[3:].replace("&", "&amp;"), h1)); continue
        if s.startswith("### "):
            story.append(Paragraph(s[4:].replace("&", "&amp;"), h2)); continue
        if s.startswith("|"):
            # crude table-row -> just print as monospace-ish line
            story.append(Paragraph("<font face='Courier'>%s</font>" %
                                   s.replace("&", "&amp;").replace("<", "&lt;"), body)); continue
        if s.lstrip().startswith("- "):
            story.append(Paragraph("&bull; " + s.lstrip()[2:].replace("&", "&amp;").replace("<", "&lt;"), body)); continue
        story.append(Paragraph(s.replace("&", "&amp;").replace("<", "&lt;"), body))
    doc.build(story)

md_to_pdf(EMPLOYEE_HANDBOOK_MD, os.path.join(OPS, "employee_handbook.pdf"),
          "Meridian Robotics — Employee Handbook (FY2026)")
md_to_pdf(IT_GUIDE_MD, os.path.join(OPS, "it_troubleshooting_guide.pdf"),
          "Meridian Robotics — IT Troubleshooting Guide")

# ----------------------------------------------------------------------------
# B) ANALYTICS AGENT — SQLite database + CSV exports + data dictionary
# ----------------------------------------------------------------------------

db_path = os.path.join(ANA, "company.db")
if os.path.exists(db_path):
    os.remove(db_path)
con = sqlite3.connect(db_path)
cur = con.cursor()

cur.executescript("""
CREATE TABLE regions (
    region_id   INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    country     TEXT NOT NULL
);
CREATE TABLE sales_reps (
    rep_id      INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    region_id   INTEGER NOT NULL REFERENCES regions(region_id),
    hire_date   TEXT NOT NULL,
    quota_usd   REAL NOT NULL
);
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    segment     TEXT NOT NULL,          -- SMB / Mid-Market / Enterprise
    region_id   INTEGER NOT NULL REFERENCES regions(region_id),
    signup_date TEXT NOT NULL
);
CREATE TABLE products (
    product_id  INTEGER PRIMARY KEY,
    sku         TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    category    TEXT NOT NULL,
    unit_price  REAL NOT NULL
);
CREATE TABLE orders (
    order_id    INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    rep_id      INTEGER NOT NULL REFERENCES sales_reps(rep_id),
    order_date  TEXT NOT NULL,
    status      TEXT NOT NULL           -- completed / refunded / pending
);
CREATE TABLE order_items (
    order_item_id INTEGER PRIMARY KEY,
    order_id      INTEGER NOT NULL REFERENCES orders(order_id),
    product_id    INTEGER NOT NULL REFERENCES products(product_id),
    quantity      INTEGER NOT NULL,
    unit_price    REAL NOT NULL
);
CREATE TABLE support_tickets (
    ticket_id     INTEGER PRIMARY KEY,
    customer_id   INTEGER NOT NULL REFERENCES customers(customer_id),
    opened_date   TEXT NOT NULL,
    closed_date   TEXT,
    priority      TEXT NOT NULL,
    csat          INTEGER                -- 1..5, null if open
);
""")

regions = [
    (1, "West", "USA"), (2, "East", "USA"), (3, "Central", "USA"),
    (4, "EMEA", "UK"), (5, "APAC", "Singapore"),
]
cur.executemany("INSERT INTO regions VALUES (?,?,?)", regions)

rep_names = ["Ava Chen", "Liam Patel", "Noah Kim", "Mia Garcia", "Ethan Brooks",
             "Sofia Rossi", "Lucas Meyer", "Emma Tanaka", "Oliver Smith", "Isabella Cruz"]
reps = []
for i, nm in enumerate(rep_names, start=1):
    reps.append((i, nm, random.randint(1, 5),
                 (datetime.date(2022, 1, 1) + datetime.timedelta(days=random.randint(0, 1200))).isoformat(),
                 round(random.choice([250000, 300000, 400000, 500000]), 2)))
cur.executemany("INSERT INTO sales_reps VALUES (?,?,?,?,?)", reps)

segments = ["SMB", "Mid-Market", "Enterprise"]
cust_prefixes = ["Globex", "Initech", "Umbrella", "Soylent", "Hooli", "Vehement",
                 "Massive", "Stark", "Wayne", "Wonka", "Acme", "Cyberdyne",
                 "Tyrell", "Nakatomi", "Gekko", "Oscorp", "Pied Piper", "Aperture",
                 "Vandelay", "Bluth"]
cust_suffixes = ["Logistics", "Manufacturing", "Health", "Retail", "Foods",
                 "Energy", "Robotics", "Systems", "Labs", "Group"]
customers = []
cid = 1
for p in cust_prefixes:
    for _ in range(random.randint(3, 8)):
        customers.append((cid, f"{p} {random.choice(cust_suffixes)}",
                          random.choice(segments), random.randint(1, 5),
                          (datetime.date(2023, 1, 1) + datetime.timedelta(days=random.randint(0, 900))).isoformat()))
        cid += 1
cur.executemany("INSERT INTO customers VALUES (?,?,?,?,?)", customers)

products = [
    (1, "MRX-100", "Meridian Picker M1", "Hardware", 18000.0),
    (2, "MRX-200", "Meridian Transport T2", "Hardware", 32000.0),
    (3, "MRX-300", "Meridian Inspector I3", "Hardware", 27500.0),
    (4, "SW-FLEET", "Fleet API License (annual)", "Software", 12000.0),
    (5, "SW-INSIGHT", "Insight Analytics (annual)", "Software", 9000.0),
    (6, "SVC-PREM", "Premium Support (annual)", "Service", 15000.0),
    (7, "SVC-INSTALL", "On-site Installation", "Service", 4000.0),
    (8, "ACC-BATT", "Spare Battery Pack", "Accessory", 1200.0),
]
cur.executemany("INSERT INTO products VALUES (?,?,?,?,?)", products)

# orders + items + a realistic seasonal trend and some refunds
orders, items, oid, oiid = [], [], 1, 1
for _ in range(2500):
    c = random.choice(customers)
    r = random.randint(1, 10)
    # date weighted toward 2025 with Q4 bump
    d = datetime.date(2024, 1, 1) + datetime.timedelta(days=random.randint(0, 700))
    status = random.choices(["completed", "refunded", "pending"], weights=[88, 7, 5])[0]
    orders.append((oid, c[0], r, d.isoformat(), status))
    for _ in range(random.randint(1, 4)):
        p = random.choice(products)
        qty = random.randint(1, 5) if p[3] != "Hardware" else random.randint(1, 3)
        items.append((oiid, oid, p[0], qty, p[4]))
        oiid += 1
    oid += 1
cur.executemany("INSERT INTO orders VALUES (?,?,?,?,?)", orders)
cur.executemany("INSERT INTO order_items VALUES (?,?,?,?,?)", items)

tickets = []
tid = 1
for _ in range(1800):
    c = random.choice(customers)
    opened = datetime.date(2025, 1, 1) + datetime.timedelta(days=random.randint(0, 500))
    closed_days = random.randint(0, 20)
    is_open = random.random() < 0.12
    closed = None if is_open else (opened + datetime.timedelta(days=closed_days)).isoformat()
    csat = None if is_open else random.choices([1, 2, 3, 4, 5], weights=[5, 8, 17, 35, 35])[0]
    tickets.append((tid, c[0], opened.isoformat(), closed,
                    random.choice(["P1", "P2", "P3", "P4"]), csat))
    tid += 1
cur.executemany("INSERT INTO support_tickets VALUES (?,?,?,?,?,?)", tickets)

con.commit()

# CSV exports for each table (useful for pandas / non-SQL agents)
for tbl in ["regions", "sales_reps", "customers", "products", "orders",
            "order_items", "support_tickets"]:
    rows = cur.execute(f"SELECT * FROM {tbl}").fetchall()
    cols = [d[0] for d in cur.execute(f"SELECT * FROM {tbl} LIMIT 1").description]
    with open(os.path.join(ANA, f"{tbl}.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(cols); w.writerows(rows)

con.close()

DATA_DICT_MD = """# Analytics Sandbox — Data Dictionary (`company.db`)

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
"""
with open(os.path.join(ANA, "data_dictionary.md"), "w") as f:
    f.write(DATA_DICT_MD)

# quick sanity summary
print("OPS files:", sorted(os.listdir(OPS)))
print("ANA files:", sorted(os.listdir(ANA)))
con2 = sqlite3.connect(db_path)
for t in ["regions", "sales_reps", "customers", "products", "orders",
          "order_items", "support_tickets"]:
    n = con2.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"  {t}: {n} rows")
rev = con2.execute("""SELECT ROUND(SUM(oi.quantity*oi.unit_price),2)
                      FROM order_items oi JOIN orders o ON o.order_id=oi.order_id
                      WHERE o.status='completed'""").fetchone()[0]
print("  completed revenue total:", rev)
con2.close()
