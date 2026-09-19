<!-- ai-generated: 100% - drafted by Codex from the supplied course documents and reviewed by the student -->
# Lab 1 specification: `svcdesk`

## 1. Status and source precedence

This document specifies the first version of `svcdesk`, a small HTTP service-desk API for creating tickets,
controlling their lifecycle, calculating priority and SLA deadlines, and reporting SLA status.

The source documents are:

1. [`REQUIREMENTS.md`](../course-package/lab1/REQUIREMENTS.md), which supplies the business requirements R-01 to
   R-25;
2. [`API.md`](../course-package/lab1/API.md), which is authoritative for paths, fields, status codes, time
   calculations, and other interface details;
3. [`CHECKS.md`](../course-package/lab1/CHECKS.md), which supplies the executable acceptance criteria.

When the sources differ in precision, `API.md` governs. Three deliberate contradictions are resolved as decisions
C1, C2, and C3 in section 4. Their selected values are recorded in the repository-root `DECISIONS.md`, must be
reflected by the implementation, and must be verified for consistency before submission.

## 2. Purpose and scope

The service replaces spreadsheet- and inbox-based ticket handling for an internal service desk. It must enable
agents, monitoring, and future integrations to:

- create and retrieve tickets through JSON over HTTP;
- calculate priority rather than trusting a client-supplied value;
- enforce a defined ticket state machine;
- calculate acknowledgement and resolution deadlines;
- determine whether SLA targets have been breached and whether a clock is paused;
- retain tickets when the service container restarts.

Lab 1 has no authentication, authorization, pagination, public-holiday calendar, or validation of whether a
`related_to` identifier exists. These concerns are outside the stated contract.

## 3. Runtime contract

- The service exposes HTTP on container port `8080` and uses JSON request and response bodies.
- Every response has media type `application/json`.
- `GET /health` becomes available within 120 seconds of `docker compose up --wait svcdesk` and returns status 200
  with at least `{"status":"ok","service":"svcdesk"}`.
- The root Compose file defines a service named exactly `svcdesk` with a `build:` context inside the repository.
- Compose sets `SVCDESK_TEST_CLOCK: "1"` for the service.
- No service uses a host-path bind mount, directly or through an override, environment expansion, or volume driver
  option. Named volumes and `tmpfs` are permitted.
- Dependencies are installed while images are built. The running images require no external network access.
- Tickets survive a restart of the `svcdesk` container; a named volume may be used for persistent storage.

## 4. Decision register

The product requirements contain three intentional conflicts. Either documented outcome would be conformant, but
the student selected the following behaviors before implementation.

| decision | conflicting requirements | selected value | required behavior |
|---|---|---|---|
| C1: P1 SLA clock | R-13 pauses all clocks outside business hours; R-14 makes P1 continuous | `wallclock` | Both P1 targets use continuous elapsed time. P2-P4 use business hours. |
| C2: reopening closed tickets | R-09 makes a closed ticket immutable; R-10 permits a closed ticket to reopen for seven days | `immutable` | A closed ticket always rejects reopen with 409; a resolved ticket may reopen within seven days. |
| C3: VIP priority | R-05 makes the matrix the only priority input; R-06 raises VIP tickets to at least P2 | `vip` | A VIP ticket calculated as P3 or P4 is raised to P2; P1 and P2 remain unchanged. |

The checker identifies these outcomes through checks L1-CORE-2.41, L1-CORE-2.35, and L1-CORE-2.46 respectively.
The declared values in `DECISIONS.md` must equal the observed values.

## 5. HTTP interface

| method and path | success response | failure behavior |
|---|---|---|
| `GET /health` | 200 health object | - |
| `POST /tickets` | 201 and the complete created Ticket | invalid input: 400 or 422 with top-level `error` |
| `GET /tickets` | 200 and a JSON array of every matching Ticket | - |
| `GET /tickets/{id}` | 200 and the matching Ticket | unknown id: 404 with top-level `error` |
| `GET /tickets/{id}/sla` | 200 and the SLA status object | unknown id: 404 with top-level `error` |
| `POST /tickets/{id}/ack` | 200 and the updated Ticket | invalid transition: 409; unknown id: 404 |
| `POST /tickets/{id}/start` | 200 and the updated Ticket | invalid transition: 409; unknown id: 404 |
| `POST /tickets/{id}/resolve` | 200 and the updated Ticket | invalid transition: 409; unknown id: 404 |
| `POST /tickets/{id}/close` | 200 and the updated Ticket | invalid transition: 409; unknown id: 404 |
| `POST /tickets/{id}/reopen` | 200 and the updated Ticket | invalid state/window: 409; unknown id: 404 |

An unknown path returns 404 with a JSON body. A wrong method on a known path may return 404 or 405.

`GET /tickets` supports optional exact-match query parameters `state` and `priority`. It returns all matching
tickets in one array, in any order, without pagination.

## 6. Ticket model

A Ticket contains:

| field | type and constraints | ownership/default |
|---|---|---|
| `id` | non-empty, unique, opaque string | server-generated |
| `title` | string, 1-200 characters | required from client |
| `description` | string, 0-4000 characters | optional; default `""` |
| `reporter.name` | string, 1-100 characters | required from client |
| `reporter.email` | string or null | optional; default null |
| `reporter.vip` | boolean | optional; default false |
| `impact` | integer 1, 2, or 3 | required from client |
| `urgency` | integer 1, 2, or 3 | required from client |
| `priority` | `P1`, `P2`, `P3`, or `P4` | server-calculated |
| `state` | `new`, `acknowledged`, `in_progress`, `resolved`, or `closed` | server-managed; initially `new` |
| `created_at` | RFC 3339 instant | set to `now` at creation |
| `acknowledged_at` | RFC 3339 instant or null | initially null |
| `resolved_at` | RFC 3339 instant or null | initially null |
| `closed_at` | RFC 3339 instant or null | initially null |
| `related_to` | string or null | optional; identifier existence is not validated in Lab 1 |
| `sla.ack_due_at` | RFC 3339 instant | server-calculated at creation |
| `sla.resolve_due_at` | RFC 3339 instant | server-calculated at creation |

The service reports timestamps in UTC with a `Z` suffix. Instant comparisons are chronological, not string-based.

Client-supplied server fields (`id`, `priority`, `state`, event timestamps, and `sla`) are ignored. Unknown input
fields are also ignored. They must not turn an otherwise valid request into an error.

## 7. Validation and errors

- A missing or empty title, title longer than 200 characters, description longer than 4000 characters, missing or
  empty reporter name, or invalid impact/urgency is rejected with status 400 or 422.
- Impact and urgency must be integers in the closed range 1-3. Values such as `5` and `"high"` are invalid.
- Validation responses contain a top-level `error` object.
- Unknown ticket identifiers return 404 with a top-level `error` object.
- Invalid state transitions and expired reopen attempts return 409 with a top-level `error` object.
- Stable error codes such as `validation`, `not_found`, `invalid_transition`, `reopen_window_expired`, and
  `ticket_closed` are recommended, although Lab 1 only requires the status and top-level `error` object.

## 8. Priority calculation

Every ticket first receives priority from the following matrix:

| impact \ urgency | 1 | 2 | 3 |
|---|---|---|---|
| **1** | P1 | P2 | P3 |
| **2** | P2 | P3 | P4 |
| **3** | P3 | P4 | P4 |

After the matrix calculation, C3 determines VIP treatment:

- `matrix`: retain the matrix result; store `reporter.vip` without using it in priority calculation;
- `vip`: raise a VIP ticket calculated as P3 or P4 to P2; leave P1 and P2 unchanged.

A client-provided `priority` field is always ignored. Under either C3 outcome, a VIP ticket with impact 1 and
urgency 1 remains P1.

## 9. State machine and reopening

| action | required state | resulting state | timestamp effect |
|---|---|---|---|
| acknowledge | `new` | `acknowledged` | set `acknowledged_at = now` |
| start | `acknowledged` | `in_progress` | none |
| resolve | `in_progress` | `resolved` | set `resolved_at = now` |
| close | `resolved` | `closed` | set `closed_at = now` |
| reopen | `resolved`, and optionally `closed` under C2 | `in_progress` | clear `resolved_at` and `closed_at` |

All transitions not listed above return 409. In particular, the service rejects acknowledgement twice, starting a
new ticket, resolving a new or merely acknowledged ticket, closing a new ticket, and reopening a new ticket.

Reopening a resolved ticket is permitted while `now <= resolved_at + 7 days`. It is rejected after that boundary.
C2 controls closed tickets:

- `reopen`: a closed ticket may reopen while `now <= closed_at + 7 days`;
- `immutable`: every reopen attempt on a closed ticket returns 409, and continuing work requires a new ticket whose
  `related_to` refers to the closed ticket.

Reopening never changes the original SLA due instants. A reopened ticket is once again unresolved for breach
calculation.

## 10. SLA targets and due instants

Targets are measured from `created_at`:

| priority | acknowledgement target | resolution target |
|---|---|---|
| P1 | 15 minutes | 4 hours |
| P2 | 1 hour | 8 hours |
| P3 | 4 hours | 24 hours |
| P4 | 8 hours | 72 hours |

A wall-clock due instant is `created_at + target`.

A business-hours due instant counts only Monday-Friday during the half-open interval
`[08:00:00, 16:00:00)` in the `Europe/Warsaw` time zone. The calculation is DST-aware, but public holidays are
treated as normal business days. If creation occurs outside a business window, counting starts at the next opening.
If a target ends exactly at 16:00, it is due at 16:00 that day rather than 08:00 the next business day. The result is
converted back to a UTC instant.

P2-P4 always use the business-hours clock. C1 controls both P1 targets:

- `wallclock`: P1 acknowledgement and resolution targets both use wall-clock time;
- `business`: P1 acknowledgement and resolution targets both use business hours.

A mixed P1 outcome is invalid. The implementation image must include IANA time-zone data for `Europe/Warsaw`.

The following vectors are normative:

| id | priority | `created_at` | wall-clock ack/resolve | business-hours ack/resolve |
|---|---|---|---|---|
| T1 | P1 | `2026-10-14T10:00:00Z` | `2026-10-14T10:15:00Z` / `2026-10-14T14:00:00Z` | same as wall-clock |
| T2 | P3 | `2026-10-16T13:30:00Z` | `2026-10-16T17:30:00Z` / `2026-10-17T13:30:00Z` | `2026-10-19T09:30:00Z` / `2026-10-21T13:30:00Z` |
| T3 | P1 | `2026-10-16T15:00:00Z` | `2026-10-16T15:15:00Z` / `2026-10-16T19:00:00Z` | `2026-10-19T06:15:00Z` / `2026-10-19T10:00:00Z` |
| T4 | P2 | `2026-10-17T10:00:00Z` | `2026-10-17T11:00:00Z` / `2026-10-17T18:00:00Z` | `2026-10-19T07:00:00Z` / `2026-10-19T14:00:00Z` |
| T5 | P4 | `2027-01-14T14:30:00Z` | `2027-01-14T22:30:00Z` / `2027-01-17T14:30:00Z` | `2027-01-15T14:30:00Z` / `2027-01-27T14:30:00Z` |
| T6 | P1 | `2027-01-15T15:50:00Z` | `2027-01-15T16:05:00Z` / `2027-01-15T19:50:00Z` | `2027-01-18T07:15:00Z` / `2027-01-18T11:00:00Z` |
| T7 | P2 | `2026-10-14T10:00:00Z` | `2026-10-14T11:00:00Z` / `2026-10-14T18:00:00Z` | `2026-10-14T11:00:00Z` / `2026-10-15T10:00:00Z` |
| T8 | P3 | `2026-10-23T13:00:00Z` | `2026-10-23T17:00:00Z` / `2026-10-24T13:00:00Z` | `2026-10-26T10:00:00Z` / `2026-10-28T14:00:00Z` |

## 11. SLA status

`GET /tickets/{id}/sla` returns:

```text
{
  priority,
  ack_due_at,
  resolve_due_at,
  ack_breached: boolean,
  resolve_breached: boolean,
  paused: boolean
}
```

At the request's `now`:

- `ack_breached` is true when acknowledgement has not occurred and `now > ack_due_at`, or when
  `acknowledged_at > ack_due_at`;
- `resolve_breached` is true when resolution has not occurred and `now > resolve_due_at`, or when
  `resolved_at > resolve_due_at`;
- equality with a due instant is not a breach;
- `paused` is true only when the ticket is neither resolved nor closed, the resolution target uses business hours,
  and `now` is outside a business window;
- a wall-clock ticket is never paused.

## 12. Controllable test clock

When `SVCDESK_TEST_CLOCK` equals `1` or `true`, each request may contain an `X-Test-Clock` header carrying an RFC
3339 instant with an offset. That instant becomes `now` for that request only and controls event timestamps, breach
status, pause status, and reopen-window evaluation.

- A malformed or offset-free header returns 400 or 422.
- Without the header, the service uses real UTC time.
- When the environment variable is disabled, the header is ignored.
- Request clocks are independent: the service does not require monotonic time and must not reject a request because
  its clock precedes a timestamp stored by another request.
- The header has no effect on `GET /tickets` or `GET /tickets/{id}`, whose response fields are not time-dependent.

## 13. Acceptance criteria

The implementation is acceptable when all of the following hold:

1. The Compose project builds the repository's `svcdesk` image, contains no bind mounts, starts successfully, and
   serves `/health` within 120 seconds.
2. Ticket creation, retrieval, listing, filtering, validation, unique identifiers, and JSON errors conform to
   sections 5-8.
3. Every allowed state transition succeeds, and every forbidden transition tested by the published checker returns
   409.
4. Reopen boundaries are inclusive at seven days and exclusive after seven days, subject to C2 for closed tickets.
5. SLA due instants reproduce the normative vectors and the selected C1 behavior.
6. Breach and pause results follow section 11, including equality not being a breach.
7. VIP priority follows the selected C3 behavior, and client-supplied priority is ignored.
8. The test clock is request-scoped and accepts every valid checker timestamp while rejecting malformed timestamps.
9. `DECISIONS.md` declares admissible C1-C3 values, contains the required reasoning fields, and matches the running
   service.
10. The specification receipt predates every commit that adds an implementation file under `src/`.

The published Tier A checker is the executable acceptance suite. Locally, L1-CORE-5 is expected to report `skip`
because receipt ancestry is checked only by the grader.

## 14. Requirements traceability

| specification area | source requirements |
|---|---|
| runtime and health | R-01, R-02, R-22, R-24 |
| ticket model and identity | R-03, R-17, R-18 |
| priority and VIP decision | R-04, R-05, R-06 |
| lifecycle and reopen decision | R-07, R-08, R-09, R-10, R-11 |
| SLA deadlines and decision C1 | R-12, R-13, R-14 |
| SLA reporting | R-15, R-16 |
| listing and filtering | R-19 |
| validation and ignored fields | R-20 |
| controllable clock | R-21 |
| persistence | R-23 |
| unknown resources | R-25 |

## 15. Specification gate

Before implementation files are added under `src/`:

1. a student reviews this specification and corrects any misunderstanding;
2. this file is committed and pushed to `main`;
3. the `specs` receipt is requested and accepted by the course bot;
4. C1, C2, and C3 are resolved as `wallclock`, `immutable`, and `vip`, documented in `DECISIONS.md`, and reflected
   in the implementation plan.
