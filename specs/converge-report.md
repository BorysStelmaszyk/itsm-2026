<!-- ai-generated: 100% - Codex compared the accepted specification, decisions, implementation plan, and published checks -->
# Lab 1 specification convergence report

## Scope

This review compares the student specification with the product requirements, the exact API contract, the
published Tier A checks, and the three decisions selected before implementation. The purpose is to identify gaps or
contradictions that could make a locally plausible service fail the stated customer outcome.

## Findings and resolutions

- R-01 and R-02 converge with the Compose contract: the service listens on port 8080 and exposes the required JSON
  health response. The enabled healthcheck uses the service itself and does not introduce a runtime dependency.
- R-05 and R-06 conflict by design. Decision C3 resolves the conflict as `vip`: the matrix is evaluated first and a
  VIP result of P3 or P4 is elevated to P2. Client-supplied priority remains ignored.
- R-09 and R-10 conflict for closed tickets. Decision C2 resolves the conflict as `immutable`; resolved tickets keep
  the seven-day reopen window, but closed tickets require a new related ticket.
- R-13 and R-14 conflict for P1. Decision C1 resolves the conflict as `wallclock`; both P1 targets run continuously,
  while P2-P4 continue to use DST-aware Europe/Warsaw business hours.
- R-16 is reflected explicitly in the breach rules: equality is not a breach, reopened tickets become unresolved
  again, and only open tickets with a business-hours resolution clock can be paused.
- R-21 is represented as a request-scoped test clock. No monotonic relationship is assumed between separate
  requests, preventing fixture order from changing behavior.
- R-22 and R-23 converge on a named SQLite volume, no host-path bind mounts, build-time dependency installation,
  and persistence across a service-container restart.

## Result

No unresolved contradictions remain. The acceptance criteria cover every fixed behavior and link the three
deliberate conflicts to `DECISIONS.md`. Implementation is ready for Tier A verification, with receipt ancestry left
to Tier B as designed.
