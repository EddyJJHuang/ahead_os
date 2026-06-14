#!/usr/bin/env python3
"""Read-only Google Workspace ingest for PM Agent live context.

This script fetches recent Gmail, Calendar, Meet, and Tasks context and writes
private local JSON snapshots under ``mock_data/pm_agent/live/``. That directory
is intentionally gitignored; run ``python build_pm_index.py`` afterward to fold
the live snapshots into the local PM RAG index.

Setup:
  1. Create a Google Cloud OAuth desktop client.
  2. Enable Gmail API, Google Calendar API, Google Tasks API, and optionally
     Google Meet API.
  3. Download OAuth credentials to ``credentials.json`` in the repo root.
  4. Run: ``python scripts/google_ingest.py --days 14 --query "checkout OR launch"``

Install deps only in the local/dev environment:
  pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LIVE_DIR = ROOT / "mock_data" / "pm_agent" / "live"
DEFAULT_CREDENTIALS = ROOT / "credentials.json"
DEFAULT_TOKEN = ROOT / "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.metadata",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/tasks.readonly",
    "https://www.googleapis.com/auth/meetings.space.readonly",
]


def _load_google_libs():
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as exc:
        sys.exit(
            "Missing Google API dependency: "
            + str(exc)
            + "\nInstall locally with: pip install google-api-python-client "
            "google-auth-httplib2 google-auth-oauthlib"
        )
    return Request, Credentials, InstalledAppFlow, build


def _credentials(credentials_path: Path, token_path: Path):
    Request, Credentials, InstalledAppFlow, _ = _load_google_libs()
    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not credentials_path.exists():
                sys.exit(f"OAuth credentials not found at {credentials_path}")
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json(), encoding="utf-8")
    return creds


def _header(headers: list[dict], name: str) -> str:
    for item in headers:
        if item.get("name", "").lower() == name.lower():
            return item.get("value", "")
    return ""


def _decode_body(data: str) -> str:
    if not data:
        return ""
    try:
        raw = base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))
        return raw.decode("utf-8", errors="replace")
    except Exception:
        return ""


def _plain_text_from_payload(payload: dict) -> str:
    mime = payload.get("mimeType", "")
    body = payload.get("body", {})
    if mime == "text/plain" and body.get("data"):
        return _decode_body(body["data"])
    for part in payload.get("parts", []) or []:
        text = _plain_text_from_payload(part)
        if text:
            return text
    return ""


def _redact(text: str) -> str:
    text = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[email]", text)
    text = re.sub(r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b", "[phone]", text)
    return text


def fetch_gmail(service, days: int, query: str, max_results: int, include_body: bool) -> dict:
    after = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y/%m/%d")
    q = f"after:{after}"
    if query:
        q += f" ({query})"
    resp = service.users().messages().list(
        userId="me",
        q=q,
        maxResults=max_results,
    ).execute()
    messages = []
    for item in resp.get("messages", []):
        msg = service.users().messages().get(
            userId="me",
            id=item["id"],
            format="full" if include_body else "metadata",
            metadataHeaders=["From", "To", "Cc", "Subject", "Date"],
        ).execute()
        headers = msg.get("payload", {}).get("headers", [])
        date_raw = _header(headers, "Date")
        try:
            date = parsedate_to_datetime(date_raw).isoformat()
        except Exception:
            date = date_raw
        record = {
            "id": msg.get("id"),
            "thread_id": msg.get("threadId"),
            "date": date,
            "from": _redact(_header(headers, "From")),
            "to": _redact(_header(headers, "To")),
            "subject": _header(headers, "Subject"),
            "snippet": _redact(msg.get("snippet", "")),
            "labels": msg.get("labelIds", []),
        }
        if include_body:
            record["body_excerpt"] = _redact(_plain_text_from_payload(msg.get("payload", {}))[:2000])
        messages.append(record)
    return {"source": "gmail", "query": q, "messages": messages}


def fetch_calendar(service, days: int, max_results: int) -> dict:
    now = datetime.now(timezone.utc)
    time_min = (now - timedelta(days=1)).isoformat()
    time_max = (now + timedelta(days=days)).isoformat()
    resp = service.events().list(
        calendarId="primary",
        timeMin=time_min,
        timeMax=time_max,
        maxResults=max_results,
        singleEvents=True,
        orderBy="startTime",
    ).execute()
    events = []
    for event in resp.get("items", []):
        attendees = [
            {
                "email": _redact(a.get("email", "")),
                "display_name": a.get("displayName", ""),
                "response_status": a.get("responseStatus", ""),
            }
            for a in event.get("attendees", []) or []
        ]
        conference = event.get("conferenceData", {})
        events.append(
            {
                "id": event.get("id"),
                "summary": event.get("summary", ""),
                "start": event.get("start", {}),
                "end": event.get("end", {}),
                "status": event.get("status", ""),
                "creator": _redact(event.get("creator", {}).get("email", "")),
                "organizer": _redact(event.get("organizer", {}).get("email", "")),
                "attendees": attendees,
                "hangout_link": event.get("hangoutLink", ""),
                "conference_id": conference.get("conferenceId", ""),
                "description_excerpt": _redact((event.get("description") or "")[:2000]),
            }
        )
    return {"source": "calendar", "time_min": time_min, "time_max": time_max, "events": events}


def fetch_tasks(service, max_results: int) -> dict:
    lists_resp = service.tasklists().list(maxResults=20).execute()
    task_lists = []
    for task_list in lists_resp.get("items", []):
        tasks_resp = service.tasks().list(
            tasklist=task_list["id"],
            maxResults=max_results,
            showCompleted=True,
            showDeleted=False,
            showHidden=False,
        ).execute()
        tasks = []
        for task in tasks_resp.get("items", []):
            tasks.append(
                {
                    "id": task.get("id"),
                    "title": task.get("title", ""),
                    "status": task.get("status", ""),
                    "due": task.get("due", ""),
                    "updated": task.get("updated", ""),
                    "notes_excerpt": _redact((task.get("notes") or "")[:1000]),
                }
            )
        task_lists.append({"id": task_list["id"], "title": task_list.get("title", ""), "tasks": tasks})
    return {"source": "tasks", "task_lists": task_lists}


def fetch_meet(meet_service, calendar_snapshot: dict, max_results: int) -> dict:
    records = []
    seen = set()
    for event in calendar_snapshot.get("events", []):
        conference_id = event.get("conference_id")
        if not conference_id or conference_id in seen:
            continue
        seen.add(conference_id)
        try:
            resp = meet_service.conferenceRecords().list(
                filter=f'space.meetingCode="{conference_id}"',
                pageSize=1,
            ).execute()
        except Exception as exc:
            records.append({"conference_id": conference_id, "error": f"{type(exc).__name__}: {exc}"})
            continue
        for rec in resp.get("conferenceRecords", [])[:max_results]:
            name = rec.get("name")
            item: dict[str, Any] = {
                "conference_id": conference_id,
                "name": name,
                "start_time": rec.get("startTime"),
                "end_time": rec.get("endTime"),
            }
            try:
                transcripts = meet_service.conferenceRecords().transcripts().list(parent=name).execute()
                item["transcripts"] = transcripts.get("transcripts", [])
            except Exception as exc:
                item["transcripts_error"] = f"{type(exc).__name__}: {exc}"
            records.append(item)
    return {"source": "meet", "conference_records": records}


def write_json(name: str, payload: dict) -> None:
    LIVE_DIR.mkdir(parents=True, exist_ok=True)
    path = LIVE_DIR / name
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest read-only Google Workspace data for PM Agent.")
    parser.add_argument("--credentials", default=str(DEFAULT_CREDENTIALS))
    parser.add_argument("--token", default=str(DEFAULT_TOKEN))
    parser.add_argument("--days", type=int, default=14)
    parser.add_argument("--query", default="launch OR checkout OR P0 OR blocker OR customer")
    parser.add_argument("--max-email", type=int, default=25)
    parser.add_argument("--max-calendar", type=int, default=30)
    parser.add_argument("--max-tasks", type=int, default=50)
    parser.add_argument("--include-email-body", action="store_true")
    parser.add_argument("--skip-meet", action="store_true")
    args = parser.parse_args()

    _, _, _, build = _load_google_libs()
    creds = _credentials(Path(args.credentials), Path(args.token))

    gmail = build("gmail", "v1", credentials=creds)
    calendar = build("calendar", "v3", credentials=creds)
    tasks = build("tasks", "v1", credentials=creds)

    gmail_snapshot = fetch_gmail(gmail, args.days, args.query, args.max_email, args.include_email_body)
    calendar_snapshot = fetch_calendar(calendar, args.days, args.max_calendar)
    tasks_snapshot = fetch_tasks(tasks, args.max_tasks)

    write_json("gmail.json", gmail_snapshot)
    write_json("google_calendar.json", calendar_snapshot)
    write_json("google_tasks.json", tasks_snapshot)

    if not args.skip_meet:
        try:
            meet = build("meet", "v2", credentials=creds)
            write_json("google_meet.json", fetch_meet(meet, calendar_snapshot, max_results=10))
        except Exception as exc:
            write_json("google_meet.json", {"source": "meet", "error": f"{type(exc).__name__}: {exc}"})

    print("\nNext: python build_pm_index.py")


if __name__ == "__main__":
    main()
