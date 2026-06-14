# FRONTEND.md — Integration guide for the frontend team (and your AI agents)

> **You are building the web UI. You do NOT need the model, the GPU, the SSD, or any
> Python.** You talk to **one HTTP API** (`api_server.py`, port **8100**) that runs on the
> GB10 box. This document is the contract. It is stable — build against it.

---

## 0. TL;DR for your AI coding agent (read this first, verbatim)

```
- The ONLY backend you call is the REST API at http://<GB10_HOST>:8100  (default http://localhost:8100).
- DO NOT call the model (:8000) or the tool server (:8088) directly. Those are internal. Only :8100.
- DO NOT hardcode model names, prompts, SQL, or tool logic in the frontend. The backend owns all of that.
- The machine-readable contract is http://<GB10_HOST>:8100/openapi.json — generate your client/types from it.
- Three capabilities, three endpoints: POST /api/chat (+ /api/chat/stream), POST /api/sql, POST /api/rag.
- Chat is the headline. Use /api/chat/stream (Server-Sent Events) for a live, token-by-token UI and to
  render the agent's tool steps as they happen. Fall back to /api/chat (non-streaming) if SSE is a hassle.
- Poll GET /health to show a "backend / model ready" badge. vLLM may be 'false' while the model loads.
- TypeScript interfaces for every request/response are in examples/api_types.ts.
- A complete, dependency-free reference implementation is in examples/frontend_demo.html — open it to see
  exactly how to call every endpoint, including SSE parsing. Copy its fetch logic.
```

---

## 1. Architecture — where the frontend sits

```
 ┌─────────────┐   HTTP/JSON + SSE    ┌──────────────────┐
 │  FRONTEND   │ ───────────────────▶ │  api_server.py   │  :8100   ◀── YOU build the left box,
 │ (your app)  │ ◀─────────────────── │  (FastAPI)       │              you CALL the right box.
 └─────────────┘                      └────────┬─────────┘
                                               │ imports
                                      ┌────────▼─────────┐
                                      │    agent.py      │  text_to_sql / rag_search / chat_with_tools
                                      └───┬─────────┬────┘
                          OpenAI API  │   │         │  HTTP
                                ┌─────▼──┐│         │┌──────────────────┐
                                │ vLLM   ││         ││ mock_server.py   │ :8088  (lookup_employee,
                                │ :8000  │┘         │└──────────────────┘         create_ticket, request_pto…)
                                └────────┘          │
                                          ┌─────────▼────────┐
                                          │ faiss RAG index  │  (knowledge base)
                                          └──────────────────┘
```

You only ever see `:8100`. Everything to its right can change (120B → 30B model, vLLM → llama.cpp,
mock tools → real tools) **without breaking your frontend**. That decoupling is intentional.

---

## 2. Services & ports

| Port | Service | Who calls it | Your concern? |
|------|---------|--------------|---------------|
| **8100** | `api_server.py` — frontend API | **the frontend** | ✅ **yes — this is your only dependency** |
| 8088 | `mock_server.py` — internal tools | the agent | ❌ no |
| 8000 | vLLM — the model (OpenAI-compatible) | the agent | ❌ no |

Find the GB10's LAN address with `hostname -I` on the box; your app calls `http://<that-ip>:8100`.
CORS is wide open (`*`) so a Vite/Next dev server on another machine works out of the box.

---

## 3. Run the backend (so you have something to call)

On the GB10 box (one command starts both the tool server and the API):

```bash
cd ~/hack && bash serve.sh          # starts mock_server :8088 + api_server :8100
curl http://localhost:8100/health   # {"status":"ok","model_id":"nemotron-super","vllm":true,"mock":true}
```

`vllm` is `false` until the model finishes loading — that's expected; chat/sql need it, the UI does not.

---

## 4. API reference

Base URL: `http://<GB10_HOST>:8100`. All bodies are JSON. Interactive docs at `/docs`.

### `GET /health`
```json
{ "status": "ok", "model_id": "nemotron-super", "vllm": true, "mock": true }
```

### `GET /api/config`
```json
{ "model_id":"nemotron-super", "capabilities":["chat","sql","rag"],
  "tools":["lookup_employee","create_ticket","get_ticket_status","request_pto","reset_password"] }
```

### `POST /api/chat`  — multi-turn tool-calling chat (non-streaming)
Request:
```json
{ "messages": [ { "role": "user", "content": "Hi, I'm Alice (alice@meridian.com). My VPN throws VPN-503." } ] }
```
Response:
```json
{
  "answer": "Hi Alice (E1001). VPN-503 means the primary gateway is saturated. Try vpn-east.meridian.com…",
  "trace": [
    { "type": "tool_call",   "name": "lookup_employee", "args": { "email": "alice@meridian.com" } },
    { "type": "tool_result", "name": "lookup_employee", "result": { "employee_id": "E1001", "name": "Alice Nguyen" } },
    { "type": "assistant",   "content": "Hi Alice (E1001)…" }
  ]
}
```
Render `answer` as the bubble; render `trace` as collapsible "🔧 agent steps" so judges can see it work.
Keep appending the conversation: send the whole `messages` array back each turn (include prior assistant turns).

### `POST /api/chat/stream`  — same, but Server-Sent Events (use this for the live UI)
Same request body. Response is `text/event-stream`; each frame is `data: {json}\n\n`. Event types:
| `type` | fields | meaning |
|--------|--------|---------|
| `token` | `text` | append to the current assistant bubble |
| `tool_call` | `name`, `args` | show "calling `name`…" |
| `tool_result` | `name`, `result` | show the tool's return |
| `error` | `message` | show an error toast |
| `done` | — | stream finished |

`EventSource` can't POST, so read the stream with `fetch` + a `ReadableStream` reader.
**Working code is in `examples/frontend_demo.html` (`streamChat()`).** Copy it.

### `POST /api/sql`  — Text-to-SQL over the company database
Request: `{ "question": "Top 5 products by completed revenue in 2025", "max_rows": 20 }`
Response:
```json
{ "sql": "SELECT p.name, p.category, ROUND(SUM(...),2) AS revenue FROM ...",
  "columns": ["name","category","revenue"],
  "rows": [["Meridian Fleet Pro","Hardware",1250000.0], ["Meridian Insight","Software",980500.0]] }
```
On failure you get `{ "error": "...", "raw": "<model output>" }`. Render `rows`/`columns` as a table and
show `sql` in a "view query" disclosure (great for the demo).

### `POST /api/rag`  — knowledge-base retrieval
Request: `{ "query": "How do I fix VPN error VPN-503?", "k": 3 }`
Response:
```json
{ "hits": [ { "rank":1, "score":0.82, "source":"it_troubleshooting_guide.md", "chunk_index":4,
              "text":"VPN-503 = Gateway saturated; switch to the secondary gateway…" } ] }
```

---

## 5. The three demo screens to support

The judged demo is fixed (see `DEMO_SCRIPT.md`). Build the UI around these so we align:

1. **Chat (headline)** — a normal chat window using `/api/chat/stream`, showing tool steps inline.
   Seed prompt: the Alice / VPN-503 flow (identity lookup → RAG → create ticket).
2. **Ask the data (SQL)** — a question box + results table + "view SQL". Suggested chips:
   "Top 5 products by revenue (2025)", "Monthly revenue trend", "Avg CSAT by ticket priority".
3. **Knowledge search (RAG)** — a search box rendering ranked hits with source + snippet.

A single-page app with three tabs is plenty. Keep it clean; the agent does the hard part.

---

## 6. Types & client generation

- Hand-written TypeScript interfaces: **`examples/api_types.ts`** (import these directly).
- Or generate a typed client from the live schema:
  `npx openapi-typescript http://<GB10_HOST>:8100/openapi.json -o src/api.d.ts`

---

## 7. Do / Don't

✅ Call only `:8100`. ✅ Send the whole `messages` history each chat turn. ✅ Show the `trace`/tool steps.
✅ Degrade gracefully when `/health` says `vllm:false`.
❌ Don't call `:8000`/`:8088`. ❌ Don't embed prompts/SQL/model names in the UI. ❌ Don't assume a
specific model — read it from `/api/config` if you want to display it.

Questions about the contract → ping the backend owner (Eddy). If you need a new endpoint or field,
ask — we'll add it to `api_server.py` and bump the version, rather than you working around it.
