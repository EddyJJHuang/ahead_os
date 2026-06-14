#!/usr/bin/env python3
"""pm_autonomy.py - NemoClaw-backed autonomous PM monitoring.

This module keeps the product-facing autonomy contract small and demo-safe:
- NemoClaw/OpenClaw provides the local sandboxed agent runtime.
- PM OS keeps the product state, evidence readers, and suggestion API.
- Model reasoning/generation continues to route through the local vLLM endpoint.

State is intentionally in-memory for the hackathon demo. Persist tasks later once
real Jira/Gmail/Calendar connectors are wired into pm_tools.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pm_agent
import pm_tools

DEFAULT_SANDBOX_NAME = os.environ.get("NEMOCLAW_SANDBOX_NAME", "local-pm-os-agent")
DEFAULT_SOURCE_SCOPE = ["jira", "github", "emails", "calendar", "tasks", "slack"]
TASK_STORE_PATH = Path(os.environ.get(
    "PM_AUTONOMY_TASKS_PATH",
    str(Path(__file__).resolve().parent / "logs" / "pm_autonomy_tasks.json"),
))
URGENT_LEVELS = {"Critical", "High"}


@dataclass
class AutonomyTask:
    id: str
    title: str
    prompt: str
    cadence_minutes: int
    source_scope: list[str]
    task_type: str = "monitor"
    output_format: str | None = None
    enabled: bool = True
    created_from: str = "natural_language"
    created_at: str = field(default_factory=lambda: _iso(_now()))
    last_run_at: str | None = None
    next_run_at: str | None = None
    last_result: dict[str, Any] | None = None


_lock = threading.RLock()
_tasks: dict[str, AutonomyTask] = {}
_state: dict[str, Any] = {
    "last_scan_at": None,
    "last_fingerprint": None,
    "latest_suggestion": None,
    "monitor_runs": 0,
}
_scheduler_started = False
_scheduler_thread: threading.Thread | None = None
_store_loaded = False


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


def _clamp_cadence(minutes: int) -> int:
    return max(1, min(minutes, 7 * 24 * 60))


def _valid_scope(scope: list[str] | None) -> list[str]:
    allowed = set(DEFAULT_SOURCE_SCOPE)
    clean: list[str] = []
    for source in scope or []:
        normalized = str(source).strip().lower()
        if normalized == "email":
            normalized = "emails"
        if normalized in allowed and normalized not in clean:
            clean.append(normalized)
    return clean or list(DEFAULT_SOURCE_SCOPE)


def _task_to_dict(task: AutonomyTask) -> dict[str, Any]:
    return asdict(task)


def _load_tasks_locked() -> None:
    global _store_loaded
    if _store_loaded:
        return
    _store_loaded = True
    if not TASK_STORE_PATH.exists():
        return
    try:
        raw = json.loads(TASK_STORE_PATH.read_text(encoding="utf-8"))
        items = raw.get("tasks", raw if isinstance(raw, list) else [])
    except Exception:
        return
    fields = set(AutonomyTask.__dataclass_fields__)
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        try:
            kwargs = {key: item.get(key) for key in fields if key in item}
            kwargs["cadence_minutes"] = _clamp_cadence(int(kwargs.get("cadence_minutes") or 15))
            kwargs["source_scope"] = _valid_scope(kwargs.get("source_scope"))
            _tasks[str(kwargs["id"])] = AutonomyTask(**kwargs)
        except Exception:
            continue


def _save_tasks_locked() -> None:
    try:
        TASK_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = TASK_STORE_PATH.with_suffix(".tmp")
        payload = {"tasks": [_task_to_dict(task) for task in _tasks.values()]}
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(TASK_STORE_PATH)
    except Exception:
        pass


def ensure_default_tasks() -> None:
    with _lock:
        _load_tasks_locked()
        if "monitor-critical-evidence" in _tasks:
            return
        now = _now()
        _tasks["monitor-critical-evidence"] = AutonomyTask(
            id="monitor-critical-evidence",
            title="Monitor critical PM evidence",
            prompt=(
                "Every 15 minutes, scan Jira, GitHub, email, calendar, tasks, and the evidence drawer. "
                "If urgent launch risk appears, generate a decision suggestion and action options."
            ),
            cadence_minutes=15,
            source_scope=list(DEFAULT_SOURCE_SCOPE),
            created_from="system_default",
            created_at=_iso(now),
            next_run_at=_iso(now),
        )
        _save_tasks_locked()


def _nemoclaw_env() -> dict[str, str]:
    env = os.environ.copy()
    root = Path(__file__).resolve().parent
    path_parts = [str(root / ".venv" / "bin"), str(Path.home() / ".local" / "bin")]
    env["PATH"] = ":".join(path_parts + [env.get("PATH", "")])
    return env


def nemoclaw_runtime_status() -> dict[str, Any]:
    cmd = ["nemoclaw", DEFAULT_SANDBOX_NAME, "status", "--json"]
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(Path(__file__).resolve().parent),
            env=_nemoclaw_env(),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except FileNotFoundError:
        return {"installed": False, "name": DEFAULT_SANDBOX_NAME, "phase": "missing", "ok": False}
    except subprocess.TimeoutExpired:
        return {"installed": True, "name": DEFAULT_SANDBOX_NAME, "phase": "timeout", "ok": False}

    if proc.returncode != 0:
        return {
            "installed": True,
            "name": DEFAULT_SANDBOX_NAME,
            "phase": "error",
            "ok": False,
            "detail": (proc.stderr or proc.stdout).strip()[-500:],
        }

    try:
        status = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"installed": True, "name": DEFAULT_SANDBOX_NAME, "phase": "unknown", "ok": False}

    return {
        "installed": True,
        "name": status.get("name") or DEFAULT_SANDBOX_NAME,
        "phase": status.get("phase"),
        "ok": bool(status.get("found") and status.get("phase") == "Ready"),
        "model": status.get("model"),
        "provider": status.get("provider"),
        "gateway_state": status.get("gatewayState"),
        "openshell_driver": status.get("openshellDriver"),
        "openshell_version": status.get("openshellVersion"),
        "sandbox_gpu_enabled": status.get("sandboxGpuEnabled"),
        "policies": status.get("policies", []),
    }


def _extract_json_object(text: str) -> dict[str, Any] | None:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?", "", stripped).strip()
        stripped = re.sub(r"```$", "", stripped).strip()
    try:
        loaded = json.loads(stripped)
        return loaded if isinstance(loaded, dict) else None
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None
    try:
        loaded = json.loads(match.group(0))
        return loaded if isinstance(loaded, dict) else None
    except json.JSONDecodeError:
        return None


def _fallback_cadence_minutes(request: str) -> int:
    text = request.lower()
    patterns = [
        (r"每隔\s*(\d+)\s*分钟", 1),
        (r"每\s*(\d+)\s*分钟", 1),
        (r"every\s+(\d+)\s*(?:minute|minutes|min|mins)\b", 1),
        (r"每隔\s*(\d+)\s*(?:小时|小時)", 60),
        (r"每\s*(\d+)\s*(?:小时|小時)", 60),
        (r"every\s+(\d+)\s*(?:hour|hours|hr|hrs)\b", 60),
        (r"每隔\s*(\d+)\s*(?:天|日)", 1440),
        (r"每\s*(\d+)\s*(?:天|日)", 1440),
        (r"every\s+(\d+)\s*(?:day|days)\b", 1440),
    ]
    for pattern, factor in patterns:
        match = re.search(pattern, text)
        if match:
            return _clamp_cadence(int(match.group(1)) * factor)
    if any(term in text for term in ["每小时", "每小時", "hourly", "each hour"]):
        return 60
    if any(term in text for term in ["每天", "每日", "daily", "each day"]):
        return 1440
    if any(term in text for term in ["每周", "每週", "weekly"]):
        return 7 * 24 * 60
    return 15


def _fallback_scope(request: str) -> list[str]:
    text = request.lower()
    source_terms = {
        "jira": ["jira", "bug", "issue", "工单", "缺陷"],
        "github": ["github", "pull request", " pr", "prs", "代码", "合并"],
        "emails": ["email", "mail", "inbox", "邮件", "邮箱", "客户"],
        "calendar": ["calendar", "meeting", "event", "日历", "会议"],
        "tasks": ["task", "todo", "任务", "待办"],
        "slack": ["slack", "channel", "消息", "群"],
    }
    scope = [source for source, terms in source_terms.items() if any(term in text for term in terms)]
    if any(term in text for term in ["all", "所有", "全部", "evidence drawer", "证据", "evidence"]):
        return list(DEFAULT_SOURCE_SCOPE)
    return _valid_scope(scope)


def _fallback_task_type(request: str) -> str:
    text = request.lower()
    creative_terms = [
        "generate", "write", "draft", "summarize", "summary", "brief", "report",
        "memo", "compose", "create", "produce", "生成", "写", "撰写", "总结",
        "汇总", "摘要", "简报", "报告", "草拟", "产出", "创建", "方案",
    ]
    monitor_terms = [
        "monitor", "scan", "watch", "check", "alert", "detect", "notify",
        "检查", "巡检", "监控", "提醒", "发现", "紧急", "风险", "异常",
    ]
    if any(term in text for term in creative_terms):
        return "creative"
    if any(term in text for term in monitor_terms):
        return "monitor"
    return "monitor"


def _fallback_output_format(request: str, task_type: str) -> str | None:
    if task_type != "creative":
        return None
    text = request.lower()
    if any(term in text for term in ["email", "邮件"]):
        return "stakeholder_email"
    if any(term in text for term in ["memo", "decision", "决策"]):
        return "decision_memo"
    if any(term in text for term in ["report", "brief", "summary", "摘要", "简报", "报告", "总结", "汇总"]):
        return "brief"
    return "markdown_brief"


def _fallback_title(request: str, scope: list[str]) -> str:
    text = request.lower()
    if _fallback_task_type(request) == "creative":
        if any(term in text for term in ["launch", "上线", "发布", "go/no-go", "risk", "风险"]):
            return "Generate launch risk brief"
        if any(term in text for term in ["customer", "客户", "stakeholder", "沟通"]):
            return "Generate stakeholder update"
        if any(term in text for term in ["evidence", "证据", "drawer"]):
            return "Generate PM evidence summary"
        return "Generate recurring PM brief"
    if any(term in text for term in ["launch", "上线", "发布", "go/no-go", "风险", "risk"]):
        return "Monitor launch risk signals"
    if any(term in text for term in ["evidence", "证据", "drawer"]):
        return "Monitor PM evidence changes"
    if set(scope) == set(DEFAULT_SOURCE_SCOPE):
        return "Monitor PM evidence for urgent changes"
    labels = {
        "jira": "Jira",
        "github": "GitHub",
        "emails": "email",
        "calendar": "calendar",
        "tasks": "tasks",
        "slack": "Slack",
    }
    joined = ", ".join(labels.get(source, source) for source in scope[:3])
    if len(scope) > 3:
        joined += ", and more"
    return f"Monitor {joined}" if joined else "Autonomous PM task"


def _parse_task_request(request: str) -> dict[str, Any]:
    fallback_scope = _fallback_scope(request)
    fallback_type = _fallback_task_type(request)
    fallback = {
        "title": _fallback_title(request, fallback_scope),
        "cadence_minutes": _fallback_cadence_minutes(request),
        "source_scope": fallback_scope,
        "task_type": fallback_type,
        "output_format": _fallback_output_format(request, fallback_type),
        "run_immediately": True,
    }
    system = (
        "You convert a PM's natural-language automation request into compact JSON. "
        "Return JSON only, no Markdown. Fields: title (<=80 chars), cadence_minutes (integer), "
        "source_scope (array subset of jira, github, emails, calendar, tasks, slack), "
        "task_type ('monitor' for alerting/scanning, 'creative' for recurring generation/drafting), "
        "output_format (brief, decision_memo, stakeholder_email, markdown_brief, or null), "
        "run_immediately (boolean). If cadence is ambiguous, use 15 minutes. "
        "If the user says all/evidence drawer, include all sources."
    )
    examples = (
        "Examples:\n"
        "Request: 每隔 10 分钟检查 Jira 和邮件，有紧急情况就提醒我\n"
        "JSON: {\"title\":\"Monitor Jira and email escalations\",\"cadence_minutes\":10,\"source_scope\":[\"jira\",\"emails\"],\"task_type\":\"monitor\",\"output_format\":null,\"run_immediately\":true}\n"
        "Request: Check all launch evidence every hour and suggest actions\n"
        "JSON: {\"title\":\"Monitor launch evidence\",\"cadence_minutes\":60,\"source_scope\":[\"jira\",\"github\",\"emails\",\"calendar\",\"tasks\",\"slack\"],\"task_type\":\"monitor\",\"output_format\":null,\"run_immediately\":true}\n"
        "Request: 每天生成一份 launch risk brief，包含证据和 action options\n"
        "JSON: {\"title\":\"Generate launch risk brief\",\"cadence_minutes\":1440,\"source_scope\":[\"jira\",\"github\",\"emails\",\"calendar\",\"tasks\"],\"task_type\":\"creative\",\"output_format\":\"brief\",\"run_immediately\":true}\n"
    )
    try:
        raw = pm_tools._llm(system, f"{examples}\nRequest: {request}\nJSON:", max_tokens=240)
        parsed = _extract_json_object(raw) or {}
    except Exception:
        parsed = {}

    title = str(parsed.get("title") or fallback["title"]).strip()[:80] or fallback["title"]
    try:
        cadence = _clamp_cadence(int(parsed.get("cadence_minutes") or fallback["cadence_minutes"]))
    except (TypeError, ValueError):
        cadence = fallback["cadence_minutes"]
    raw_scope = parsed.get("source_scope")
    scope = _valid_scope(raw_scope if isinstance(raw_scope, list) else fallback["source_scope"])
    raw_type = str(parsed.get("task_type") or fallback["task_type"]).strip().lower()
    task_type = raw_type if raw_type in {"monitor", "creative"} else fallback["task_type"]
    output_format = parsed.get("output_format", fallback["output_format"])
    if output_format is not None:
        output_format = str(output_format).strip()[:40] or None
    return {
        "title": title,
        "cadence_minutes": cadence,
        "source_scope": scope,
        "task_type": task_type,
        "output_format": output_format,
        "run_immediately": bool(parsed.get("run_immediately", fallback["run_immediately"])),
    }


def _fingerprint(analysis: dict[str, Any], source_counts: dict[str, int]) -> str:
    material = {
        "decision": analysis.get("ship_readiness", {}).get("decision"),
        "risk_level": analysis.get("ship_readiness", {}).get("risk_level"),
        "risks": [
            {"risk": r.get("risk"), "severity": r.get("severity"), "evidence": r.get("evidence", [])}
            for r in analysis.get("risks", [])
            if r.get("severity") in URGENT_LEVELS
        ],
        "actions": [a.get("id") for a in analysis.get("actions", [])[:4]],
        "source_counts": source_counts,
    }
    encoded = json.dumps(material, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]


def _flatten_evidence(analysis: dict[str, Any], limit: int = 6) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for risk in analysis.get("risks", []):
        for ref in risk.get("evidence", []):
            key = f"{ref.get('type')}:{ref.get('id')}"
            if key in seen:
                continue
            seen.add(key)
            out.append(ref)
            if len(out) >= limit:
                return out
    for criterion in analysis.get("criteria", []):
        if criterion.get("ok"):
            continue
        for ref in criterion.get("evidence", []):
            key = f"{ref.get('type')}:{ref.get('id')}"
            if key in seen:
                continue
            seen.add(key)
            out.append(ref)
            if len(out) >= limit:
                return out
    return out


def _action_option(action: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": action.get("id"),
        "title": action.get("title"),
        "impact": action.get("impact"),
        "effort": action.get("effort"),
        "rationale": action.get("rationale"),
        "draft_kind": action.get("draft_kind"),
        "context": action.get("context"),
        "evidence": action.get("evidence", []),
    }


def _suggestion_from_analysis(
    analysis: dict[str, Any],
    *,
    trigger: str,
    source_scope: list[str],
    task_id: str | None,
    task_prompt: str | None,
    previous_fingerprint: str | None,
) -> dict[str, Any]:
    ship = analysis.get("ship_readiness", {})
    summary = analysis.get("executive_summary", {})
    risks = analysis.get("risks", [])
    urgent_risks = [r for r in risks if r.get("severity") in URGENT_LEVELS]
    decision = ship.get("decision", "NO")
    risk_level = ship.get("risk_level", "High")
    urgent = decision == "NO" or risk_level in URGENT_LEVELS or bool(urgent_risks)
    current_fp = _fingerprint(analysis, pm_tools.list_sources())
    changed = previous_fingerprint is not None and previous_fingerprint != current_fp

    if summary.get("what_changed"):
        why_now = " ".join(summary["what_changed"][:2])
    elif urgent_risks:
        top = urgent_risks[0]
        why_now = f"{top.get('risk')} {top.get('mitigation', '')}".strip()
    elif changed:
        why_now = "The evidence fingerprint changed since the last autonomous scan."
    else:
        why_now = "No new urgent blocker was found in this scan."

    if urgent:
        title = ship.get("recommended_action") or summary.get("recommended_decision") or "Review launch decision"
    else:
        title = "No urgent decision change detected"

    return {
        "id": f"sug-{uuid.uuid4().hex[:10]}",
        "title": title,
        "severity": risk_level,
        "urgent": urgent,
        "changed_since_last_scan": changed,
        "decision": decision,
        "summary": summary.get("narrative") or title,
        "why_now": why_now,
        "detected_at": _iso(_now()),
        "trigger": trigger,
        "task_id": task_id,
        "task_prompt": task_prompt,
        "source_scope": source_scope,
        "evidence": _flatten_evidence(analysis),
        "action_options": [_action_option(a) for a in analysis.get("actions", [])[:4]],
        "analysis_generated_at": analysis.get("generated_at"),
        "fingerprint": current_fp,
        "runtime": "NemoClaw / OpenClaw sandbox",
    }


def run_monitor(
    trigger: str = "manual",
    *,
    task_id: str | None = None,
    task_prompt: str | None = None,
    source_scope: list[str] | None = None,
) -> dict[str, Any]:
    scope = _valid_scope(source_scope)
    with _lock:
        previous_fingerprint = _state.get("last_fingerprint")

    analysis = pm_agent.run_analysis()
    source_counts = pm_tools.list_sources()
    suggestion = _suggestion_from_analysis(
        analysis,
        trigger=trigger,
        source_scope=scope,
        task_id=task_id,
        task_prompt=task_prompt,
        previous_fingerprint=previous_fingerprint,
    )

    with _lock:
        _state["last_scan_at"] = suggestion["detected_at"]
        _state["last_fingerprint"] = suggestion["fingerprint"]
        _state["latest_suggestion"] = suggestion
        _state["monitor_runs"] = int(_state.get("monitor_runs") or 0) + 1

    return {
        "status": "ok",
        "trigger": trigger,
        "source_counts": source_counts,
        "suggestion": suggestion,
        "runtime": nemoclaw_runtime_status(),
    }


def list_tasks() -> list[dict[str, Any]]:
    ensure_default_tasks()
    with _lock:
        return [_task_to_dict(task) for task in _tasks.values()]


def get_task(task_id: str) -> dict[str, Any] | None:
    ensure_default_tasks()
    with _lock:
        task = _tasks.get(task_id)
        return _task_to_dict(task) if task else None


def preview_task_request(request: str) -> dict[str, Any]:
    """Parse a natural-language request into a PROPOSED task spec without creating it.

    Powers the chat "launch a recurring task?" confirmation card: the model proposes
    the schedule/scope, the user confirms, then create_task_from_request actually runs.
    """
    spec = _parse_task_request(request)
    return {
        "request": request.strip(),
        "title": spec["title"],
        "cadence_minutes": spec["cadence_minutes"],
        "source_scope": spec["source_scope"],
        "task_type": spec["task_type"],
        "output_format": spec["output_format"],
    }


def create_task_from_request(request: str) -> dict[str, Any]:
    ensure_default_tasks()
    spec = _parse_task_request(request)
    now = _now()
    task = AutonomyTask(
        id=f"task-{uuid.uuid4().hex[:8]}",
        title=spec["title"],
        prompt=request.strip(),
        cadence_minutes=spec["cadence_minutes"],
        source_scope=spec["source_scope"],
        task_type=spec["task_type"],
        output_format=spec["output_format"],
        created_at=_iso(now),
        next_run_at=_iso(now + timedelta(minutes=spec["cadence_minutes"])),
    )
    with _lock:
        _tasks[task.id] = task
        _save_tasks_locked()

    result = None
    if spec.get("run_immediately", True):
        result = run_task(task.id)

    return {
        "status": "created",
        "task": get_task(task.id),
        "result": result,
        "latest_suggestion": get_latest_suggestion(),
        "runtime": nemoclaw_runtime_status(),
    }


def _creative_task_output(task_snapshot: dict[str, Any], analysis: dict[str, Any]) -> str:
    facts = {
        "ship_readiness": analysis.get("ship_readiness"),
        "executive_summary": analysis.get("executive_summary"),
        "top_risks": analysis.get("risks", [])[:5],
        "top_actions": analysis.get("actions", [])[:5],
        "criteria": analysis.get("criteria", []),
        "source_counts": pm_tools.list_sources(),
        "generated_at": analysis.get("generated_at"),
    }
    system = (
        "You are Local PM OS running as a private recurring work agent. "
        "Create the requested deliverable from the provided PM evidence only. "
        "Use compact GitHub-flavored Markdown, cite source IDs, and include concrete next actions. "
        "Do not invent facts, do not use raw HTML, and keep the output suitable for a PM chat panel."
    )
    user = (
        f"Recurring task request:\n{task_snapshot.get('prompt')}\n\n"
        f"Requested output format: {task_snapshot.get('output_format') or 'markdown_brief'}\n\n"
        f"Current evidence facts:\n{json.dumps(facts, ensure_ascii=False, indent=2)}"
    )
    return pm_tools._llm(system, user, max_tokens=1000).strip()


def update_task(task_id: str, *, enabled: bool | None = None, cadence_minutes: int | None = None) -> dict[str, Any]:
    ensure_default_tasks()
    with _lock:
        task = _tasks.get(task_id)
        if not task:
            return {"error": f"unknown task '{task_id}'"}
        if enabled is not None:
            task.enabled = bool(enabled)
        if cadence_minutes is not None:
            task.cadence_minutes = _clamp_cadence(int(cadence_minutes))
            task.next_run_at = _iso(_now() + timedelta(minutes=task.cadence_minutes))
        _save_tasks_locked()
        return {"status": "updated", "task": _task_to_dict(task)}


def run_task(task_id: str) -> dict[str, Any]:
    ensure_default_tasks()
    with _lock:
        task = _tasks.get(task_id)
        if not task:
            return {"error": f"unknown task '{task_id}'"}
        task_snapshot = _task_to_dict(task)

    result = run_monitor(
        trigger="task",
        task_id=task_id,
        task_prompt=task_snapshot["prompt"],
        source_scope=task_snapshot["source_scope"],
    )
    output = None
    output_error = None
    if task_snapshot.get("task_type") == "creative":
        try:
            output = _creative_task_output(task_snapshot, pm_agent.run_analysis())
        except Exception as exc:
            output_error = f"{type(exc).__name__}: {exc}"
    now = _now()
    with _lock:
        task = _tasks[task_id]
        task.last_run_at = _iso(now)
        task.next_run_at = _iso(now + timedelta(minutes=task.cadence_minutes))
        task.last_result = {
            "ran_at": task.last_run_at,
            "suggestion_id": result.get("suggestion", {}).get("id"),
            "urgent": result.get("suggestion", {}).get("urgent"),
            "task_type": task.task_type,
        }
        if output:
            task.last_result["output"] = output
        if output_error:
            task.last_result["output_error"] = output_error
        _save_tasks_locked()
        refreshed = _task_to_dict(task)
    return {"status": "ok", "task": refreshed, "result": result, "output": output, "output_error": output_error}


def get_latest_suggestion() -> dict[str, Any] | None:
    with _lock:
        return _state.get("latest_suggestion")


def get_status() -> dict[str, Any]:
    ensure_default_tasks()
    with _lock:
        state = dict(_state)
        tasks = [_task_to_dict(task) for task in _tasks.values()]
        scheduler_running = _scheduler_started and bool(_scheduler_thread and _scheduler_thread.is_alive())
    return {
        "status": "ok",
        "runtime": nemoclaw_runtime_status(),
        "scheduler": {
            "running": scheduler_running,
            "poll_seconds": 20,
            "task_count": len(tasks),
        },
        "tasks": tasks,
        "latest_suggestion": state.get("latest_suggestion"),
        "last_scan_at": state.get("last_scan_at"),
        "monitor_runs": state.get("monitor_runs", 0),
    }


def _scheduler_loop() -> None:
    while True:
        ensure_default_tasks()
        now = _now()
        due_ids: list[str] = []
        with _lock:
            for task in _tasks.values():
                if not task.enabled or not task.next_run_at:
                    continue
                try:
                    due_at = datetime.fromisoformat(task.next_run_at.replace("Z", "+00:00"))
                except ValueError:
                    due_at = now
                if due_at <= now:
                    due_ids.append(task.id)
        for task_id in due_ids:
            try:
                run_task(task_id)
            except Exception as exc:
                with _lock:
                    task = _tasks.get(task_id)
                    if task:
                        task.last_result = {"error": f"{type(exc).__name__}: {exc}", "ran_at": _iso(_now())}
                        task.next_run_at = _iso(_now() + timedelta(minutes=task.cadence_minutes))
                        _save_tasks_locked()
        time.sleep(20)


def start_scheduler() -> dict[str, Any]:
    global _scheduler_started, _scheduler_thread
    ensure_default_tasks()
    with _lock:
        if _scheduler_started and _scheduler_thread and _scheduler_thread.is_alive():
            return {"status": "already_running"}
        _scheduler_thread = threading.Thread(target=_scheduler_loop, name="pm-autonomy-scheduler", daemon=True)
        _scheduler_thread.start()
        _scheduler_started = True
    return {"status": "started"}
