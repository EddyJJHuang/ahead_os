#!/usr/bin/env python3
"""agent.py — Hackathon agent skeleton.

Talks to vLLM (or any OpenAI-compatible endpoint) on ``OPENAI_BASE_URL`` and
exposes three capabilities the hackathon demo needs:

* ``text_to_sql(question)``     — translate NL → SQL → run against ``company.db``
* ``rag_search(query)``         — retrieve top-k chunks from the pre-built faiss index
* ``chat_with_tools(question)`` — multi-turn with OpenAI-style tool calling,
  plus a ReAct fallback for when the vLLM tool parser doesn't fire

The model id, endpoint and SSD paths can be overridden via env vars:

    OPENAI_BASE_URL    default http://localhost:8000/v1
    OPENAI_API_KEY     default "not-needed"
    MODEL_ID           default "nemotron-super"   (must match vLLM's --served-model-name)
    SSD_ROOT           default auto-detected      (/mnt/ssd/Hackathon | /Volumes/SSD-3/Hackathon)
    MOCK_BASE_URL      default http://localhost:8088

Smoke test:    python agent.py
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any

import requests
from openai import OpenAI

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


def _detect_ssd_root() -> Path:
    """Find the SSD bundle root in a platform-aware way."""
    env = os.environ.get("SSD_ROOT")
    if env:
        return Path(env)
    for candidate in (
        Path("/mnt/ssd/Hackathon"),                # GB10 / Linux mount
        Path("/Volumes/SSD-3/Hackathon"),         # macOS mount
        Path(__file__).resolve().parent,           # next to this script
    ):
        if (candidate / "mock_data").exists():
            return candidate
    raise RuntimeError(
        "Could not locate the SSD bundle. Set SSD_ROOT env var to the directory "
        "containing mock_data/, models/, wheels/."
    )


SSD_ROOT = _detect_ssd_root()
MODEL_ID = os.environ.get("MODEL_ID", "nemotron-super")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "http://localhost:8000/v1")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "not-needed")
MOCK_BASE_URL = os.environ.get("MOCK_BASE_URL", "http://localhost:8088")

DB_PATH = SSD_ROOT / "mock_data" / "analytics_agent" / "company.db"
RAG_INDEX_PATH = SSD_ROOT / "rag_index.faiss"
RAG_CHUNKS_PATH = SSD_ROOT / "rag_chunks.json"

client = OpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY)

# ---------------------------------------------------------------------------
# Text-to-SQL
# ---------------------------------------------------------------------------

# Connect read-only so a misbehaving SQL can't damage the demo DB.
def _open_db() -> sqlite3.Connection:
    uri = f"file:{DB_PATH}?mode=ro"
    return sqlite3.connect(uri, uri=True)


SQL_SCHEMA = """
You are given a SQLite database with these tables and key columns:
- regions(region_id, name, country)
- sales_reps(rep_id, name, region_id→regions, hire_date, quota_usd)
- customers(customer_id, name, segment[SMB|Mid-Market|Enterprise], region_id→regions, signup_date)
- products(product_id, sku, name, category[Hardware|Software|Service|Accessory], unit_price)
- orders(order_id, customer_id→customers, rep_id→sales_reps, order_date, status[completed|refunded|pending])
- order_items(order_item_id, order_id→orders, product_id→products, quantity, unit_price)
- support_tickets(ticket_id, customer_id→customers, opened_date, closed_date[nullable], priority, csat[1..5,nullable])

Revenue := SUM(order_items.quantity * order_items.unit_price) WHERE orders.status='completed'.

Rules:
- Output ONLY a single SQLite SELECT or WITH statement. No prose, no commentary, no Markdown.
- Use ISO dates ('YYYY-MM-DD'). Use strftime('%Y', order_date) for year filters.
- Limit large results with LIMIT 50 unless the user asks otherwise.
"""


def _extract_sql(text: str) -> str:
    """Strip reasoning chatter (``<think>``…``</think>``) and code fences."""
    if not text:
        return ""
    # 1) ```sql ... ``` fenced block wins
    m = re.search(r"```(?:sql)?\s*(.+?)```", text, re.S | re.I)
    if m:
        return m.group(1).strip().rstrip(";")
    # 2) From the first SELECT/WITH onward
    m = re.search(r"\b(SELECT|WITH)\b.+", text, re.S | re.I)
    if m:
        return m.group(0).strip().rstrip(";")
    # 3) Last-resort cleanup
    return text.strip().strip("`").rstrip(";")


def text_to_sql(question: str, max_rows: int = 20) -> dict:
    """Translate the question into SQL, run it, return rows + the SQL used."""
    messages = [
        {"role": "system", "content": SQL_SCHEMA},
        {"role": "user", "content": question},
    ]
    resp = client.chat.completions.create(
        model=MODEL_ID, messages=messages, max_tokens=512
    )
    raw = resp.choices[0].message.content or ""
    sql = _extract_sql(raw)
    if not sql.lower().lstrip().startswith(("select", "with")):
        return {"error": "Model did not produce a SELECT/WITH statement", "raw": raw}

    with _open_db() as db:
        cursor = db.execute(sql)
        columns = [c[0] for c in cursor.description]
        rows = cursor.fetchmany(max_rows)
    return {"sql": sql, "columns": columns, "rows": rows}


# ---------------------------------------------------------------------------
# RAG (uses pre-built index produced by build_index.py)
# ---------------------------------------------------------------------------


def _load_rag_index():
    """Lazy-load faiss index + chunk metadata.

    Returns ``(index, chunks, meta)`` or ``None`` if the index hasn't been built.
    """
    if not RAG_INDEX_PATH.exists() or not RAG_CHUNKS_PATH.exists():
        return None
    try:
        import faiss  # type: ignore[import-untyped]
    except ImportError:
        return None
    index = faiss.read_index(str(RAG_INDEX_PATH))
    payload = json.loads(RAG_CHUNKS_PATH.read_text())
    return index, payload["chunks"], payload["meta"]


def _embed_query(query: str):
    """Use the same bge-large ONNX path as ``build_index.py`` for query embeddings."""
    import numpy as np
    import onnxruntime as ort
    from tokenizers import Tokenizer

    onnx_path = SSD_ROOT / "models" / "bge-large-en-v1.5" / "onnx" / "model.onnx"
    tok_path = SSD_ROOT / "models" / "bge-large-en-v1.5" / "tokenizer.json"

    if not hasattr(_embed_query, "_cache"):
        _embed_query._cache = (
            Tokenizer.from_file(str(tok_path)),
            ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"]),
        )
    tok, sess = _embed_query._cache

    enc = tok.encode(query)
    ids = np.array([enc.ids], dtype=np.int64)
    mask = np.array([enc.attention_mask], dtype=np.int64)
    type_ids = np.zeros_like(ids)
    feed = {
        "input_ids": ids,
        "attention_mask": mask,
        "token_type_ids": type_ids,
    }
    # Some exports don't ship token_type_ids — drop if so.
    expected = {i.name for i in sess.get_inputs()}
    feed = {k: v for k, v in feed.items() if k in expected}
    out = sess.run(None, feed)
    cls = out[0][:, 0, :]
    return cls / np.linalg.norm(cls, axis=1, keepdims=True)


def rag_search(query: str, k: int = 3) -> list[dict]:
    """Return the top-k retrieved chunks for ``query``."""
    loaded = _load_rag_index()
    if not loaded:
        return [
            {
                "error": (
                    "RAG index not found. Run build_index.py on the SSD first "
                    f"(expected {RAG_INDEX_PATH})."
                )
            }
        ]
    index, chunks, meta = loaded
    qv = _embed_query(query).astype("float32")
    distances, indices = index.search(qv, k)
    hits: list[dict] = []
    for rank, (idx, score) in enumerate(zip(indices[0], distances[0])):
        if idx < 0:
            continue
        hits.append(
            {
                "rank": rank + 1,
                "score": float(score),
                "source": meta[idx].get("source"),
                "chunk_index": meta[idx].get("chunk_index"),
                "text": chunks[idx],
            }
        )
    return hits


# ---------------------------------------------------------------------------
# Tool calling
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_employee",
            "description": "Look up an employee by email or employee_id to verify identity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string"},
                    "employee_id": {"type": "string"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_ticket",
            "description": "Create an IT/HR/security ticket.",
            "parameters": {
                "type": "object",
                "required": ["requester_email", "category", "priority", "summary"],
                "properties": {
                    "requester_email": {"type": "string"},
                    "category": {
                        "type": "string",
                        "enum": [
                            "network",
                            "software",
                            "hardware",
                            "access",
                            "hr",
                            "security_incident",
                        ],
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["P1", "P2", "P3", "P4"],
                    },
                    "summary": {"type": "string"},
                    "details": {"type": "string"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_ticket_status",
            "description": "Get the current status of a ticket.",
            "parameters": {
                "type": "object",
                "required": ["ticket_id"],
                "properties": {"ticket_id": {"type": "string"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "request_pto",
            "description": "Submit a PTO (paid time off) request for an employee.",
            "parameters": {
                "type": "object",
                "required": ["employee_id", "start_date", "end_date"],
                "properties": {
                    "employee_id": {"type": "string"},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    "note": {"type": "string"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reset_password",
            "description": "Trigger a self-service password reset email.",
            "parameters": {
                "type": "object",
                "required": ["employee_id"],
                "properties": {"employee_id": {"type": "string"}},
            },
        },
    },
]


def call_tool(name: str, args: dict[str, Any]) -> dict:
    """Dispatch a tool call to the local mock server."""
    try:
        if name == "lookup_employee":
            return requests.get(f"{MOCK_BASE_URL}/employees/lookup", params=args, timeout=5).json()
        if name == "create_ticket":
            return requests.post(f"{MOCK_BASE_URL}/tickets", json=args, timeout=5).json()
        if name == "get_ticket_status":
            ticket_id = args.get("ticket_id", "")
            return requests.get(f"{MOCK_BASE_URL}/tickets/{ticket_id}", timeout=5).json()
        if name == "request_pto":
            return requests.post(f"{MOCK_BASE_URL}/pto/request", json=args, timeout=5).json()
        if name == "reset_password":
            return requests.post(f"{MOCK_BASE_URL}/account/reset_password", json=args, timeout=5).json()
        return {"error": f"unknown tool {name}"}
    except requests.RequestException as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}


def _try_parse_inline_tool(content: str) -> tuple[str, dict] | None:
    """ReAct fallback: parse a tool call out of the assistant's free-form content.

    Triggered when vLLM's ``--tool-call-parser`` doesn't fire and the model
    expresses tool intent as raw JSON inside ``message.content``.
    """
    if not content:
        return None
    # Greedily find the largest balanced-looking JSON object
    candidates = re.findall(r"\{[^{}]*(?:\"tool\"|\"name\")[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", content, re.S)
    for candidate in candidates:
        try:
            obj = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        name = obj.get("tool") or obj.get("name") or obj.get("function")
        args = obj.get("args") or obj.get("arguments") or obj.get("parameters") or {}
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                args = {}
        if name:
            return name, args
    return None


def chat_with_tools(question: str, max_rounds: int = 5) -> str:
    """Multi-round tool-calling chat. Falls back to ReAct parsing if needed."""
    messages: list[dict] = [{"role": "user", "content": question}]
    for _ in range(max_rounds):
        resp = client.chat.completions.create(
            model=MODEL_ID,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=512,
        )
        msg = resp.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))

        # Path 1: native tool_calls populated
        if msg.tool_calls:
            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments or "{}")
                result = call_tool(tc.function.name, args)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result),
                    }
                )
            continue

        # Path 2: ReAct fallback — content has inline JSON
        parsed = _try_parse_inline_tool(msg.content or "")
        if parsed:
            name, args = parsed
            result = call_tool(name, args)
            messages.append(
                {
                    "role": "user",
                    "content": f"Tool `{name}` returned: {json.dumps(result)}",
                }
            )
            continue

        # No tool intent → final answer
        return msg.content or ""

    return "[exceeded tool rounds]"


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------


def _print_section(title: str) -> None:
    print(f"\n{'=' * 8} {title} {'=' * 8}")


def _smoke_test() -> None:
    _print_section("CONFIG")
    print(f"SSD_ROOT       = {SSD_ROOT}")
    print(f"MODEL_ID       = {MODEL_ID}")
    print(f"OPENAI_BASE    = {OPENAI_BASE_URL}")
    print(f"MOCK_BASE      = {MOCK_BASE_URL}")
    print(f"DB_PATH        = {DB_PATH}  exists={DB_PATH.exists()}")
    print(f"RAG_INDEX_PATH = {RAG_INDEX_PATH}  exists={RAG_INDEX_PATH.exists()}")

    _print_section("Text-to-SQL")
    result = text_to_sql("What was total completed revenue by product category in 2025?")
    print(json.dumps(result, indent=2, default=str))

    _print_section("RAG")
    hits = rag_search("VPN-503 reconnect steps")
    for hit in hits[:3]:
        if "error" in hit:
            print(hit)
        else:
            print(f"[{hit['source']} #{hit['chunk_index']}] score={hit['score']:.3f}")
            print(hit["text"][:200])
            print("---")

    _print_section("Tool calling")
    answer = chat_with_tools(
        "My VPN is broken with error VPN-503. My email is alice@meridian.com. "
        "Please file a P2 network ticket and tell me the ticket id."
    )
    print(answer)


if __name__ == "__main__":
    try:
        _smoke_test()
    except Exception as exc:  # noqa: BLE001 — surface anything during dry-run
        print(f"\nERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)
