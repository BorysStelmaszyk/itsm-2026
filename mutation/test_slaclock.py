# ai-generated: 100% - Codex wrote behavioural tests from the course module's documented contracts.
"""Contract tests: explicit boundary cases, without inspecting implementation text."""

from datetime import datetime, timedelta

import pytest

import slaclock


def moment(text):
    return datetime.fromisoformat(text)


@pytest.mark.parametrize(
    "impact,urgency,ordinary,vip",
    [
        (1, 1, "P1", "P1"), (1, 2, "P2", "P2"), (1, 3, "P3", "P2"),
        (2, 1, "P2", "P2"), (2, 2, "P3", "P2"), (2, 3, "P4", "P2"),
        (3, 1, "P3", "P2"), (3, 2, "P4", "P2"), (3, 3, "P4", "P2"),
    ],
)
def test_priority_matrix_and_vip(impact, urgency, ordinary, vip):
    assert slaclock.priority_of(impact, urgency) == ordinary
    assert slaclock.priority_of(impact, urgency, False) == ordinary
    assert slaclock.priority_of(impact, urgency, True) == vip


@pytest.mark.parametrize("invalid", [-100, -1, 0, 4, 100, 1.0, 2.0, True, False, "1", None])
@pytest.mark.parametrize("vip", [False, True])
def test_priority_rejects_invalid_impact_and_urgency(invalid, vip):
    with pytest.raises(ValueError):
        slaclock.priority_of(invalid, 2, vip)
    with pytest.raises(ValueError):
        slaclock.priority_of(2, invalid, vip)


@pytest.mark.parametrize(
    "priority,expected",
    [("P1", (15, 240)), ("P2", (60, 480)), ("P3", (240, 1440)), ("P4", (480, 4320))],
)
def test_targets(priority, expected):
    assert slaclock.targets(priority) == expected


@pytest.mark.parametrize("priority", ["", "p1", " P1", "P1 ", "P0", "P5", "P11", "1"])
def test_unknown_priority_is_rejected(priority):
    with pytest.raises(ValueError):
        slaclock.targets(priority)
    with pytest.raises(ValueError):
        slaclock.escalation_tier(priority, False, 0)


@pytest.mark.parametrize(
    "elapsed,target,expected",
    [
        (0, 1, "ok"), (1, 1, "warning"), (2, 1, "breached"),
        (0, 4, "ok"), (2, 4, "ok"), (3, 4, "warning"),
        (4, 4, "warning"), (5, 4, "breached"),
        (11, 15, "ok"), (12, 15, "warning"), (14, 15, "warning"),
        (15, 15, "warning"), (16, 15, "breached"),
        (44, 60, "ok"), (45, 60, "warning"), (60, 60, "warning"),
        (61, 60, "breached"), (74, 100, "ok"), (75, 100, "warning"),
        (76, 100, "warning"), (100, 100, "warning"), (101, 100, "breached"),
        (75, 101, "ok"), (76, 101, "warning"), (10000, 15, "breached"),
    ],
)
def test_sla_thresholds(elapsed, target, expected):
    assert slaclock.sla_state(elapsed, target) == expected


@pytest.mark.parametrize("elapsed,target", [(-1, 1), (-100, 100), (0, 0), (1, 0), (0, -1), (-1, -1)])
def test_invalid_sla_clock(elapsed, target):
    with pytest.raises(ValueError):
        slaclock.sla_state(elapsed, target)


@pytest.mark.parametrize("weekday", range(7))
@pytest.mark.parametrize(
    "time,inside",
    [("00:00", False), ("07:59", False), ("08:00", True), ("08:01", True),
     ("12:00", True), ("15:59", True), ("16:00", False), ("16:01", False), ("23:59", False)],
)
def test_business_hours_every_weekday(weekday, time, inside):
    monday = moment(f"2026-11-09T{time}:59.999999")
    assert slaclock.is_business_time(monday + timedelta(days=weekday)) is (weekday < 5 and inside)


@pytest.mark.parametrize(
    "start,minutes,expected",
    [
        ("2026-11-09T07:59", 0, "2026-11-09T08:00"),
        ("2026-11-09T00:00", 1, "2026-11-09T08:01"),
        ("2026-11-09T08:00", 0, "2026-11-09T08:00"),
        ("2026-11-09T08:00", 1, "2026-11-09T08:01"),
        ("2026-11-09T08:00", 479, "2026-11-09T15:59"),
        ("2026-11-09T08:00", 480, "2026-11-09T16:00"),
        ("2026-11-09T08:00", 481, "2026-11-10T08:01"),
        ("2026-11-09T08:00", 960, "2026-11-10T16:00"),
        ("2026-11-09T12:34", 0, "2026-11-09T12:34"),
        ("2026-11-09T12:34", 206, "2026-11-09T16:00"),
        ("2026-11-09T12:34", 207, "2026-11-10T08:01"),
        ("2026-11-09T15:59", 1, "2026-11-09T16:00"),
        ("2026-11-09T15:59", 2, "2026-11-10T08:01"),
        ("2026-11-09T16:00", 0, "2026-11-10T08:00"),
        ("2026-11-09T23:59", 1, "2026-11-10T08:01"),
        ("2026-11-13T15:59", 1, "2026-11-13T16:00"),
        ("2026-11-13T15:59", 2, "2026-11-16T08:01"),
        ("2026-11-13T16:00", 0, "2026-11-16T08:00"),
        ("2026-11-14T07:00", 0, "2026-11-16T08:00"),
        ("2026-11-14T12:00", 480, "2026-11-16T16:00"),
        ("2026-11-15T23:59", 1, "2026-11-16T08:01"),
        ("2026-11-09T08:00", 2400, "2026-11-13T16:00"),
        ("2026-11-09T08:00", 2401, "2026-11-16T08:01"),
        ("2026-12-31T15:59", 2, "2027-01-01T08:01"),
        ("2024-02-28T15:59", 2, "2024-02-29T08:01"),
    ],
)
def test_add_business_minutes(start, minutes, expected):
    assert slaclock.add_business_minutes(moment(start), minutes) == moment(expected)


@pytest.mark.parametrize("start", ["2026-11-09T08:00", "2026-11-14T12:00"])
def test_add_rejects_negative_duration(start):
    with pytest.raises(ValueError):
        slaclock.add_business_minutes(moment(start), -1)


def test_add_ignores_seconds_and_microseconds():
    assert slaclock.add_business_minutes(moment("2026-11-09T12:34:59.999999"), 0) == moment("2026-11-09T12:34")
    assert slaclock.add_business_minutes(moment("2026-11-13T15:59:59.999999"), 1) == moment("2026-11-13T16:00")
    assert slaclock.add_business_minutes(moment("2026-11-09T07:59:59.999999"), 1) == moment("2026-11-09T08:01")


def test_add_allows_day_366_but_not_367():
    # 2024 starts on Monday; its 366 calendar days contain 262 weekdays.
    start = moment("2024-01-01T08:00")
    assert slaclock.add_business_minutes(start, 262 * 480) == moment("2024-12-31T16:00")
    assert slaclock.add_business_minutes(start, 262 * 480 + 1) == moment("2025-01-01T08:01")
    assert slaclock.add_business_minutes(start, 263 * 480) == moment("2025-01-01T16:00")
    with pytest.raises(ValueError):
        slaclock.add_business_minutes(start, 263 * 480 + 1)


@pytest.mark.parametrize(
    "start,end,expected",
    [
        ("2026-11-09T08:00", "2026-11-09T08:00", 0),
        ("2026-11-14T12:00", "2026-11-14T12:00", 0),
        ("2026-11-09T00:00", "2026-11-09T07:59", 0),
        ("2026-11-09T07:59", "2026-11-09T08:00", 0),
        ("2026-11-09T07:59", "2026-11-09T08:01", 1),
        ("2026-11-09T08:00", "2026-11-09T08:01", 1),
        ("2026-11-09T08:00", "2026-11-09T15:59", 479),
        ("2026-11-09T08:00", "2026-11-09T16:00", 480),
        ("2026-11-09T00:00", "2026-11-09T23:59", 480),
        ("2026-11-09T12:34", "2026-11-09T15:02", 148),
        ("2026-11-09T15:59", "2026-11-09T16:01", 1),
        ("2026-11-09T16:00", "2026-11-09T23:59", 0),
        ("2026-11-09T16:00", "2026-11-10T08:00", 0),
        ("2026-11-09T15:59", "2026-11-10T08:01", 2),
        ("2026-11-09T08:00", "2026-11-10T16:00", 960),
        ("2026-11-13T15:59", "2026-11-16T08:01", 2),
        ("2026-11-13T16:00", "2026-11-16T08:00", 0),
        ("2026-11-14T00:00", "2026-11-15T23:59", 0),
        ("2026-11-09T08:00", "2026-11-16T08:00", 2400),
        ("2026-11-09T08:00", "2026-11-16T08:01", 2401),
        ("2026-12-31T15:59", "2027-01-01T08:01", 2),
        ("2024-02-28T15:59", "2024-02-29T08:01", 2),
    ],
)
def test_business_minutes_between(start, end, expected):
    assert slaclock.business_minutes_between(moment(start), moment(end)) == expected


def test_between_ignores_subminute_parts_before_comparing():
    assert slaclock.business_minutes_between(moment("2026-11-09T08:00:59.999999"), moment("2026-11-09T08:01:00")) == 1
    assert slaclock.business_minutes_between(moment("2026-11-09T08:00:59"), moment("2026-11-09T08:00:01")) == 0


@pytest.mark.parametrize("start,end", [
    ("2026-11-09T08:01", "2026-11-09T08:00"),
    ("2026-11-15T00:00", "2026-11-14T23:59"),
    ("2026-11-10T08:00", "2026-11-09T08:00"),
])
def test_between_rejects_backwards_interval(start, end):
    with pytest.raises(ValueError):
        slaclock.business_minutes_between(moment(start), moment(end))


def test_between_calendar_span_limit():
    start = moment("2024-01-01T00:00")
    assert slaclock.business_minutes_between(start, moment("2025-01-01T00:00")) == 262 * 480
    assert slaclock.business_minutes_between(start, moment("2025-01-01T08:01")) == 262 * 480 + 1
    with pytest.raises(ValueError):
        slaclock.business_minutes_between(start, moment("2025-01-02T00:00"))
    # Calendar dates, not the number of complete elapsed 24-hour periods, bound the interval.
    with pytest.raises(ValueError):
        slaclock.business_minutes_between(moment("2024-01-01T23:59"), moment("2025-01-02T00:00"))


@pytest.mark.parametrize("day", range(7))
@pytest.mark.parametrize("hour,minute", [(7, 59), (8, 0), (12, 17), (15, 59), (16, 0)])
@pytest.mark.parametrize("duration", [0, 1, 59, 480, 481, 2401])
def test_due_date_and_elapsed_clock_agree(day, hour, minute, duration):
    start = datetime(2026, 11, 9, hour, minute, 31, 123) + timedelta(days=day)
    due = slaclock.add_business_minutes(start, duration)
    assert slaclock.business_minutes_between(start, due) == duration


@pytest.mark.parametrize(
    "priority,breached,base,reopened",
    [("P1", False, 1, 2), ("P1", True, 3, 3),
     ("P2", False, 1, 2), ("P2", True, 2, 3),
     ("P3", False, 0, 1), ("P3", True, 1, 2),
     ("P4", False, 0, 1), ("P4", True, 1, 2)],
)
def test_escalation_matrix_and_reopen_boundary(priority, breached, base, reopened):
    assert slaclock.escalation_tier(priority, breached, 0) == base
    assert slaclock.escalation_tier(priority, breached, 1) == base
    assert slaclock.escalation_tier(priority, breached, 2) == reopened
    assert slaclock.escalation_tier(priority, breached, 3) == reopened
    assert slaclock.escalation_tier(priority, breached, 100) == reopened


@pytest.mark.parametrize("priority", ["P1", "P2", "P3", "P4"])
@pytest.mark.parametrize("breached", [False, True])
def test_escalation_rejects_negative_reopens(priority, breached):
    with pytest.raises(ValueError):
        slaclock.escalation_tier(priority, breached, -1)


@pytest.mark.parametrize(
    "text,expected",
    [("1m", 1), ("59m", 59), ("60m", 60), ("90m", 90), ("1000m", 1000),
     ("1h", 60), ("4h", 240), ("24h", 1440), ("1h0m", 60), ("1h30m", 90),
     ("1h59m", 119), ("2d", 2880), ("1d4h", 1680), ("1d0h5m", 1445),
     ("1d59m", 1499), ("1d24h", 2880), ("2d3h4m", 3064),
     ("0h60m", 60), ("0d60m", 60), ("0d0h60m", 60), ("0d1h", 60),
     ("001h02m", 62), (" \t1h30m\n", 90)],
)
def test_parse_duration(text, expected):
    assert slaclock.parse_duration(text) == expected


@pytest.mark.parametrize("text", [
    "", " ", "0m", "0h", "0d", "0d0h0m", "0h0m", "1.5h", "-5m", "+5m",
    "1 h", "1h 5m", "1h\n5m", "30m1h", "1m1d", "1h1d", "1h2h", "1m2m",
    "1d2d", "H", "1H", "1D", "1M", "1", "m", "abc1h", "1hgarbage", "1h!",
    "1h60m", "1h61m", "1d60m", "1d0h60m", "0d1h60m", "1d1h60m",
])
def test_parse_invalid_duration(text):
    with pytest.raises(ValueError):
        slaclock.parse_duration(text)
