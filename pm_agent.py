#!/usr/bin/env python3
"""pm_agent.py — Local PM OS triage agent.

Three entry points used by api_server.py:
  * run_analysis()        — the "Run PM Analysis" workflow → structured
                            ship-readiness, risks, actions, executive summary.
  * ask(messages)         — evidence-grounded chat (retrieves via pm_tools then answers).
  * generate_draft(kind, context) — delegate to pm_tools draft generators.

Design: FACTS are computed deterministically from the sources (so the panels are
always correct and consistent), and the LLM is used for the executive *narrative*
and on-demand drafts. This keeps the demo reliable while still showing reasoning.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import agent
import pm_tools as T

TODAY = T.TODAY
LAUNCH_TARGET = T.LAUNCH_TARGET
NEXT_WINDOW = "2026-06-23"


def _ev(type_: str, id_: str, title: str, ref: str | None = None) -> dict:
    return {"type": type_, "id": id_, "title": title, "ref": ref}


# ---------------------------------------------------------------------------
# 1. Deterministic signal gathering
# ---------------------------------------------------------------------------
def gather_signals() -> dict:
    issues = T.search_jira()
    prs = T.search_github()
    emails = T.search_email()
    events = T.search_calendar()
    tasks = T.search_tasks()

    open_p0 = [i for i in issues if i.get("priority") == "P0" and i.get("status") not in ("Done", "Closed")]
    blocking_prs = [p for p in prs if p.get("blocking_launch") and p.get("status") != "merged"]
    unreviewed_prs = [p for p in blocking_prs if not p.get("approvals")]
    escalations = [e for e in emails if e.get("escalation")]
    qa_events = [e for e in events if "qa" in (e.get("title", "").lower())]
    qa_task = next((t for t in tasks if "qa sign-off" in t.get("title", "").lower()), None)
    comms_task = next((t for t in tasks if "stakeholder" in t.get("title", "").lower()), None)
    incomplete_tasks = [t for t in tasks if t.get("status") != "done"]
    return {
        "open_p0": open_p0, "blocking_prs": blocking_prs, "unreviewed_prs": unreviewed_prs,
        "escalations": escalations, "qa_events": qa_events, "qa_task": qa_task,
        "comms_task": comms_task, "incomplete_tasks": incomplete_tasks,
        "counts": {"issues": len(issues), "prs": len(prs), "emails": len(emails),
                   "events": len(events), "tasks": len(tasks)},
    }


# ---------------------------------------------------------------------------
# 2. Go/No-Go criteria (deterministic ship-readiness)
# ---------------------------------------------------------------------------
def evaluate_criteria(sig: dict) -> list[dict]:
    open_p0, qa_task, comms_task = sig["open_p0"], sig["qa_task"], sig["comms_task"]
    qa_ok = bool(sig["qa_events"]) and (qa_task or {}).get("status") == "done"
    return [
        {"name": "Zero open P0 bugs", "ok": len(open_p0) == 0,
         "detail": (f"{len(open_p0)} open P0 bug(s): " + ", ".join(i["id"] for i in open_p0)) if open_p0 else "No open P0 bugs",
         "evidence": [_ev("jira", i["id"], i["title"]) for i in open_p0]},
        {"name": "QA sign-off complete", "ok": qa_ok,
         "detail": "No QA review on the calendar and QA sign-off not done" if not qa_ok else "QA sign-off complete",
         "evidence": ([_ev("task", qa_task["id"], qa_task["title"])] if qa_task else []) +
                     [_ev("calendar", "GAP", "No 'Checkout QA Review' event scheduled")]},
        {"name": "All launch PRs merged", "ok": len(sig["blocking_prs"]) == 0,
         "detail": ("Open launch-blocking PR(s): " + ", ".join(f"PR-{p['number']}" for p in sig["blocking_prs"])) if sig["blocking_prs"] else "All launch PRs merged",
         "evidence": [_ev("github", f"PR-{p['number']}", p["title"]) for p in sig["blocking_prs"]]},
        {"name": "Stakeholder communication sent", "ok": (comms_task or {}).get("status") == "done",
         "detail": "Stakeholder launch update not sent" if (comms_task or {}).get("status") != "done" else "Stakeholder update sent",
         "evidence": [_ev("task", comms_task["id"], comms_task["title"])] if comms_task else []},
    ]


# ---------------------------------------------------------------------------
# 3. Risks + actions (deterministic, with real evidence chains)
# ---------------------------------------------------------------------------
def build_risks(sig: dict) -> list[dict]:
    risks = []
    if sig["open_p0"]:
        risks.append({
            "risk": f"{len(sig['open_p0'])} open P0 payment bug(s) block the launch",
            "severity": "Critical",
            "evidence": [_ev("jira", i["id"], i["title"]) for i in sig["open_p0"]],
            "mitigation": "Resolve CHK-101 (Amex 500) and CHK-102 (double-charge) before shipping; CHK-103 fix is in PR-89. Never ship payments with open P0s.",
        })
    if sig["escalations"]:
        e = sig["escalations"][0]
        risks.append({
            "risk": f"Escalating enterprise customer: {e.get('account','customer')}",
            "severity": "High",
            "evidence": [_ev("email", e["id"], e["subject"], e.get("thread_id"))] +
                        [_ev("jira", j, "linked issue") for j in e.get("links", {}).get("jira", [])],
            "mitigation": "Reply to the customer today tying resolution to CHK-101; the account is churn-sensitive.",
        })
    if sig["unreviewed_prs"]:
        p = sig["unreviewed_prs"][0]
        risks.append({
            "risk": f"Launch PR-{p['number']} unreviewed for {p.get('days_open','?')} days",
            "severity": "High",
            "evidence": [_ev("github", f"PR-{p['number']}", p["title"])] +
                        [_ev("jira", j, "launch story") for j in p.get("linked_jira", [])],
            "mitigation": f"Request review from {', '.join(p.get('requested_reviewers', [])) or 'a reviewer'} and merge; it blocks the launch story.",
        })
    if not (bool(sig["qa_events"]) and (sig["qa_task"] or {}).get("status") == "done"):
        qa_task = sig["qa_task"]
        risks.append({
            "risk": "QA sign-off cannot happen — no QA review scheduled",
            "severity": "High",
            "evidence": ([_ev("task", qa_task["id"], qa_task["title"])] if qa_task else []) +
                        [_ev("calendar", "GAP", "No 'Checkout QA Review' before Go/No-Go")],
            "mitigation": "Schedule a full-day checkout QA review before the Go/No-Go on 2026-06-18.",
        })
    if (sig["comms_task"] or {}).get("status") != "done":
        ct = sig["comms_task"]
        risks.append({
            "risk": "Stakeholder launch communication not sent",
            "severity": "Medium",
            "evidence": [_ev("task", ct["id"], ct["title"])] if ct else [],
            "mitigation": "Send a launch status update to affected accounts and internal stakeholders.",
        })
    return risks


def build_actions(sig: dict) -> list[dict]:
    """Top Actions (Panel 2). Each carries a draft_kind + context for /api/pm/draft."""
    actions = []
    if not (bool(sig["qa_events"]) and (sig["qa_task"] or {}).get("status") == "done"):
        actions.append({
            "id": "act-qa", "title": "Schedule checkout QA review", "impact": "High", "effort": "5 min",
            "draft_kind": "slack_update",
            "rationale": "QA sign-off is a hard launch gate and nothing is on the calendar (TASK-2).",
            "context": "Ask Sarah (QA Lead) to book a full-day Enterprise Checkout QA pass before the Go/No-Go on 2026-06-18. Covers Amex, multi-currency VAT, payment retry, PO billing. Blocks TASK-2.",
            "evidence": [_ev("task", "TASK-2", "QA sign-off on Enterprise Checkout"), _ev("calendar", "GAP", "No QA review scheduled")],
        })
    if sig["unreviewed_prs"]:
        p = sig["unreviewed_prs"][0]
        actions.append({
            "id": "act-pr", "title": f"Request review on PR-{p['number']}", "impact": "High", "effort": "2 min",
            "draft_kind": "slack_update",
            "rationale": f"PR-{p['number']} is the launch PR (CHK-110) and has had no review for {p.get('days_open','?')} days.",
            "context": f"Ping {', '.join(p.get('requested_reviewers', []))} to review PR-{p['number']} ('{p['title']}') today — it blocks the Enterprise Checkout launch.",
            "evidence": [_ev("github", f"PR-{p['number']}", p["title"])],
        })
    if sig["escalations"]:
        e = sig["escalations"][0]
        actions.append({
            "id": "act-cust", "title": f"Reply to {e.get('account','customer')} escalation", "impact": "High", "effort": "5 min",
            "draft_kind": "stakeholder_email",
            "rationale": "Churn-sensitive enterprise account escalating on the Amex failure (CHK-101).",
            "context": f"Reply to {e['from']} re: '{e['subject']}'. Acknowledge the Amex checkout failure (CHK-101), commit to a fix timeline, and reassure on the double-charge safeguard. Account: {e.get('account')}.",
            "evidence": [_ev("email", e["id"], e["subject"]), _ev("jira", "CHK-101", "Amex checkout failure")],
        })
    actions.append({
        "id": "act-memo", "title": "Send Go/No-Go decision memo", "impact": "High", "effort": "5 min",
        "draft_kind": "decision_memo",
        "rationale": "VP needs a clear recommendation before Thursday's Go/No-Go.",
        "context": "Recommend delaying the Enterprise Checkout launch from 2026-06-19 to 2026-06-23. Reasons: open P0 payment bugs (CHK-101/102), unreviewed launch PR-88, no QA sign-off. A 2-day slip is recoverable; a payment incident is not.",
        "evidence": [_ev("calendar", "EV-1", "Launch Go/No-Go"), _ev("jira", "CHK-101", "open P0"), _ev("github", "PR-88", "unreviewed launch PR")],
    })
    if (sig["comms_task"] or {}).get("status") != "done":
        actions.append({
            "id": "act-comms", "title": "Send stakeholder launch update", "impact": "Medium", "effort": "3 min",
            "draft_kind": "stakeholder_email",
            "rationale": "Stakeholder comms is a launch checklist item (TASK-4) and not started.",
            "context": "Send a brief status update to internal stakeholders and affected enterprise accounts on the Enterprise Checkout launch readiness and the likely 2-day delay.",
            "evidence": [_ev("task", "TASK-4", "Send stakeholder launch update")],
        })
    return actions


# ---------------------------------------------------------------------------
# 4. Executive summary (LLM narrative grounded in the deterministic facts)
# ---------------------------------------------------------------------------
def _facts_blob(sig: dict, criteria: list[dict]) -> str:
    lines = [f"Today: {TODAY}. Target launch: {LAUNCH_TARGET} (Enterprise Checkout)."]
    lines.append("Open P0 bugs: " + (", ".join(f"{i['id']} ({i['title']})" for i in sig["open_p0"]) or "none"))
    lines.append("Launch-blocking open PRs: " + (", ".join(f"PR-{p['number']} ({p.get('days_open','?')}d, reviews={len(p.get('approvals',[]))})" for p in sig["blocking_prs"]) or "none"))
    lines.append("Customer escalations: " + (", ".join(f"{e['id']} {e.get('account','')}" for e in sig["escalations"]) or "none"))
    lines.append("QA review scheduled: " + ("yes" if sig["qa_events"] else "NO") + f"; QA sign-off task status: {(sig['qa_task'] or {}).get('status','n/a')}")
    lines.append("Go/No-Go criteria: " + "; ".join(f"{c['name']}={'OK' if c['ok'] else 'FAIL'}" for c in criteria))
    return "\n".join(lines)


def _executive_summary(sig: dict, criteria: list[dict], decision: str) -> dict:
    what_changed = []
    if sig["escalations"]:
        what_changed.append(f"{sig['escalations'][0].get('account','A customer')} escalated again on the Amex checkout failure (CHK-101).")
    if sig["unreviewed_prs"]:
        p = sig["unreviewed_prs"][0]
        what_changed.append(f"PR-{p['number']} (launch PR) has sat unreviewed for {p.get('days_open','?')} days.")
    if sig["open_p0"]:
        what_changed.append(f"{len(sig['open_p0'])} P0 payment bugs are still open with the launch {('this week' )}.")
    whats_blocked = [c["detail"] for c in criteria if not c["ok"]]
    fallback_narrative = (
        f"Enterprise Checkout is currently a {decision} for the {LAUNCH_TARGET} target. "
        f"{len(sig['open_p0'])} open P0 payment bug(s), an unreviewed launch PR, and no scheduled QA sign-off "
        f"mean the launch criteria are not met. Recommend delaying to {NEXT_WINDOW} and clearing blockers."
    )
    narrative = fallback_narrative
    try:
        out = T._llm(
            "You are Local PM OS, an AI chief of staff. Given the facts, write a 2-3 sentence executive read "
            "for a product manager: are we on track, what's the biggest risk, what should happen next. "
            "Be specific and decision-oriented. Output only the paragraph.",
            _facts_blob(sig, criteria), max_tokens=300,
        )
        if out and len(out) > 40:
            narrative = out
    except Exception:
        pass
    return {
        "headline": f"Enterprise Checkout launch is {'AT RISK' if decision == 'NO' else 'ON TRACK'}",
        "what_changed": what_changed,
        "whats_blocked": whats_blocked,
        "recommended_decision": (f"Delay launch from {LAUNCH_TARGET} to {NEXT_WINDOW}" if decision == "NO" else "Proceed with launch"),
        "narrative": narrative,
    }


# ---------------------------------------------------------------------------
# 5. The "Run PM Analysis" workflow
# ---------------------------------------------------------------------------
def run_analysis() -> dict:
    sig = gather_signals()
    criteria = evaluate_criteria(sig)
    failed = [c for c in criteria if not c["ok"]]
    decision = "NO" if failed else "YES"
    risk_level = "Critical" if sig["open_p0"] else ("High" if failed else "Low")
    risks = build_risks(sig)
    actions = build_actions(sig)
    summary = _executive_summary(sig, criteria, decision)
    return {
        "ship_readiness": {
            "decision": decision,
            "recommended_action": summary["recommended_decision"],
            "risk_level": risk_level,
            "evidence_strength": "Strong",
            "based_on": ["Jira", "GitHub", "Email", "Calendar", "Tasks", "Docs"],
            "target_date": LAUNCH_TARGET,
        },
        "executive_summary": summary,
        "criteria": criteria,
        "risks": risks,
        "actions": actions,
        "stats": sig["counts"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# 6. Ask PM OS — evidence-grounded chat (tool-calling + ReAct fallback)
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = (
    "You are Local PM OS, a private AI chief of staff for a product manager at Meridian. "
    f"Today is {TODAY}; the Enterprise Checkout launch is targeted for {LAUNCH_TARGET}. "
    "Answer the PM's question using the evidence provided to you. Be concise and decision-oriented: "
    "state what is true, cite source IDs (e.g. CHK-101, PR-88, EM-2001), call out the key risk, and "
    "recommend the next action. If the evidence doesn't cover something, say so rather than guessing. "
    "Format answers in clean GitHub-flavored Markdown for a compact chat panel: start with a one-sentence "
    "answer, then use short bullet lists with bold labels when useful. Use inline source IDs, avoid raw HTML, "
    "avoid large tables unless the user explicitly asks for comparison, and keep headings to level 3 or smaller. "
    "Keep your reasoning brief."
)


def retrieve_evidence(question: str) -> dict:
    """Gather what's needed to answer a PM question: KB chunks (RAG) + a live
    state snapshot from the structured sources. Returns evidence text + a trace."""
    docs = [h for h in T.search_docs(question, k=4) if "text" in h]
    sig = gather_signals()
    p0 = ", ".join(f"{i['id']} ({i['title']})" for i in sig["open_p0"]) or "none"
    prs = ", ".join(f"PR-{p['number']} ('{p['title']}', open {p.get('days_open','?')}d, approvals={len(p.get('approvals',[]))})"
                    for p in sig["blocking_prs"]) or "none"
    esc = "; ".join(f"{e['id']} from {e.get('account','')}: {e['subject']}" for e in sig["escalations"]) or "none"
    state = [
        f"Target launch: {LAUNCH_TARGET}; Go/No-Go review: 2026-06-18.",
        f"Open P0 bugs: {p0}",
        f"Launch-blocking open PRs: {prs}",
        f"Customer escalations: {esc}",
        f"QA review scheduled on calendar: {'yes' if sig['qa_events'] else 'NO'}; QA sign-off task: {(sig['qa_task'] or {}).get('status','n/a')}",
        f"Stakeholder comms task: {(sig['comms_task'] or {}).get('status','n/a')}",
    ]
    text = ("## Knowledge base\n" + "\n".join(f"- [{h['source']}] {h['text']}" for h in docs) +
            "\n\n## Current state (live: Jira/GitHub/Email/Calendar/Tasks)\n" + "\n".join(f"- {s}" for s in state))
    trace = [
        {"type": "tool_call", "name": "retrieve_evidence", "args": {"query": question}},
        {"type": "tool_result", "name": "search_docs", "result": [{"source": h["source"], "score": round(h["score"], 3)} for h in docs]},
        {"type": "tool_result", "name": "state_snapshot", "result": state},
    ]
    return {"text": text, "trace": trace}


def ask(messages: list[dict], max_rounds: int = 1) -> dict:
    """Evidence-grounded answer: retrieve (RAG + state) then answer in ONE call.
    Reliable and fast — avoids open-ended ReAct with a verbose reasoning model."""
    question = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "")
    ev = retrieve_evidence(question)
    convo = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": "Evidence retrieved for the current question — answer using ONLY this, and cite the IDs:\n\n" + ev["text"]},
    ] + [m for m in messages if m.get("role") in ("user", "assistant")]
    resp = agent.client.chat.completions.create(model=agent.MODEL_ID, messages=convo, max_tokens=8192)
    return {"answer": resp.choices[0].message.content or "", "trace": ev["trace"]}


# delegate (kept here so api_server imports one module)
def generate_draft(kind: str, context: str) -> dict:
    return T.generate_draft(kind, context)
