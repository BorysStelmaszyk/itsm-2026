# ai-generated: 100% - Codex implemented black-box tests for the accepted Lab 1 API behavior
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any


BASE_URL = os.getenv("SVCDESK_URL", "http://svcdesk:8080").rstrip("/")
passed = 0
failed = 0


def request(
    method: str,
    path: str,
    body: dict[str, Any] | None = None,
    clock: str | None = None,
) -> tuple[int, Any]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"Content-Type": "application/json"} if data is not None else {}
    if clock is not None:
        headers["X-Test-Clock"] = clock
    operation = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(operation, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8")
        return exc.code, json.loads(payload) if payload else None


def check(name: str, condition: bool) -> None:
    global passed, failed
    if condition:
        passed += 1
        print(f"PASS {name}")
    else:
        failed += 1
        print(f"FAIL {name}")


def ticket_body(**overrides: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "title": "Own test ticket",
        "description": "Created by the Compose tests profile",
        "reporter": {"name": "Test Reporter", "email": None, "vip": False},
        "impact": 1,
        "urgency": 1,
        "related_to": None,
    }
    body.update(overrides)
    return body


def wait_for_service() -> None:
    for _ in range(30):
        try:
            status, payload = request("GET", "/health")
            if status == 200 and payload.get("status") == "ok":
                return
        except (OSError, ValueError):
            pass
        time.sleep(1)
    raise RuntimeError("svcdesk did not become healthy")


def main() -> int:
    try:
        wait_for_service()

        status, health = request("GET", "/health")
        check("health status", status == 200)
        check("health identity", health.get("service") == "svcdesk")

        t1 = "2026-10-14T10:00:00Z"
        status, first = request("POST", "/tickets", ticket_body(), t1)
        check("create status", status == 201)
        check("create state", first.get("state") == "new")
        check("matrix P1", first.get("priority") == "P1")
        check("test clock", first.get("created_at") == t1)

        status, second = request("POST", "/tickets", ticket_body(title="Second ticket"), t1)
        check("unique ids", status == 201 and second.get("id") != first.get("id"))

        vip_body = ticket_body(
            title="VIP visibility",
            reporter={"name": "VIP Reporter", "vip": True},
            impact=3,
            urgency=3,
            priority="P1",
        )
        status, vip = request("POST", "/tickets", vip_body, t1)
        check("VIP elevation", status == 201 and vip.get("priority") == "P2")
        check("client priority ignored", vip.get("priority") != "P1")

        status, fetched = request("GET", f"/tickets/{first['id']}")
        check("retrieve ticket", status == 200 and fetched.get("id") == first.get("id"))
        status, listed = request("GET", "/tickets?priority=P1")
        check("priority filter", status == 200 and first.get("id") in {item["id"] for item in listed})

        status, acknowledged = request(
            "POST", f"/tickets/{first['id']}/ack", clock="2026-10-14T10:05:00Z"
        )
        check("acknowledge", status == 200 and acknowledged.get("state") == "acknowledged")
        status, _ = request("POST", f"/tickets/{first['id']}/ack", clock="2026-10-14T10:06:00Z")
        check("duplicate ack rejected", status == 409)
        status, started = request(
            "POST", f"/tickets/{first['id']}/start", clock="2026-10-14T10:06:00Z"
        )
        check("start", status == 200 and started.get("state") == "in_progress")
        status, resolved = request(
            "POST", f"/tickets/{first['id']}/resolve", clock="2026-10-14T11:00:00Z"
        )
        check("resolve", status == 200 and resolved.get("state") == "resolved")
        status, reopened = request(
            "POST", f"/tickets/{first['id']}/reopen", clock="2026-10-20T11:00:00Z"
        )
        check("reopen resolved in window", status == 200 and reopened.get("state") == "in_progress")

        status, lifecycle = request("POST", "/tickets", ticket_body(title="Immutable close"), t1)
        lifecycle_id = lifecycle["id"]
        request("POST", f"/tickets/{lifecycle_id}/ack", clock="2026-10-14T10:05:00Z")
        request("POST", f"/tickets/{lifecycle_id}/start", clock="2026-10-14T10:06:00Z")
        request("POST", f"/tickets/{lifecycle_id}/resolve", clock="2026-10-14T11:00:00Z")
        status, closed = request(
            "POST", f"/tickets/{lifecycle_id}/close", clock="2026-10-14T12:00:00Z"
        )
        check("close", status == 200 and closed.get("state") == "closed")
        status, _ = request(
            "POST", f"/tickets/{lifecycle_id}/reopen", clock="2026-10-15T12:00:00Z"
        )
        check("closed immutable", status == 409)

        t3 = "2026-10-16T15:00:00Z"
        status, p1_after_hours = request("POST", "/tickets", ticket_body(title="After hours P1"), t3)
        check(
            "P1 wallclock SLA",
            status == 201
            and p1_after_hours.get("sla", {}).get("ack_due_at") == "2026-10-16T15:15:00Z"
            and p1_after_hours.get("sla", {}).get("resolve_due_at") == "2026-10-16T19:00:00Z",
        )

        status, invalid = request("POST", "/tickets", {"impact": 1, "urgency": 1}, t1)
        check("validation envelope", status in {400, 422} and "error" in invalid)
        status, invalid_clock = request("POST", "/tickets", ticket_body(), "yesterday")
        check("malformed clock", status in {400, 422} and "error" in invalid_clock)
        status, unknown = request("GET", "/tickets/does-not-exist")
        check("unknown ticket", status == 404 and "error" in unknown)
    except Exception as exc:  # The final summary still lets the checker explain a runner failure.
        global failed
        failed += 1
        print(f"FAIL unexpected runner error: {exc}")

    print(f"ITSMLAB-TESTS: passed={passed} failed={failed}")
    return 0 if failed == 0 and passed >= 10 else 1


if __name__ == "__main__":
    sys.exit(main())
