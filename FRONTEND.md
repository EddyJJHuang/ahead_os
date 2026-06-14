# FRONTEND.md — Local PM OS (frontend integration guide)

> **You are building the 4-panel UI.** You talk to **one HTTP API** (`api_server.py`, port **8100**)
> on the GB10 box. This is the contract — build against it. You do NOT touch the model, the GPU,
> the data files, or any Python.

Local PM OS is a **private AI chief of staff for product managers**. It converts fragmented company
context (Jira, GitHub, Email, Slack, Calendar, Tasks, Docs) into **decisions and actions** — all on-device.

---

## 0. TL;DR for your AI coding agent (read verbatim)

```
- The ONLY backend is the REST API at http://<GB10_HOST>:8100  (default http://localhost:8100).
- Build FOUR panels:
    Panel 1 Executive Decision   <- POST /api/pm/analysis  (ship_readiness + executive_summary)
    Panel 2 Top Actions          <- POST /api/pm/analysis  (.actions[]) ; "Generate Draft" -> POST /api/pm/draft
    Panel 3 Ask PM OS            <- POST /api/pm/ask  (or /api/pm/ask/stream for live tokens)
    Panel 4 Evidence Explorer    <- POST /api/pm/analysis (.risks[].evidence) + GET /api/pm/sources[/{source}]
- A single "Run PM Analysis" button calls POST /api/pm/analysis ONCE and fills Panels 1, 2 and 4.
- DO NOT call the model (:8000) or tool internals directly. Only :8100.
- DO NOT compute risk/decisions in the frontend — the backend owns all reasoning. Just render the JSON.
- The machine schema is http://<GB10_HOST>:8100/openapi.json ; types are in examples/pm_types.ts.
- A complete, dependency-free reference implementation of all 4 panels is examples/pm_os_demo.html — copy it.
- Poll GET /health for a readiness badge (vllm may be false briefly while the model loads).
```

---

## 1. Architecture (where you sit)

```
 ┌──────────────────────────┐   HTTP/JSON + SSE    ┌──────────────────┐
 │  FRONTEND (4 panels)      │ ───────────────────▶ │  api_server.py   │ :8100  ← your only dependency
 └──────────────────────────┘ ◀─────────────────── │  (FastAPI)       │
                                                    └────────┬─────────┘
                                              pm_agent.py / pm_tools.py
                                       ┌───────────────┬──────────────┴─────────────┐
                                  vLLM :8000      6 sources (jira/github/emails/      RAG over 5 KB docs
                                  (reasoning)      slack/calendar/tasks .json)        (launch_plan, strategy…)
```

Everything right of `:8100` can change (model, data, tools) without breaking your UI.

---

## 2. Endpoints

Base: `http://<GB10_HOST>:8100`. Interactive docs at `/docs`. Find the LAN IP with `hostname -I`.

### `POST /api/pm/analysis`  — Run PM Analysis (fills Panels 1, 2, 4)
No body. Runs the triage workflow (scan Jira → GitHub → email → calendar → tasks → docs → prioritize).
Response:
```json
{
  "ship_readiness": {
    "decision": "NO",                                  // "YES" | "NO"
    "recommended_action": "Delay launch from 2026-06-19 to 2026-06-23",
    "risk_level": "Critical",                           // Low | Medium | High | Critical
    "evidence_strength": "Strong",
    "based_on": ["Jira","GitHub","Email","Calendar","Tasks","Docs"],
    "target_date": "2026-06-19"
  },
  "executive_summary": {
    "headline": "Enterprise Checkout launch is AT RISK",
    "what_changed": ["Globex escalated again on the Amex failure (CHK-101).", "..."],
    "whats_blocked": ["3 open P0 bug(s): CHK-101, CHK-102, CHK-103", "..."],
    "recommended_decision": "Delay launch from 2026-06-19 to 2026-06-23",
    "narrative": "We are off track: all launch-blocking criteria are failing ..."   // LLM-generated
  },
  "criteria": [ {"name":"Zero open P0 bugs","ok":false,"detail":"3 open P0 bug(s): ...","evidence":[...]}, ... ],
  "risks": [
    {
      "risk":"3 open P0 payment bug(s) block the launch",
      "severity":"Critical",                            // Critical | High | Medium | Low
      "evidence":[ {"type":"jira","id":"CHK-101","title":"Checkout fails for Amex cards","ref":null}, ... ],
      "mitigation":"Resolve CHK-101 (Amex 500) and CHK-102 ..."
    }, ...
  ],
  "actions": [
    {
      "id":"act-qa", "title":"Schedule checkout QA review", "impact":"High", "effort":"5 min",
      "draft_kind":"slack_update",                      // feeds POST /api/pm/draft
      "rationale":"QA sign-off is a hard launch gate ...",
      "context":"Ask Sarah (QA Lead) to book ...",      // pass this as `context` to /api/pm/draft
      "evidence":[ {"type":"task","id":"TASK-2","title":"QA sign-off ...","ref":null}, ... ]
    }, ...
  ],
  "stats": {"issues":7,"prs":4,"emails":4,"events":4,"tasks":5},
  "generated_at": "2026-06-14T..."
}
```
- **Panel 1** = `ship_readiness` + `executive_summary`. Render `decision` huge (green YES / red NO), then `risk_level`, `recommended_action`, `based_on` chips, and `narrative`.
- **Panel 2** = `actions[]`. Each row: title, Impact, Effort, and a **Generate Draft** button → `POST /api/pm/draft` with `{kind: action.draft_kind, context: action.context}`.
- **Panel 4** = `risks[].evidence` (the expandable Risk → Jira → GitHub → Email chain) and `criteria[]`.

### `POST /api/pm/draft`  — Generate Draft (Panel 2 buttons)
Request: `{ "kind": "decision_memo", "context": "..." }`
`kind` ∈ `jira_comment | slack_update | decision_memo | stakeholder_email | followup_task`.
Response: `{ "kind": "decision_memo", "draft": "**Decision:** Delay ...\n\n**Why:** ..." }` (markdown text).

### `POST /api/pm/ask`  — Ask PM OS (Panel 3, non-streaming)
Request: `{ "messages": [ {"role":"user","content":"Can we ship Friday? What's blocking it?"} ] }`
Response: `{ "answer": "...", "trace": [ {"type":"tool_call","name":"search_jira","args":{...}}, {"type":"tool_result","name":"search_jira","result":[...]}, ... ] }`
Render `answer`; render `trace` as the evidence the agent pulled (also great for Panel 4).
Suggested prompts: *"Can we ship Friday?"*, *"What changed overnight?"*, *"What are the biggest risks?"*, *"Draft a stakeholder update."*, *"What is blocking launch?"*

### `POST /api/pm/ask/stream`  — Ask PM OS (SSE, recommended for the live UI)
Same body. `text/event-stream`; each frame `data: {json}\n\n`. Event `type`s:
`token`(`text`) · `tool_call`(`name`,`args`) · `tool_result`(`name`,`result`) · `error`(`message`) · `done`.
Read with `fetch` + a `ReadableStream` reader — working code is in `examples/pm_os_demo.html` (`streamAsk()`).

### `GET /api/pm/sources` and `GET /api/pm/sources/{source}`  — Evidence Explorer (Panel 4)
`GET /api/pm/sources` → `{"jira":7,"github":4,"emails":4,"slack":5,"calendar":4,"tasks":5}`.
`GET /api/pm/sources/jira` → `{ "source":"jira", "count":7, "meta":{...}, "records":[ {...}, ... ] }`.
`{source}` ∈ `jira | github | emails | slack | calendar | tasks`. Render records in a browsable table per source so a PM can click from a risk's evidence id (e.g. `CHK-101`) to the raw record.

### `GET /health`
`{ "status":"ok", "model_id":"nemotron-super", "vllm":true, "mock":true }`

---

## 3. The 4 panels (what to build)

| Panel | Purpose | Data |
|---|---|---|
| **1 — Executive Decision** | Answer "are we on track?" instantly | `analysis.ship_readiness` + `analysis.executive_summary` |
| **2 — Top Actions** | "What should I do next?" + one-click drafts | `analysis.actions[]` → `POST /api/pm/draft` |
| **3 — Ask PM OS** | NL questions, evidence-grounded | `POST /api/pm/ask/stream` |
| **4 — Evidence Explorer** | Transparency: risk → source records | `analysis.risks[].evidence` + `GET /api/pm/sources/{source}` |

A single **Run PM Analysis** button drives Panels 1/2/4. Panel 3 is independent chat.

---

## 4. Run the backend (so you have something to call)
```bash
cd ~/hack
sg docker -c 'bash ~/hack/dock.sh vllm30'   # model (:8000)  — already running in the demo env
bash serve.sh                               # tools (:8088) + API (:8100)
curl http://localhost:8100/api/pm/sources   # sanity check
```

## 5. Do / Don't
✅ Call only `:8100`. ✅ Render the backend's JSON as-is. ✅ Use `/api/pm/ask/stream` for chat. ✅ Link
evidence ids to `/api/pm/sources/{source}`. ✅ Degrade gracefully while `/health` `vllm:false`.
❌ Don't compute decisions/risks client-side. ❌ Don't call `:8000`/`:8088`. ❌ Don't hardcode the dataset —
read it from the endpoints. Need a new field/endpoint? Ask the backend owner (Eddy) — we'll add it and bump the version.
