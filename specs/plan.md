<!-- ai-generated: 100% - Codex translated the accepted Lab 1 specification and student decisions into an implementation plan -->
# Lab 1 implementation plan

## Chosen design

- Python 3.13 with FastAPI and Uvicorn.
- SQLite stored at `SVCDESK_DB`, defaulting to `/data/svcdesk.db` in the container.
- A small package under `src/svcdesk/` separates HTTP handling, time/SLA calculation, and persistence.
- All timestamps are stored as UTC RFC 3339 strings and converted to aware `datetime` values for calculations.
- C1 is `wallclock`, C2 is `immutable`, and C3 is `vip`.

## Delivery sequence

1. Add pinned runtime dependencies and a production Dockerfile.
2. Implement ticket validation, priority calculation, test-clock parsing, and JSON error envelopes.
3. Implement SQLite persistence and ticket retrieval/list filtering.
4. Implement the state machine and seven-day reopen boundary.
5. Implement wall-clock and Europe/Warsaw business-hours SLA calculations.
6. Implement SLA breach and pause reporting.
7. Run focused local tests, build with Compose, and run `itsmlab verify 1` until every Core check passes.

## Risk controls

- Use timezone-aware datetimes only; naive test-clock values are rejected.
- Keep the business window half-open and preserve the 16:00 tie rule.
- Perform each state transition in one SQLite transaction.
- Ignore unknown and server-owned request fields without copying them into stored records.
- Keep the container independent of network access after its image has been built.
