# ai-generated: 100% - Codex implemented the Lab 2 metric rules R-01 through R-18
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any


UTC = timezone.utc
RATE_QUANTUM = Decimal("0.000001")
SECOND_QUANTUM = Decimal("1")


class DoraValidationError(ValueError):
    """The supplied DORA request or event log is not well formed."""


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise DoraValidationError(f"{label} must be an object")
    return value


def _require_string(value: Any, label: str, *, maximum: int | None = None) -> str:
    if not isinstance(value, str) or not value or (maximum is not None and len(value) > maximum):
        suffix = f" with 1..{maximum} characters" if maximum is not None else ""
        raise DoraValidationError(f"{label} must be a non-empty string{suffix}")
    return value


def _parse_instant(value: Any, label: str) -> datetime:
    if not isinstance(value, str):
        raise DoraValidationError(f"{label} must be an RFC 3339 instant")
    candidate = f"{value[:-1]}+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise DoraValidationError(f"{label} must be an RFC 3339 instant") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise DoraValidationError(f"{label} must include a UTC offset")
    return parsed.astimezone(UTC)


def _seconds(value) -> Decimal:
    return Decimal(value.days * 86400 + value.seconds) + Decimal(value.microseconds) / Decimal(1_000_000)


def _round_seconds(value: Decimal) -> int:
    return int(max(value, Decimal(0)).quantize(SECOND_QUANTUM, rounding=ROUND_HALF_UP))


def _median_seconds(values: list[Decimal]) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    middle = len(ordered) // 2
    value = ordered[middle] if len(ordered) % 2 else (ordered[middle - 1] + ordered[middle]) / 2
    return _round_seconds(value)


def _rate(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return float((Decimal(numerator) / Decimal(denominator)).quantize(RATE_QUANTUM, rounding=ROUND_HALF_UP))


def _normalise_events(raw_events: list[Any]) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    events: list[dict[str, Any]] = []
    seen_event_ids: set[str] = set()

    for position, raw_event in enumerate(raw_events):
        event = _require_mapping(raw_event, f"events[{position}]")
        event_id = _require_string(event.get("event_id"), f"events[{position}].event_id", maximum=64)
        if event_id in seen_event_ids:
            continue
        seen_event_ids.add(event_id)

        event_type = event.get("type")
        if event_type not in {"commit", "deployment", "incident"}:
            raise DoraValidationError(f"events[{position}].type is invalid")
        parsed = dict(event)
        parsed["_at"] = _parse_instant(event.get("at"), f"events[{position}].at")

        if event_type == "commit":
            parsed["sha"] = _require_string(event.get("sha"), f"events[{position}].sha")
            parsed["branch"] = _require_string(event.get("branch"), f"events[{position}].branch")
            reverts = event.get("reverts")
            change_id = event.get("change_id")
            if reverts is None:
                parsed["change_id"] = _require_string(change_id, f"events[{position}].change_id")
            else:
                parsed["reverts"] = _require_string(reverts, f"events[{position}].reverts")
                if change_id is not None:
                    raise DoraValidationError("a revert commit must have a null change_id")
        elif event_type == "deployment":
            parsed["deployment_id"] = _require_string(
                event.get("deployment_id"), f"events[{position}].deployment_id"
            )
            parsed["environment"] = _require_string(
                event.get("environment"), f"events[{position}].environment"
            )
            if event.get("outcome") not in {"success", "failure"}:
                raise DoraValidationError(f"events[{position}].outcome is invalid")
            commits = event.get("commits")
            if not isinstance(commits, list) or any(not isinstance(sha, str) or not sha for sha in commits):
                raise DoraValidationError(f"events[{position}].commits must be an array of shas")
            if not isinstance(event.get("unplanned"), bool):
                raise DoraValidationError(f"events[{position}].unplanned must be boolean")
            if event.get("caused_by") is not None:
                parsed["caused_by"] = _require_string(
                    event.get("caused_by"), f"events[{position}].caused_by"
                )
        else:
            parsed["incident_id"] = _require_string(
                event.get("incident_id"), f"events[{position}].incident_id"
            )
            if event.get("phase") not in {"opened", "resolved"}:
                raise DoraValidationError(f"events[{position}].phase is invalid")
            deployments = event.get("deployments")
            if not isinstance(deployments, list) or any(
                not isinstance(deployment_id, str) or not deployment_id for deployment_id in deployments
            ):
                raise DoraValidationError(f"events[{position}].deployments must be an array of ids")

        events.append(parsed)

    commits_by_sha: dict[str, dict[str, Any]] = {}
    deployments_by_id: dict[str, dict[str, Any]] = {}
    incidents_by_id: dict[str, dict[str, Any]] = {}

    for event in events:
        if event["type"] == "commit":
            if event["sha"] in commits_by_sha:
                raise DoraValidationError("commit shas must be unique")
            commits_by_sha[event["sha"]] = event
        elif event["type"] == "deployment":
            if event["deployment_id"] in deployments_by_id:
                raise DoraValidationError("deployment ids must be unique")
            deployments_by_id[event["deployment_id"]] = event
        else:
            incident = incidents_by_id.setdefault(
                event["incident_id"],
                {"incident_id": event["incident_id"], "opened": None, "resolved": None, "deployments": set()},
            )
            phase = event["phase"]
            if incident[phase] is not None:
                raise DoraValidationError(f"incident {event['incident_id']} has duplicate {phase} events")
            incident[phase] = event["_at"]
            incident["deployments"].update(event["deployments"])

    incident_ids = set(incidents_by_id)
    deployment_ids = set(deployments_by_id)
    for event in events:
        if event["type"] == "commit" and event.get("reverts") is not None:
            if event["reverts"] not in commits_by_sha:
                raise DoraValidationError(f"reverts references unknown sha {event['reverts']}")
        elif event["type"] == "deployment":
            for sha in event["commits"]:
                if sha not in commits_by_sha:
                    raise DoraValidationError(f"deployment references unknown sha {sha}")
            if event.get("caused_by") is not None and event["caused_by"] not in incident_ids:
                raise DoraValidationError(f"caused_by references unknown incident {event['caused_by']}")
        elif event["type"] == "incident":
            for deployment_id in event["deployments"]:
                if deployment_id not in deployment_ids:
                    raise DoraValidationError(f"incident references unknown deployment {deployment_id}")

    for incident in incidents_by_id.values():
        if incident["resolved"] is not None and incident["opened"] is None:
            raise DoraValidationError(f"incident {incident['incident_id']} resolved without opening")

    return events, commits_by_sha, deployments_by_id, incidents_by_id


def compute_metrics(payload: Any) -> dict[str, Any]:
    body = _require_mapping(payload, "body")
    window = _require_mapping(body.get("window"), "window")
    window_from = _parse_instant(window.get("from"), "window.from")
    window_to = _parse_instant(window.get("to"), "window.to")
    if window_to <= window_from:
        raise DoraValidationError("window.to must be after window.from")
    raw_events = body.get("events")
    if not isinstance(raw_events, list):
        raise DoraValidationError("events must be an array")

    events, commits_by_sha, _, incidents_by_id = _normalise_events(raw_events)

    resolved_changes: dict[str, str] = {}

    def resolve_change(sha: str, trail: set[str] | None = None) -> str:
        if sha in resolved_changes:
            return resolved_changes[sha]
        path = set() if trail is None else set(trail)
        if sha in path:
            raise DoraValidationError("revert chain contains a cycle")
        path.add(sha)
        commit = commits_by_sha[sha]
        change_id = commit.get("change_id")
        if commit.get("reverts") is not None:
            change_id = resolve_change(commit["reverts"], path)
        if not isinstance(change_id, str):
            raise DoraValidationError(f"commit {sha} does not resolve to a change")
        resolved_changes[sha] = change_id
        return change_id

    for sha in commits_by_sha:
        resolve_change(sha)

    production_deployments = [
        event
        for event in events
        if event["type"] == "deployment"
        and event["environment"] == "production"
        and window_from <= event["_at"] < window_to
    ]
    successful_deployments = [
        deployment for deployment in production_deployments if deployment["outcome"] == "success"
    ]
    failed_deployments = [
        deployment for deployment in production_deployments if deployment["outcome"] == "failure"
    ]

    first_success_by_sha: dict[str, dict[str, Any]] = {}
    for deployment in sorted(successful_deployments, key=lambda item: (item["_at"], item["deployment_id"].encode())):
        for sha in deployment["commits"]:
            first_success_by_sha.setdefault(sha, deployment)

    lead_times: list[Decimal] = []
    negative_lead_time_pairs = 0
    for sha, deployment in first_success_by_sha.items():
        duration = _seconds(deployment["_at"] - commits_by_sha[sha]["_at"])
        if duration < 0:
            negative_lead_time_pairs += 1
            duration = Decimal(0)
        lead_times.append(duration)

    off_main_shas = {
        sha
        for deployment in production_deployments
        for sha in deployment["commits"]
        if commits_by_sha[sha]["branch"] != "main"
    }
    deployments_without_commits = sum(not deployment["commits"] for deployment in production_deployments)

    recovery_times: list[Decimal] = []
    open_failures = 0
    for deployment in failed_deployments:
        covering = [
            incident
            for incident in incidents_by_id.values()
            if deployment["deployment_id"] in incident["deployments"] and incident["opened"] is not None
        ]
        covering.sort(key=lambda incident: (incident["opened"], incident["incident_id"].encode("utf-8")))
        incident = covering[0] if covering else None
        if incident is None or incident["resolved"] is None:
            open_failures += 1
            continue
        recovery_times.append(max(_seconds(incident["resolved"] - deployment["_at"]), Decimal(0)))

    incident_intervals = [
        (
            incident["incident_id"],
            incident["opened"],
            incident["resolved"] if incident["resolved"] is not None else window_to,
        )
        for incident in incidents_by_id.values()
        if incident["opened"] is not None
    ]
    overlapping_incident_pairs = 0
    for left_index, (_, left_start, left_end) in enumerate(incident_intervals):
        for _, right_start, right_end in incident_intervals[left_index + 1 :]:
            if left_start < right_end and right_start < left_end:
                overlapping_incident_pairs += 1

    first_commit_by_change: dict[str, datetime] = {}
    for sha, commit in commits_by_sha.items():
        change_id = resolved_changes[sha]
        current = first_commit_by_change.get(change_id)
        if current is None or commit["_at"] < current:
            first_commit_by_change[change_id] = commit["_at"]

    first_success_by_change: dict[str, datetime] = {}
    for deployment in sorted(successful_deployments, key=lambda item: (item["_at"], item["deployment_id"].encode())):
        for change_id in {resolved_changes[sha] for sha in deployment["commits"]}:
            first_success_by_change.setdefault(change_id, deployment["_at"])
    true_change_lead_times = [
        max(_seconds(deployed_at - first_commit_by_change[change_id]), Decimal(0))
        for change_id, deployed_at in first_success_by_change.items()
    ]

    deployments_count = len(production_deployments)
    failed_count = len(failed_deployments)
    rework_count = sum(
        deployment["unplanned"] and deployment.get("caused_by") is not None
        for deployment in production_deployments
    )
    window_days = _seconds(window_to - window_from) / Decimal(86400)
    deployment_frequency = float(
        (Decimal(deployments_count) / window_days).quantize(RATE_QUANTUM, rounding=ROUND_HALF_UP)
    )

    return {
        "spec_version": "1.0.0",
        "window": {"from": window["from"], "to": window["to"]},
        "deployment_frequency_per_day": deployment_frequency,
        "change_lead_time_seconds_p50": _median_seconds(lead_times),
        "failed_deployment_recovery_time_seconds_p50": _median_seconds(recovery_times),
        "change_fail_rate": _rate(failed_count, deployments_count),
        "deployment_rework_rate": _rate(rework_count, deployments_count),
        "counts": {
            "deployments": deployments_count,
            "successful_deployments": len(successful_deployments),
            "failed_deployments": failed_count,
            "recovered_failures": len(recovery_times),
            "open_failures": open_failures,
            "rework_deployments": rework_count,
            "lead_time_pairs": len(lead_times),
            "changes": len(set(resolved_changes.values())),
        },
        "anomalies": {
            "negative_lead_time_pairs": negative_lead_time_pairs,
            "deployments_without_commits": deployments_without_commits,
            "commits_never_on_main": len(off_main_shas),
            "revert_chains_collapsed": sum(
                commit.get("reverts") is not None for commit in commits_by_sha.values()
            ),
            "overlapping_incident_pairs": overlapping_incident_pairs,
        },
        "ground_truth": {
            "changes_delivered": len(first_success_by_change),
            "true_change_lead_time_seconds_p50": _median_seconds(true_change_lead_times),
        },
    }
