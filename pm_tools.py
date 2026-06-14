#!/usr/bin/env python3
"""pm_tools.py — Local PM OS tools.

Two families, matching the PRD:
  * READ tools     — search_jira/github/email/calendar/tasks (over the structured
                     JSON sources) + search_docs (RAG over the KB).
  * GENERATE tools — generate_jira_comment / slack_update / decision_memo /
                     stakeholder_email / followup_task (LLM-backed drafts).

Reuses the running stack: agent.client (vLLM :8000) for generation and
agent._embed_query (bge ONNX) for RAG. No new dependencies; agent.py unmodified.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import agent  # reuse vLLM client, MODEL_ID, SSD_ROOT, bge embedder

# Single source of truth for ALL demo data. Everything (panels, analysis,
# evidence, autonomy, chat) reads from here. Point PM_DATA_DIR at any directory
# that follows mock_data/pm_agent/SCHEMA.md to swap the entire dataset in one go.
PM_DIR = Path(os.environ.get("PM_DATA_DIR", str(agent.SSD_ROOT / "mock_data" / "pm_agent")))
# RAG index over PM_DIR/docs (rebuild with build_index.py after editing docs).
PM_RAG_INDEX = Path(os.environ.get("PM_RAG_INDEX", str(agent.SSD_ROOT / "rag_pm.faiss")))
PM_RAG_CHUNKS = Path(os.environ.get("PM_RAG_CHUNKS", str(agent.SSD_ROOT / "rag_pm_chunks.json")))

TODAY = "2026-06-14"
LAUNCH_TARGET = "2026-06-19"

# source name -> (filename, key holding the record list)
_SOURCES = {
    "jira": ("jira.json", "issues"),
    "github": ("github.json", "pull_requests"),
    "emails": ("emails.json", "messages"),
    "slack": ("slack.json", "messages"),
    "calendar": ("calendar.json", "events"),
    "tasks": ("tasks.json", "tasks"),
}

# ---------------------------------------------------------------------------
# Two-phase demo data
#   peacetime/  — always loaded (the normal day).
#   emergency/  — merged in ONLY while the emergency flag is set, simulating a
#                 crisis injected by trigger_emergency.sh or the API. This is how
#                 the demo goes "calm -> trigger -> AI detects & advises".
# A flat PM_DIR (no peacetime/) is still supported for single-set reference
# datasets like mock_data/pm_os.
# ---------------------------------------------------------------------------
PEACE_DIR = PM_DIR / "peacetime"
EMERGENCY_DIR = PM_DIR / "emergency"
EMERGENCY_FLAG = PM_DIR / ".emergency_active"


def emergency_active() -> bool:
    return EMERGENCY_FLAG.exists()


def set_emergency(active: bool) -> bool:
    """Toggle the emergency overlay. Returns the resulting state."""
    if active:
        EMERGENCY_FLAG.write_text("on", encoding="utf-8")
    elif EMERGENCY_FLAG.exists():
        EMERGENCY_FLAG.unlink()
    return emergency_active()


def _read_records(dirpath: Path, fname: str, key: str) -> tuple[list[dict], dict]:
    path = dirpath / fname
    if not path.exists():
        return [], {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get(key, []), data


def _load(source: str) -> tuple[list[dict], dict]:
    fname, key = _SOURCES[source]
    base = PEACE_DIR if PEACE_DIR.exists() else PM_DIR  # peacetime layout, else flat
    recs, meta = _read_records(base, fname, key)
    if emergency_active():
        erecs, _ = _read_records(EMERGENCY_DIR, fname, key)
        recs = recs + erecs
    return recs, meta


def list_sources() -> dict[str, int]:
    return {s: len(_load(s)[0]) for s in _SOURCES}


def get_source(source: str) -> dict:
    """Raw records + top-level metadata — powers the Evidence Explorer."""
    if source not in _SOURCES:
        return {"error": f"unknown source '{source}'", "available": list(_SOURCES)}
    recs, full = _load(source)
    list_key = _SOURCES[source][1]
    meta = {k: v for k, v in full.items() if k != list_key}
    return {"source": source, "count": len(recs), "meta": meta, "records": recs}


def _matches(rec: dict, query: str | None) -> bool:
    if not query:
        return True
    blob = json.dumps(rec, ensure_ascii=False).lower()
    return all(term in blob for term in query.lower().split())


def _search(source: str, query: str | None = None, **filters: Any) -> list[dict]:
    recs, _ = _load(source)
    out = []
    for r in recs:
        if not _matches(r, query):
            continue
        ok = True
        for k, v in filters.items():
            if v is None:
                continue
            rv = r.get(k)
            if isinstance(rv, str) and isinstance(v, str):
                if v.lower() not in rv.lower():  # forgiving substring match
                    ok = False
                    break
            elif rv != v:
                ok = False
                break
        if ok:
            out.append(r)
    return out


# ---- typed read tools (the PRD's search_*) --------------------------------
def search_jira(query=None, status=None, priority=None, component=None) -> list[dict]:
    return _search("jira", query, status=status, priority=priority, component=component)


def search_github(query=None, status=None) -> list[dict]:
    return _search("github", query, status=status)


def search_email(query=None) -> list[dict]:
    return _search("emails", query)


def search_calendar(query=None, type=None) -> list[dict]:
    return _search("calendar", query, type=type)


def search_tasks(query=None, status=None) -> list[dict]:
    return _search("tasks", query, status=status)


# ---- RAG over the KB docs (the PRD's search_docs) -------------------------
def _load_pm_index():
    if not PM_RAG_INDEX.exists() or not PM_RAG_CHUNKS.exists():
        return None
    try:
        import faiss
    except ImportError:
        return None
    index = faiss.read_index(str(PM_RAG_INDEX))
    payload = json.loads(PM_RAG_CHUNKS.read_text(encoding="utf-8"))
    return index, payload["chunks"], payload["meta"]


def search_docs(query: str, k: int = 4) -> list[dict]:
    loaded = _load_pm_index()
    if not loaded:
        return [{"error": "PM RAG index missing — build it with RAG_DOCS_DIR=mock_data/pm_os/docs python build_index.py"}]
    index, chunks, meta = loaded
    qv = agent._embed_query(query).astype("float32")
    distances, indices = index.search(qv, k)
    hits = []
    for rank, (idx, score) in enumerate(zip(indices[0], distances[0])):
        if idx < 0:
            continue
        hits.append({
            "rank": rank + 1,
            "score": float(score),
            "source": meta[idx].get("source"),
            "chunk_index": meta[idx].get("chunk_index"),
            "text": chunks[idx],
        })
    return hits


# ---------------------------------------------------------------------------
# Tool schemas + dispatch (for the Ask PM OS chat agent)
# ---------------------------------------------------------------------------
PM_TOOLS = [
    {"type": "function", "function": {
        "name": "search_jira",
        "description": "Search Jira issues for the Enterprise Checkout project. Filter by status (Open/In Progress/In Review/Done), priority (P0-P3), or component.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}, "status": {"type": "string"},
            "priority": {"type": "string"}, "component": {"type": "string"}}}}},
    {"type": "function", "function": {
        "name": "search_github",
        "description": "Search GitHub pull requests in the checkout-service repo. Filter by status (open/merged).",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}, "status": {"type": "string"}}}}},
    {"type": "function", "function": {
        "name": "search_email",
        "description": "Search emails, including customer escalations.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}}}},
    {"type": "function", "function": {
        "name": "search_calendar",
        "description": "Search calendar events (reviews, launches, meetings).",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}, "type": {"type": "string"}}}}},
    {"type": "function", "function": {
        "name": "search_tasks",
        "description": "Search PM tasks / launch checklist items. Filter by status (not_started/in_progress/blocked/done).",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}, "status": {"type": "string"}}}}},
    {"type": "function", "function": {
        "name": "search_docs",
        "description": "Semantic search over the product knowledge base (launch plan, strategy, success metrics, roadmap, company context). Use for launch criteria, goals, definitions.",
        "parameters": {"type": "object", "required": ["query"], "properties": {
            "query": {"type": "string"}, "k": {"type": "integer"}}}}},
]

_DISPATCH = {
    "search_jira": search_jira, "search_github": search_github,
    "search_email": search_email, "search_calendar": search_calendar,
    "search_tasks": search_tasks, "search_docs": search_docs,
}


def call_pm_tool(name: str, args: dict) -> Any:
    fn = _DISPATCH.get(name)
    if not fn:
        return {"error": f"unknown tool {name}"}
    try:
        return fn(**(args or {}))
    except TypeError as exc:
        return {"error": f"bad args for {name}: {exc}"}


# ---------------------------------------------------------------------------
# Generation tools (LLM-backed drafts)
# ---------------------------------------------------------------------------
def _llm(system: str, user: str, max_tokens: int = 700) -> str:
    resp = agent.client.chat.completions.create(
        model=agent.MODEL_ID,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        max_tokens=max_tokens,
    )
    return (resp.choices[0].message.content or "").strip()


def generate_jira_comment(context: str) -> str:
    return _llm("You are a product manager writing a concise, professional Jira comment. "
                "Output only the comment text (no preamble).", f"Context:\n{context}\n\nWrite the Jira comment.")


def generate_slack_update(context: str) -> str:
    return _llm("You are a PM posting a short, scannable Slack update to the launch channel. "
                "Use a couple of bullet points and @-mentions where useful. Output only the message.",
                f"Context:\n{context}\n\nWrite the Slack message.")


def generate_decision_memo(context: str) -> str:
    return _llm("You are a PM writing a crisp launch Go/No-Go decision memo. "
                "Structure: Decision, Why (evidence), Conditions to revisit. Output only the memo.",
                f"Context:\n{context}\n\nWrite the decision memo.")


def generate_stakeholder_email(context: str) -> str:
    return _llm("You are a PM writing a concise stakeholder email about a product launch status. "
                "Professional, direct, no fluff. Output only Subject: and the body.",
                f"Context:\n{context}\n\nWrite the email.")


def generate_followup_task(context: str) -> str:
    return _llm("You are a PM creating a clear follow-up task. Output only: a one-line Title, "
                "an Owner suggestion, a Due date suggestion, and one sentence of detail.",
                f"Context:\n{context}\n\nWrite the task.")


DRAFT_KINDS = {
    "jira_comment": generate_jira_comment,
    "slack_update": generate_slack_update,
    "decision_memo": generate_decision_memo,
    "stakeholder_email": generate_stakeholder_email,
    "followup_task": generate_followup_task,
}


def generate_draft(kind: str, context: str) -> dict:
    fn = DRAFT_KINDS.get(kind)
    if not fn:
        return {"error": f"unknown draft kind '{kind}'", "available": list(DRAFT_KINDS)}
    return {"kind": kind, "draft": fn(context)}
