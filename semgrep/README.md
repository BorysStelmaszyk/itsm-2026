<!-- ai-generated: 100% - Codex documented the two service-specific review guards and their limits -->
# svcdesk Semgrep review guards

These are review guards, not assertions that every match is exploitable. They
record two security assumptions of this service and remain reporting-only.

| Rule | Existing code | Review decision |
|---|---|---|
| `svcdesk-review-dynamic-ticket-sql` | `TicketStore.list` in `src/svcdesk/storage.py` | Accept the current query: interpolated fragments are assembled exclusively from fixed SQL strings, while request filter values are passed as SQLite parameters. Review any change to that boundary. |
| `svcdesk-review-test-clock-switch` | `request_now` in `src/svcdesk/clock.py` | Accept for the course's deterministic SLA tests: the code defaults to disabled and checks the environment switch before using the request header. Course Compose intentionally enables it; production configuration must leave it disabled. |

The SQL guard is scoped to `TicketStore`; it does not claim to detect all SQL
injection. Its fixtures distinguish interpolated queries from parameterized
queries, logging, and another class. Both the accepted fixed-fragment query and
an unsafe direct interpolation need review, so both are positive examples.

The clock guard deliberately reports both safe and unsafe defaults for the exact
`SVCDESK_TEST_CLOCK` variable. A match asks a reviewer to check the default, the
header gate, and deployment configuration. Ordinary database/upstream settings
and similarly named environment variables are negative examples. Neither rule
proves dataflow or whether a production deployment is secure.

From the repository root, use the course-pinned image:

```powershell
docker run --rm --network none -v "${PWD}:/work:ro" -w /work semgrep/semgrep:1.178.0 semgrep --test semgrep/
docker run --rm --network none -v "${PWD}:/work:ro" -w /work semgrep/semgrep:1.178.0 semgrep scan --config semgrep/rules.yml --metrics=off src/
```

The first command checks the annotated true and false positives in `rules.py`.
The second must report each rule in the existing service code (P-31).
