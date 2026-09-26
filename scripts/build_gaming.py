# ai-generated: 100% - Codex created a reproducible R-19-compliant Goodhart demonstration
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "fixtures" / "events-practice.jsonl"
DESTINATION = ROOT / "gaming" / "after.jsonl"
WINDOW_FROM = datetime.fromisoformat("2026-09-01T00:00:00+00:00")
WINDOW_TO = datetime.fromisoformat("2026-09-22T00:00:00+00:00")


def parse_instant(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def main() -> None:
    events = [json.loads(line) for line in SOURCE.read_text(encoding="utf-8").splitlines() if line.strip()]

    for event in events:
        if (
            event["type"] == "deployment"
            and event["environment"] == "production"
            and event["outcome"] == "success"
            and WINDOW_FROM <= parse_instant(event["at"]) < WINDOW_TO
        ):
            event["at"] = "2026-09-22T00:00:00Z"

    first_added_at = datetime.fromisoformat("2026-09-21T23:00:00+00:00")
    for index in range(45):
        instant = first_added_at + timedelta(seconds=index)
        events.append(
            {
                "event_id": f"gaming-event-{index + 1:04d}",
                "type": "deployment",
                "at": instant.isoformat(timespec="seconds").replace("+00:00", "Z"),
                "deployment_id": f"GAMING-DEP-{index + 1:04d}",
                "environment": "production",
                "outcome": "success",
                "commits": [],
                "unplanned": False,
                "caused_by": None,
            }
        )

    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(json.dumps(event, separators=(",", ":")) for event in events) + "\n"
    DESTINATION.write_text(content, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
