#!/usr/bin/env python3
"""api_server.py — Frontend-facing HTTP/JSON API for the GB10 agent demo.

The web frontend talks ONLY to this server. It hides vLLM, the mock tool
server and the RAG index behind a small, stable REST contract, so the frontend
team can build against a fixed shape while the backend/model swaps underneath.

    Browser ──HTTP──> api_server.py (:8100) ──> agent.py
                                                  ├─ vLLM           :8000  (model, OpenAI-compatible)
                                                  ├─ mock_server.py :8088  (internal tools)
                                                  └─ faiss RAG index       (local files)

Run (after `source ~/hack/env.sh`):
    uvicorn mock_server:app --host 0.0.0.0 --port 8088   # tools  (separate terminal)
    uvicorn api_server:app  --host 0.0.0.0 --port 8100   # this API
    #   interactive docs : http://localhost:8100/docs
    #   machine schema   : http://localhost:8100/openapi.json   <-- frontend agents: generate types from this

This file is ADDITIVE: it imports agent.py and reuses its functions. It does
not modify the agent. No new dependencies (FastAPI + uvicorn ship in the venv).
"""
from __future__ import annotations

import json
import os
from typing import Any, Iterable, Optional

import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

import agent  # existing skeleton — reused, not modified

app = FastAPI(
    title="Meridian Ops Agent API",
    version="1.0.0",
    description=(
        "Frontend-facing API for the GB10 local-AI agent. Three capabilities: "
        "tool-calling chat, Text-to-SQL, and RAG. Everything runs locally on the GB10."
    ),
)

# Frontend runs on a different origin (a teammate's laptop / Vite dev server),
# so allow cross-origin calls. Fine for a local hackathon demo.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------- #
# Schemas — these ARE the frontend contract (also published at /openapi.json) #
# --------------------------------------------------------------------------- #
class ChatMessage(BaseModel):
    role: str = Field(..., description="user | assistant | tool", examples=["user"])
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., description="Full conversation so far (oldest first).")
    max_rounds: int = Field(5, description="Max tool-calling rounds before forcing an answer.")


class TraceStep(BaseModel):
    type: str = Field(..., description="tool_call | tool_result | assistant")
    name: Optional[str] = None
    args: Optional[dict[str, Any]] = None
    result: Optional[Any] = None
    content: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    trace: list[TraceStep] = Field(default_factory=list, description="Ordered steps the agent took.")


class SqlRequest(BaseModel):
    question: str = Field(..., examples=["Top 5 products by completed revenue in 2025"])
    max_rows: int = 20


class SqlResponse(BaseModel):
    sql: Optional[str] = None
    columns: Optional[list[str]] = None
    rows: Optional[list[list[Any]]] = None
    error: Optional[str] = None
    raw: Optional[str] = None


class RagRequest(BaseModel):
    query: str = Field(..., examples=["How do I fix VPN error VPN-503?"])
    k: int = 3


class RagHit(BaseModel):
    rank: Optional[int] = None
    score: Optional[float] = None
    source: Optional[str] = None
    chunk_index: Optional[int] = None
    text: Optional[str] = None
    error: Optional[str] = None


class RagResponse(BaseModel):
    hits: list[RagHit]


# --------------------------------------------------------------------------- #
# Health / config                                                             #
# --------------------------------------------------------------------------- #
def _ping(url: str) -> bool:
    try:
        return requests.get(url, timeout=2).ok
    except requests.RequestException:
        return False


@app.get("/", tags=["meta"])
def root():
    return {"service": "Meridian Ops Agent API", "docs": "/docs", "health": "/health"}


@app.get("/health", tags=["meta"])
def health():
    """Liveness + downstream status. Frontend can poll this to show a 'backend ready' badge."""
    base = agent.OPENAI_BASE_URL.rstrip("/")
    return {
        "status": "ok",
        "model_id": agent.MODEL_ID,
        "vllm": _ping(f"{base}/models"),
        "mock": _ping(f"{agent.MOCK_BASE_URL}/health"),
    }


@app.get("/api/config", tags=["meta"])
def config():
    """Static config the UI may want (model id, tool names, capabilities)."""
    return {
        "model_id": agent.MODEL_ID,
        "openai_base_url": agent.OPENAI_BASE_URL,
        "mock_base_url": agent.MOCK_BASE_URL,
        "capabilities": ["chat", "sql", "rag"],
        "tools": [t["function"]["name"] for t in agent.TOOLS],
    }


# --------------------------------------------------------------------------- #
# Text-to-SQL                                                                 #
# --------------------------------------------------------------------------- #
@app.post("/api/sql", response_model=SqlResponse, tags=["capabilities"])
def api_sql(req: SqlRequest):
    """Natural-language question -> SQL -> executed against company.db -> rows."""
    res = agent.text_to_sql(req.question, max_rows=req.max_rows)
    if isinstance(res.get("rows"), list):  # tuples -> lists so they JSON-serialize
        res["rows"] = [list(r) for r in res["rows"]]
    return res


# --------------------------------------------------------------------------- #
# RAG                                                                         #
# --------------------------------------------------------------------------- #
@app.post("/api/rag", response_model=RagResponse, tags=["capabilities"])
def api_rag(req: RagRequest):
    """Retrieve the top-k knowledge-base chunks for a query."""
    return {"hits": agent.rag_search(req.query, k=req.k)}


# --------------------------------------------------------------------------- #
# Chat — non-streaming, returns the full answer + a trace of tool steps       #
# --------------------------------------------------------------------------- #
def _run_chat(messages: list[dict], max_rounds: int) -> tuple[str, list[dict]]:
    trace: list[dict] = []
    convo: list[dict] = list(messages)
    for _ in range(max_rounds):
        resp = agent.client.chat.completions.create(
            model=agent.MODEL_ID, messages=convo, tools=agent.TOOLS,
            tool_choice="auto", max_tokens=512,
        )
        msg = resp.choices[0].message
        convo.append(msg.model_dump(exclude_none=True))

        if msg.tool_calls:  # native tool calling
            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments or "{}")
                result = agent.call_tool(tc.function.name, args)
                trace.append({"type": "tool_call", "name": tc.function.name, "args": args})
                trace.append({"type": "tool_result", "name": tc.function.name, "result": result})
                convo.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(result)})
            continue

        parsed = agent._try_parse_inline_tool(msg.content or "")  # ReAct fallback
        if parsed:
            name, args = parsed
            result = agent.call_tool(name, args)
            trace.append({"type": "tool_call", "name": name, "args": args})
            trace.append({"type": "tool_result", "name": name, "result": result})
            convo.append({"role": "user", "content": f"Tool `{name}` returned: {json.dumps(result)}"})
            continue

        answer = msg.content or ""
        trace.append({"type": "assistant", "content": answer})
        return answer, trace
    return "[exceeded tool rounds]", trace


@app.post("/api/chat", response_model=ChatResponse, tags=["capabilities"])
def api_chat(req: ChatRequest):
    """Multi-round tool-calling chat. Returns the final answer plus the tool trace."""
    answer, trace = _run_chat([m.model_dump() for m in req.messages], req.max_rounds)
    return {"answer": answer, "trace": trace}


# --------------------------------------------------------------------------- #
# Chat — Server-Sent Events stream (tokens + tool steps), for a live chat UI  #
# --------------------------------------------------------------------------- #
def _sse(event: dict) -> str:
    return f"data: {json.dumps(event)}\n\n"


def _stream_chat(messages: list[dict], max_rounds: int) -> Iterable[str]:
    """Yields SSE frames. Event shapes:
        {"type":"token","text": "..."}          incremental answer text
        {"type":"tool_call","name":..,"args":..} agent decided to call a tool
        {"type":"tool_result","name":..,"result":..}
        {"type":"error","message":..}
        {"type":"done"}
    """
    convo: list[dict] = list(messages)
    try:
        for _ in range(max_rounds):
            stream = agent.client.chat.completions.create(
                model=agent.MODEL_ID, messages=convo, tools=agent.TOOLS,
                tool_choice="auto", max_tokens=512, stream=True,
            )
            content_parts: list[str] = []
            tool_acc: dict[int, dict] = {}
            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    content_parts.append(delta.content)
                    yield _sse({"type": "token", "text": delta.content})
                if delta.tool_calls:
                    for tcd in delta.tool_calls:
                        slot = tool_acc.setdefault(tcd.index, {"id": "", "name": "", "args": ""})
                        if tcd.id:
                            slot["id"] = tcd.id
                        if tcd.function and tcd.function.name:
                            slot["name"] = tcd.function.name
                        if tcd.function and tcd.function.arguments:
                            slot["args"] += tcd.function.arguments

            if tool_acc:  # native tool calls came back -> execute and loop
                convo.append({
                    "role": "assistant",
                    "content": "".join(content_parts) or None,
                    "tool_calls": [
                        {"id": s["id"], "type": "function",
                         "function": {"name": s["name"], "arguments": s["args"]}}
                        for s in tool_acc.values()
                    ],
                })
                for s in tool_acc.values():
                    try:
                        args = json.loads(s["args"] or "{}")
                    except json.JSONDecodeError:
                        args = {}
                    yield _sse({"type": "tool_call", "name": s["name"], "args": args})
                    result = agent.call_tool(s["name"], args)
                    yield _sse({"type": "tool_result", "name": s["name"], "result": result})
                    convo.append({"role": "tool", "tool_call_id": s["id"], "content": json.dumps(result)})
                continue

            # ReAct fallback: the model wrote a tool call as JSON in its content
            parsed = agent._try_parse_inline_tool("".join(content_parts))
            if parsed:
                name, args = parsed
                yield _sse({"type": "tool_call", "name": name, "args": args})
                result = agent.call_tool(name, args)
                yield _sse({"type": "tool_result", "name": name, "result": result})
                convo.append({"role": "assistant", "content": "".join(content_parts)})
                convo.append({"role": "user", "content": f"Tool `{name}` returned: {json.dumps(result)}"})
                continue

            yield _sse({"type": "done"})
            return
        yield _sse({"type": "done"})
    except Exception as exc:  # surface to the UI instead of silently dropping the stream
        yield _sse({"type": "error", "message": f"{type(exc).__name__}: {exc}"})


@app.post("/api/chat/stream", tags=["capabilities"])
def api_chat_stream(req: ChatRequest):
    """Same as /api/chat but streams Server-Sent Events. See _stream_chat for event shapes."""
    gen = _stream_chat([m.model_dump() for m in req.messages], req.max_rounds)
    return StreamingResponse(gen, media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("API_PORT", "8100")))
