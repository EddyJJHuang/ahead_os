# ahead_os — Local PM OS

**A private AI Chief of Staff for product teams, running entirely on one NVIDIA GB10.**
Dell × NVIDIA "Local AI on Dell Pro Max with GB10" Hackathon.

Local PM OS continuously turns fragmented company context — Jira, GitHub, Email, Slack, Calendar, Tasks,
and Docs — into **prioritized decisions and actions**, on-device. It doesn't help you *search*; it answers
**"Are we on track? What changed? What's at risk? What should I do next?"**

---

## Who are you?

| If you are… | Start here |
|---|---|
| **Frontend dev** (or a frontend AI agent) | **[`FRONTEND.md`](FRONTEND.md)** — the 4-panel API contract. You call **one** server (`:8100`). Plus [`examples/pm_types.ts`](examples/pm_types.ts) and the runnable reference **[`examples/pm_os_demo.html`](examples/pm_os_demo.html)**. |
| **Backend / ops / on-site** | [`START_HERE.md`](START_HERE.md) → [`ON_SITE_PLAYBOOK.md`](ON_SITE_PLAYBOOK.md) for the GB10 deploy + degrade ladder. |

## The product — 4 panels

| Panel | Question it answers | Endpoint |
|---|---|---|
| **① Executive Decision** | Are we on track? Ship or not? | `POST /api/pm/analysis` |
| **② Top Actions** | What should I do next? (one-click drafts) | `POST /api/pm/analysis` → `POST /api/pm/draft` |
| **③ Ask PM OS** | Natural-language Q&A, evidence-grounded | `POST /api/pm/ask` / `…/stream` |
| **④ Evidence Explorer** | Why? (risk → Jira → PR → email chain) | `POST /api/pm/analysis` + `GET /api/pm/sources/{source}` |

## Architecture

```
 Frontend (4 panels) ──HTTP/JSON+SSE──▶ api_server.py :8100   ← frontend's only dependency
                                              │
                                  pm_agent.py (triage) + pm_tools.py (search_*/generate_*)
                                              ├─▶ vLLM :8000   reasoning (Nemotron, OpenAI-compatible)
                                              ├─▶ 6 sources    mock_data/pm_os/*.json
                                              └─▶ faiss RAG    mock_data/pm_os/docs/*.md
```

The frontend never sees the model or the data — only the stable `:8100` contract. The model/data/tools can
change underneath without breaking the UI.

## Components

| File | Role |
|---|---|
| `api_server.py` | Frontend API (`:8100`): `/api/pm/analysis`, `/api/pm/ask[/stream]`, `/api/pm/draft`, `/api/pm/sources`. |
| `pm_agent.py` | PM triage agent: `run_analysis` (deterministic facts + LLM narrative), `ask` (evidence-grounded chat), `generate_draft`. |
| `pm_tools.py` | `search_jira/github/email/calendar/tasks` + RAG `search_docs`; `generate_*` drafts. |
| `mock_data/pm_os/` | 6 structured sources + 5 KB docs (the Enterprise Checkout launch scenario). |
| `agent.py` | Lower-level vLLM client + bge embedder (reused by the PM modules; unmodified). |
| `serve.sh` / `dock.sh` | Start tools+API / manage the vLLM container. |

## Run it (on the GB10)
```bash
cd ~/hack && source env.sh
sg docker -c 'bash ~/hack/dock.sh vllm30'   # model (:8000), 30B FP8, 16K context
bash serve.sh                               # tool server (:8088) + PM OS API (:8100)
curl http://localhost:8100/api/pm/sources   # sanity check
# open examples/pm_os_demo.html in a browser → click "Run PM Analysis"
```
Frontend teammates point their app at `http://<GB10_LAN_IP>:8100` (`hostname -I`).

## Demo scenario
**Enterprise Checkout launch** (target Fri 2026-06-19). The data encodes a launch-at-risk story: 3 open P0
payment bugs, an unreviewed launch PR (PR-88), an escalating enterprise customer (Globex / Amex), no QA review
scheduled, and an incomplete checklist. PM OS concludes **NO-GO → delay 2 days**, lists ranked actions, and
drafts the stakeholder comms — grounded in cross-linked evidence.

## Constraints (see `CLAUDE.md`)
Don't `pip install torch/vllm/nvidia-*` (they're in the vLLM image). Don't add new Python packages (the arm64
wheel set is fixed). Extend additively (PM OS is built on top of `agent.py`, not by refactoring it). Large
assets (`models/`, `images/`, `wheels/`) are not in git — they come from the SSD bundle.
