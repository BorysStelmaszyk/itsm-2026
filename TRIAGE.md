---
lab5_triage:
  image: null
  sarif_receipt: null
---
<!-- ai-generated: 100% - Codex drafted decisions from inspected code and local scanner output; CI evidence is pending -->
# Triage

Status: local preparation. The image digest and SARIF receipt will be recorded only after the
main workflow publishes its attestations and the course bot receipts the unchanged canary SARIF.
The table will then be reconciled against every finding on our own code in that captured SARIF.

| Tool | Rule | Decision | Reason |
|---|---|---|---|
| gitleaks | generic-api-key | ignore | At k8s/evidence.json:8066, Helm's checksum/secret annotation contains a SHA-256 rollout checksum, not a usable credential. Preserve the earlier lab evidence and ignore only this file/rule/line fingerprint in .gitleaksignore. |
| semgrep | dockerfile.security.missing-user.missing-user | accept | The laboratory container runs as root and uses a named SQLite data volume created by earlier labs. Accept this only in the isolated course environment through 2026-11-28; before deployment migrate existing volume ownership and introduce an unprivileged runtime user. |
| semgrep | python.sqlalchemy.security.sqlalchemy-execute-raw-query.sqlalchemy-execute-raw-query | accept | In src/svcdesk/storage.py:120 this is a false positive: sqlite3 receives fixed SQL fragments and bound caller values, not SQLAlchemy raw user SQL. In semgrep/rules.py:9,13,31 the expressions are deliberate, nonexecuted positive/negative scanner fixtures; retain these only as rule tests. Review on any fixture/query change and before deployment. |
| semgrep | python.lang.security.audit.formatted-sql-query.formatted-sql-query | accept | semgrep/rules.py:13,31 contains deliberate interpolation patterns used as static test fixtures for the custom rule. This file is never imported by svcdesk or executed by the rule tests; retain as test-only evidence and review before any change to its usage. |
| semgrep | semgrep.svcdesk-review-dynamic-ticket-sql | accept | The custom review guard finds src/svcdesk/storage.py:120. SQL fragments come only from fixed strings and all caller values use SQLite bound parameters. Retain this guard to review that invariant whenever this query changes; re-evaluate before any external deployment. |
| semgrep | semgrep.svcdesk-review-test-clock-switch | accept | The custom guard finds src/svcdesk/clock.py:40. SVCDESK_TEST_CLOCK defaults to 0 and only the laboratory Compose environment enables deterministic request time. Keep it for the course contract and require it disabled before external deployment. |

## Image hardening

The base is pinned to python:3.13-slim@sha256:e48f59cdba69a3cbd9ed2cf0f348d90d45a8d350d98134cf1070bc106ee9ed90.
The build refreshes Debian packages and removes pip after installing the application dependencies:
pip and its vendored libraries are not needed by the running service. No vulnerability ignore is
currently configured. Local scans are preparation evidence, not the attested canary measurements.

## Bake-off

Pending the canary run, SARIF receipt and revealed labels. The final comparison must use those
captured files and their actual TP, FP, FN, precision, recall and F1; the published practice set
cannot substitute for this measurement. No final bakeoff.json has been fabricated.
