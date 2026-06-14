#!/usr/bin/env python3
"""mock_server.py — Meridian Internal Ops Tools (OpenAPI-faithful FastAPI mock).

Run:
    uvicorn mock_server:app --host 0.0.0.0 --port 8088

Implements the 5 endpoints declared in
``mock_data/ops_agent/internal_tools_openapi.json``:

* GET  /employees/lookup           lookup_employee
* POST /tickets                    create_ticket
* GET  /tickets/{ticket_id}        get_ticket_status
* POST /pto/request                request_pto
* POST /account/reset_password     reset_password

All endpoints return realistic-looking but **fully fake** data. State is in
process memory only (resets on restart) — this is a hackathon demo, not a
production service.
"""
from __future__ import annotations

import random
import secrets
import string
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field

app = FastAPI(
    title="Meridian Internal Ops Tools (mock)",
    version="2026.1-mock",
    description="Local hackathon mock matching internal_tools_openapi.json",
)

# ---------------------------------------------------------------------------
# Fake data (seeded so each restart looks identical)
# ---------------------------------------------------------------------------

random.seed(42)

_EMPLOYEES_SEED: list[dict] = [
    {
        "employee_id": "E1001",
        "name": "Alice Nguyen",
        "email": "alice@meridian.com",
        "department": "IT",
        "manager_email": "diane@meridian.com",
        "pto_balance_days": 14.5,
    },
    {
        "employee_id": "E1002",
        "name": "Bob Schmidt",
        "email": "bob@meridian.com",
        "department": "Engineering",
        "manager_email": "diane@meridian.com",
        "pto_balance_days": 6.0,
    },
    {
        "employee_id": "E1003",
        "name": "Carmen Ortega",
        "email": "carmen@meridian.com",
        "department": "Sales",
        "manager_email": "eric@meridian.com",
        "pto_balance_days": 18.0,
    },
    {
        "employee_id": "E1004",
        "name": "Diane Park",
        "email": "diane@meridian.com",
        "department": "IT",
        "manager_email": "frank@meridian.com",
        "pto_balance_days": 9.5,
    },
    {
        "employee_id": "E1005",
        "name": "Eric Lambert",
        "email": "eric@meridian.com",
        "department": "Sales",
        "manager_email": "frank@meridian.com",
        "pto_balance_days": 4.0,
    },
    {
        "employee_id": "E1006",
        "name": "Farah Khan",
        "email": "farah@meridian.com",
        "department": "Security",
        "manager_email": "frank@meridian.com",
        "pto_balance_days": 20.0,
    },
]

EMPLOYEES_BY_EMAIL: dict[str, dict] = {e["email"]: e for e in _EMPLOYEES_SEED}
EMPLOYEES_BY_ID: dict[str, dict] = {e["employee_id"]: e for e in _EMPLOYEES_SEED}


@dataclass(frozen=True)
class TicketRecord:
    """Immutable ticket record kept in the in-memory store."""

    ticket_id: str
    status: str
    category: str
    priority: str
    summary: str
    requester_email: str
    details: str
    created_at: str
    updated_at: str

    def as_response(self) -> dict:
        # The schema only exposes a subset of fields publicly.
        return {
            "ticket_id": self.ticket_id,
            "status": self.status,
            "category": self.category,
            "priority": self.priority,
            "summary": self.summary,
            "created_at": self.created_at,
        }


TICKETS: dict[str, TicketRecord] = {}


# ---------------------------------------------------------------------------
# Pydantic request/response models
# ---------------------------------------------------------------------------


class EmployeeResponse(BaseModel):
    employee_id: str
    name: str
    email: str
    department: str
    manager_email: str
    pto_balance_days: float


TicketCategory = Literal[
    "network", "software", "hardware", "access", "hr", "security_incident"
]
TicketPriority = Literal["P1", "P2", "P3", "P4"]


class CreateTicketBody(BaseModel):
    requester_email: str
    category: TicketCategory
    priority: TicketPriority
    summary: str
    details: str = ""


class TicketResponse(BaseModel):
    ticket_id: str
    status: str
    category: str
    priority: str
    summary: str
    created_at: str


class PtoRequestBody(BaseModel):
    employee_id: str
    start_date: str
    end_date: str
    note: str = ""


class PtoResponse(BaseModel):
    request_id: str
    status: str
    employee_id: str
    start_date: str
    end_date: str
    approver_email: str
    submitted_at: str


class PasswordResetBody(BaseModel):
    employee_id: str


class PasswordResetResponse(BaseModel):
    employee_id: str
    status: str
    reset_email_sent_to: str
    expires_at: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _new_ticket_id() -> str:
    return "T-" + "".join(random.choices(string.digits, k=6))


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health")
def health() -> dict:
    """Convenience endpoint for quick smoke tests."""
    return {"status": "ok", "tickets": len(TICKETS), "employees": len(EMPLOYEES_BY_ID)}


@app.get("/employees/lookup", response_model=EmployeeResponse)
def lookup_employee(
    email: str | None = Query(default=None),
    employee_id: str | None = Query(default=None),
) -> dict:
    if not email and not employee_id:
        raise HTTPException(
            status_code=400, detail="Provide either email or employee_id"
        )
    if email and email in EMPLOYEES_BY_EMAIL:
        return EMPLOYEES_BY_EMAIL[email]
    if employee_id and employee_id in EMPLOYEES_BY_ID:
        return EMPLOYEES_BY_ID[employee_id]
    raise HTTPException(status_code=404, detail="employee not found")


@app.post("/tickets", response_model=TicketResponse, status_code=201)
def create_ticket(body: CreateTicketBody) -> dict:
    # Soft identity check — keeps the demo realistic without blocking unknown emails
    if body.requester_email not in EMPLOYEES_BY_EMAIL:
        # don't 401 — just note it. Lets the agent demo "create then verify" flows
        pass
    ticket = TicketRecord(
        ticket_id=_new_ticket_id(),
        status="open",
        category=body.category,
        priority=body.priority,
        summary=body.summary,
        requester_email=body.requester_email,
        details=body.details,
        created_at=_now_iso(),
        updated_at=_now_iso(),
    )
    TICKETS[ticket.ticket_id] = ticket
    return ticket.as_response()


@app.get("/tickets/{ticket_id}", response_model=TicketResponse)
def get_ticket_status(ticket_id: str) -> dict:
    rec = TICKETS.get(ticket_id)
    if not rec:
        raise HTTPException(status_code=404, detail=f"ticket {ticket_id} not found")
    return rec.as_response()


@app.post("/pto/request", response_model=PtoResponse, status_code=201)
def request_pto(body: PtoRequestBody) -> dict:
    emp = EMPLOYEES_BY_ID.get(body.employee_id)
    if not emp:
        raise HTTPException(
            status_code=404, detail=f"employee {body.employee_id} not found"
        )
    return {
        "request_id": "PTO-" + "".join(random.choices(string.digits, k=5)),
        "status": "submitted",
        "employee_id": body.employee_id,
        "start_date": body.start_date,
        "end_date": body.end_date,
        "approver_email": emp["manager_email"],
        "submitted_at": _now_iso(),
    }


@app.post("/account/reset_password", response_model=PasswordResetResponse)
def reset_password(body: PasswordResetBody) -> dict:
    emp = EMPLOYEES_BY_ID.get(body.employee_id)
    if not emp:
        raise HTTPException(
            status_code=404, detail=f"employee {body.employee_id} not found"
        )
    # In real life: enqueue email. Here: just acknowledge.
    return {
        "employee_id": body.employee_id,
        "status": "reset_email_sent",
        "reset_email_sent_to": emp["email"],
        "expires_at": _now_iso(),
    }


if __name__ == "__main__":
    # Standalone run for quick testing: python mock_server.py
    import uvicorn

    uvicorn.run(
        "mock_server:app",
        host="0.0.0.0",
        port=8088,
        log_level="info",
    )
