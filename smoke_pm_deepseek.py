#!/usr/bin/env python3
"""Smoke-test PM launch readiness with DeepSeek/OpenAI-compatible chat.

This is a local-only helper for testing prompt quality before the GB10 FAISS
environment is ready. It does not start a server and does not replace
``api_server.py``.

Usage:
    export OPENAI_API_KEY=...
    export OPENAI_BASE_URL=https://api.deepseek.com/v1
    export MODEL_ID=deepseek-chat
    python smoke_pm_deepseek.py "Are we ready to launch?"
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PM_ROOT = ROOT / "mock_data" / "pm_agent"
DEFAULT_QUESTION = (
    "Are we ready to launch? Summarize blockers, customer impact, "
    "next actions, and the stakeholder update."
)

SYSTEM_PROMPT = """
You are a senior product operations partner for a local AI launch-readiness demo.
Use only the provided PM context to make a launch recommendation.

Return a concise brief with:
- Decision: Go, Conditional Go, or Hold
- Top blockers
- Customer impact
- Immediate next actions with owners when known
- Stakeholder update

Be explicit when evidence is missing. Do not invent Jira, GitHub, or customer facts.
"""


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def load_context() -> str:
    parts: list[str] = []
    for path in [
        PM_ROOT / "docs" / "pm_workspace.md",
        PM_ROOT / "docs" / "product_docs.md",
        PM_ROOT / "playbook" / "launch_readiness.md",
        PM_ROOT / "playbook" / "prioritization.md",
        PM_ROOT / "playbook" / "customer_escalations.md",
        PM_ROOT / "playbook" / "stakeholder_updates.md",
    ]:
        text = _read_text(path)
        if text:
            rel = path.relative_to(ROOT)
            parts.append(f"# Source: {rel}\n\n{text}")
    return "\n\n---\n\n".join(parts)


def chat(question: str) -> str:
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        sys.exit("Set OPENAI_API_KEY or DEEPSEEK_API_KEY before running this script.")

    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
    model = os.environ.get("MODEL_ID", "deepseek-chat")
    context = load_context()
    if not context:
        sys.exit("No PM context found. Expected files under mock_data/pm_agent/.")

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Question: {question}\n\n"
                    f"PM context:\n{context[:24000]}\n\n"
                    "Make the launch recommendation."
                ),
            },
        ],
        "temperature": 0.2,
        "max_tokens": 900,
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        sys.exit(f"HTTP {exc.code}: {detail}")
    except urllib.error.URLError as exc:
        if "CERTIFICATE_VERIFY_FAILED" not in str(exc):
            raise
        payload = _chat_with_curl(base_url, api_key, body)
    return payload["choices"][0]["message"]["content"]


def _chat_with_curl(base_url: str, api_key: str, body: dict) -> dict:
    """Fallback for Python.org macOS builds that lack local CA certificates."""
    proc = subprocess.run(
        [
            "curl",
            "-sS",
            base_url.rstrip("/") + "/chat/completions",
            "-H",
            "Content-Type: application/json",
            "-H",
            f"Authorization: Bearer {api_key}",
            "--data-binary",
            "@-",
        ],
        input=json.dumps(body),
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        sys.exit(proc.stderr.strip() or f"curl failed with exit code {proc.returncode}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        sys.exit(proc.stdout)


def main() -> None:
    question = " ".join(sys.argv[1:]).strip() or DEFAULT_QUESTION
    print(chat(question))


if __name__ == "__main__":
    main()
