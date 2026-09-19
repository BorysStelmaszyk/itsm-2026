# ai-generated: 100% - Codex implemented the Lab 1 HTTP API from the accepted specification and decisions
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Annotated, Any
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .clock import (
    due_instants,
    format_instant,
    is_business_time,
    parse_instant,
    request_now,
    resolution_uses_business_clock,
)
from .models import TicketInput
from .storage import TicketStore


class ApiError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message


store = TicketStore(os.getenv("SVCDESK_DB", "svcdesk.db"))


@asynccontextmanager
async def lifespan(_: FastAPI):
    store.initialize()
    yield


app = FastAPI(title="svcdesk", lifespan=lifespan)


@app.exception_handler(ApiError)
async def api_error_handler(_, exc: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation",
                "message": "request validation failed",
                "details": exc.errors(),
            }
        },
    )


def now_dependency(
    x_test_clock: Annotated[str | None, Header(alias="X-Test-Clock")] = None,
) -> datetime:
    try:
        return request_now(x_test_clock)
    except ValueError as exc:
        raise ApiError(422, "invalid_clock", str(exc)) from exc


def load_ticket(ticket_id: str) -> dict[str, Any]:
    ticket = store.get(ticket_id)
    if ticket is None:
        raise ApiError(404, "not_found", "ticket not found")
    return ticket


def calculate_priority(impact: int, urgency: int, vip: bool) -> str:
    matrix = {
        (1, 1): "P1",
        (1, 2): "P2",
        (1, 3): "P3",
        (2, 1): "P2",
        (2, 2): "P3",
        (2, 3): "P4",
        (3, 1): "P3",
        (3, 2): "P4",
        (3, 3): "P4",
    }
    priority = matrix[(impact, urgency)]
    # Decision C3 is vip: matrix results P3 and P4 are raised to P2 for VIP reporters.
    if vip and priority in {"P3", "P4"}:
        return "P2"
    return priority


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "svcdesk"}


@app.post("/tickets", status_code=201)
def create_ticket(
    payload: TicketInput,
    now: Annotated[datetime, Depends(now_dependency)],
) -> dict[str, Any]:
    priority = calculate_priority(payload.impact, payload.urgency, payload.reporter.vip)
    ack_due_at, resolve_due_at = due_instants(priority, now)
    ticket = {
        "id": str(uuid4()),
        "title": payload.title,
        "description": payload.description,
        "reporter": payload.reporter.model_dump(),
        "impact": payload.impact,
        "urgency": payload.urgency,
        "priority": priority,
        "state": "new",
        "created_at": format_instant(now),
        "acknowledged_at": None,
        "resolved_at": None,
        "closed_at": None,
        "related_to": payload.related_to,
        "sla": {
            "ack_due_at": format_instant(ack_due_at),
            "resolve_due_at": format_instant(resolve_due_at),
        },
    }
    store.insert(ticket)
    return ticket


@app.get("/tickets")
def list_tickets(
    state: Annotated[str | None, Query()] = None,
    priority: Annotated[str | None, Query()] = None,
) -> list[dict[str, Any]]:
    return store.list(state, priority)


@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: str) -> dict[str, Any]:
    return load_ticket(ticket_id)


def transition(ticket_id: str, action: str, now: datetime) -> dict[str, Any]:
    ticket = load_ticket(ticket_id)
    expected_states = {
        "ack": "new",
        "start": "acknowledged",
        "resolve": "in_progress",
        "close": "resolved",
    }
    target_states = {
        "ack": "acknowledged",
        "start": "in_progress",
        "resolve": "resolved",
        "close": "closed",
    }

    if action == "reopen":
        # Decision C2 is immutable: only resolved tickets may reopen.
        if ticket["state"] == "closed":
            raise ApiError(409, "ticket_closed", "closed tickets are immutable")
        if ticket["state"] != "resolved":
            raise ApiError(409, "invalid_transition", "only a resolved ticket can be reopened")
        resolved_at = parse_instant(ticket["resolved_at"])
        if now > resolved_at + timedelta(days=7):
            raise ApiError(409, "reopen_window_expired", "the seven-day reopen window has expired")
        ticket["state"] = "in_progress"
        ticket["resolved_at"] = None
        ticket["closed_at"] = None
        store.save(ticket)
        return ticket

    if ticket["state"] != expected_states[action]:
        raise ApiError(409, "invalid_transition", f"cannot {action} a ticket in state {ticket['state']}")

    ticket["state"] = target_states[action]
    if action == "ack":
        ticket["acknowledged_at"] = format_instant(now)
    elif action == "resolve":
        ticket["resolved_at"] = format_instant(now)
    elif action == "close":
        ticket["closed_at"] = format_instant(now)
    store.save(ticket)
    return ticket


@app.post("/tickets/{ticket_id}/ack")
def acknowledge_ticket(
    ticket_id: str,
    now: Annotated[datetime, Depends(now_dependency)],
) -> dict[str, Any]:
    return transition(ticket_id, "ack", now)


@app.post("/tickets/{ticket_id}/start")
def start_ticket(
    ticket_id: str,
    now: Annotated[datetime, Depends(now_dependency)],
) -> dict[str, Any]:
    return transition(ticket_id, "start", now)


@app.post("/tickets/{ticket_id}/resolve")
def resolve_ticket(
    ticket_id: str,
    now: Annotated[datetime, Depends(now_dependency)],
) -> dict[str, Any]:
    return transition(ticket_id, "resolve", now)


@app.post("/tickets/{ticket_id}/close")
def close_ticket(
    ticket_id: str,
    now: Annotated[datetime, Depends(now_dependency)],
) -> dict[str, Any]:
    return transition(ticket_id, "close", now)


@app.post("/tickets/{ticket_id}/reopen")
def reopen_ticket(
    ticket_id: str,
    now: Annotated[datetime, Depends(now_dependency)],
) -> dict[str, Any]:
    return transition(ticket_id, "reopen", now)


@app.get("/tickets/{ticket_id}/sla")
def ticket_sla(
    ticket_id: str,
    now: Annotated[datetime, Depends(now_dependency)],
) -> dict[str, Any]:
    ticket = load_ticket(ticket_id)
    ack_due_at = parse_instant(ticket["sla"]["ack_due_at"])
    resolve_due_at = parse_instant(ticket["sla"]["resolve_due_at"])
    acknowledged_at = (
        parse_instant(ticket["acknowledged_at"]) if ticket["acknowledged_at"] is not None else None
    )
    resolved_at = parse_instant(ticket["resolved_at"]) if ticket["resolved_at"] is not None else None

    ack_breached = acknowledged_at > ack_due_at if acknowledged_at is not None else now > ack_due_at
    resolve_breached = resolved_at > resolve_due_at if resolved_at is not None else now > resolve_due_at
    paused = (
        ticket["state"] not in {"resolved", "closed"}
        and resolution_uses_business_clock(ticket["priority"])
        and not is_business_time(now)
    )

    return {
        "priority": ticket["priority"],
        "ack_due_at": ticket["sla"]["ack_due_at"],
        "resolve_due_at": ticket["sla"]["resolve_due_at"],
        "ack_breached": ack_breached,
        "resolve_breached": resolve_breached,
        "paused": paused,
    }
