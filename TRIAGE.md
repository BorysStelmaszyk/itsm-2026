---
lab5_triage:
  image: ghcr.io/borysstelmaszyk/itsm-2026@sha256:46f423b347da9c8785c608f416927980cf3ee943a55a431da1fbe11be82a4ffb
  sarif_receipt: 372
---
<!-- ai-generated: 100% - Codex drafted decisions from inspected code and local scanner output; CI evidence is pending -->
# Triage

The image digest is from the successful `main` image job. The unchanged canary SARIF was
captured in `bakeoff/sarif/` and submitted for the course receipt in issue #372. The table
covers the three distinct Semgrep rules reported outside `lab5-canary/`, plus the local
gitleaks ignore and the two service-specific review guards.

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

The matrix counts nine labelled defects in the canary set, using only the unchanged SARIF files
receipted in issue #372 and the subsequently revealed labels. I would keep Trivy as a gate for
dependency manifests and the built image: it found 3 defects, with 1 false positive and 6 false
negatives (precision 0.7500, recall 0.3333, F1 0.4615). I would also keep gitleaks as a secret
gate because a real credential is costly to publish, while investigating each alert before any
ignore. On this set gitleaks has 2 true positives, 1 false positive and 7 false negatives
(precision 0.6667, recall 0.2222, F1 0.3333). Those two gates are complementary: a dependency
pin and a hard-coded credential need different detectors.

Semgrep has the largest recall here: 4 true positives, 2 false positives and 5 false negatives
(precision 0.6667, recall 0.4444, F1 0.5333). I would keep it reporting rather than blocking:
its two unmatched findings show that a broad code rule still needs human review of context.
Grype and OSV-Scanner each found the two vulnerable dependency defects with no unmatched
findings (precision 1.0000, recall 0.2222, F1 0.3636 for each). Their clean precision does not
make them general code or secret detectors. I would retain both as independent reporting
cross-checks and promote a finding to a gate only after testing how often they alert incorrectly
on the live service. The false negatives across tools show why passing one scanner cannot certify
the whole repository. These are measurements on deliberately seeded defects; such examples are
easier for detectors than naturally occurring faults, so the observed recall is an upper bound
for real work rather than a performance promise. There is no true-negative cell because the
labelled unit is a defect, not every line of harmless code.
