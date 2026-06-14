# ahead_os — GB10 Local-AI Agent (Dell × NVIDIA Hackathon)

A fully **local** autonomous business agent running on one NVIDIA GB10, with three capabilities:

- **Chat with tools** — verify an employee, open a ticket, request PTO, reset a password…
- **Text-to-SQL** — answer questions over the company database
- **RAG** — retrieve from the IT/HR knowledge base

Everything runs on-box: the model (vLLM), the tools, and the data. No cloud dependency.

---

## Who are you?

| If you are… | Start here |
|---|---|
| **Frontend dev** (or a frontend AI agent) | **[`FRONTEND.md`](FRONTEND.md)** — the API contract you build against. You only call **one** server (`:8100`). Plus [`examples/`](examples/): TypeScript types + a runnable reference UI. |
| **Backend / ops / on-site** | **[`START_HERE.md`](START_HERE.md)** → [`ON_SITE_PLAYBOOK.md`](ON_SITE_PLAYBOOK.md) → [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md). |
| **New AI agent on this repo** | Read `START_HERE.md` (ops) or `FRONTEND.md` (UI) per your task, then `CLAUDE.md` for constraints. |

---

## Architecture

```
 Frontend (web UI)  ──HTTP/JSON+SSE──▶  api_server.py  :8100   ← the frontend's ONLY dependency
                                              │ imports
                                          agent.py
                                              ├─▶ vLLM            :8000   model (OpenAI-compatible)
                                              ├─▶ mock_server.py  :8088   internal tools
                                              └─▶ faiss RAG index         knowledge base
```

The frontend never sees the model or the tools — only the stable `:8100` API. The backend
(120B ↔ 30B, vLLM ↔ llama.cpp, mock ↔ real tools) can change without touching the UI.

## Components

| File | Role |
|---|---|
| `api_server.py` | **Frontend-facing REST API** (FastAPI, `:8100`): `/api/chat`, `/api/chat/stream`, `/api/sql`, `/api/rag`. |
| `agent.py` | Core agent: `text_to_sql`, `rag_search`, `chat_with_tools` (talks to vLLM + tools). |
| `mock_server.py` | FastAPI mock of the internal tools (`:8088`). |
| `serve.sh` | Start `mock_server` + `api_server` together. |
| `dock.sh` | Docker helper: `load`, `vllm` (start the model), `logs`, `down`. |
| `healthcheck.sh` | End-to-end stack check. |
| `FRONTEND.md` / `examples/` | Frontend contract, TS types, and a dependency-free reference UI. |

## Run it (on the GB10)

```bash
cd ~/hack && source env.sh
sg docker -c 'bash ~/hack/dock.sh vllm'     # 1) start the model (:8000) — see ON_SITE_PLAYBOOK for L1-L5 fallbacks
bash serve.sh                               # 2) start tools (:8088) + frontend API (:8100)
bash healthcheck.sh                         # 3) confirm everything is green
```

Frontend teammates then point their app at `http://<GB10_LAN_IP>:8100` (find it with `hostname -I`).

## Constraints (see `CLAUDE.md`)

Don't `pip install torch/vllm/nvidia-*` (they live in the vLLM image). Don't add new Python packages
(the arm64 wheel set is fixed). Don't refactor `agent.py` — extend additively, like `api_server.py` does.

## Bundle note

Large assets (`models/`, `images/`, `wheels/`, `repos/`, `mock_data/`) are **not** in git — they come from
the offline SSD bundle and are copied to `~/hack` on-site. This repo is **code + docs + the RAG index** only.
