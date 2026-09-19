# ai-generated: 100% - Codex implemented the request clock and SLA arithmetic from API.md
from __future__ import annotations

import os
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo


UTC = timezone.utc
WARSAW = ZoneInfo("Europe/Warsaw")
BUSINESS_OPEN = time(8, 0)
BUSINESS_CLOSE = time(16, 0)

SLA_TARGETS = {
    "P1": (timedelta(minutes=15), timedelta(hours=4)),
    "P2": (timedelta(hours=1), timedelta(hours=8)),
    "P3": (timedelta(hours=4), timedelta(hours=24)),
    "P4": (timedelta(hours=8), timedelta(hours=72)),
}


def parse_instant(value: str) -> datetime:
    candidate = value.strip()
    if candidate.endswith("Z"):
        candidate = f"{candidate[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ValueError("timestamp must be an RFC 3339 instant") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must include a UTC offset")
    return parsed.astimezone(UTC)


def format_instant(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def request_now(header_value: str | None) -> datetime:
    enabled = os.getenv("SVCDESK_TEST_CLOCK", "0").strip().lower() in {"1", "true"}
    if enabled and header_value is not None:
        return parse_instant(header_value)
    return datetime.now(UTC)


def is_business_time(value: datetime) -> bool:
    local = value.astimezone(WARSAW)
    local_time = local.time().replace(tzinfo=None)
    return local.weekday() < 5 and BUSINESS_OPEN <= local_time < BUSINESS_CLOSE


def _next_business_open(local: datetime) -> datetime:
    current = local
    while True:
        if current.weekday() >= 5:
            next_day = current.date() + timedelta(days=1)
            current = datetime.combine(next_day, BUSINESS_OPEN, tzinfo=WARSAW)
            continue

        current_time = current.time().replace(tzinfo=None)
        if current_time < BUSINESS_OPEN:
            return datetime.combine(current.date(), BUSINESS_OPEN, tzinfo=WARSAW)
        if current_time >= BUSINESS_CLOSE:
            next_day = current.date() + timedelta(days=1)
            current = datetime.combine(next_day, BUSINESS_OPEN, tzinfo=WARSAW)
            continue
        return current


def add_business_time(start: datetime, duration: timedelta) -> datetime:
    current = _next_business_open(start.astimezone(WARSAW))
    remaining = duration

    while True:
        closing = datetime.combine(current.date(), BUSINESS_CLOSE, tzinfo=WARSAW)
        available = closing - current
        if remaining <= available:
            return (current + remaining).astimezone(UTC)
        remaining -= available
        current = _next_business_open(
            datetime.combine(current.date() + timedelta(days=1), BUSINESS_OPEN, tzinfo=WARSAW)
        )


def resolution_uses_business_clock(priority: str) -> bool:
    # Decision C1 is wallclock: P1 is continuous, while P2-P4 use business hours.
    return priority != "P1"


def due_instants(priority: str, created_at: datetime) -> tuple[datetime, datetime]:
    acknowledgement_target, resolution_target = SLA_TARGETS[priority]
    if priority == "P1":
        return created_at + acknowledgement_target, created_at + resolution_target
    return (
        add_business_time(created_at, acknowledgement_target),
        add_business_time(created_at, resolution_target),
    )
