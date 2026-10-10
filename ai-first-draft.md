---
lab3_first_draft:
  source: ai
  tool: "OpenAI Codex (GPT-5), desktop app, 2026-10-10"
  ladder: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
  verdict: TODO
  evidence: {p99_seconds: TODO, bucket: [TODO, TODO], relative_width: TODO}
lab3_flawed_ladder:
  verdict: refuted
  evidence: {p99_seconds: TODO, bucket: [TODO, TODO], relative_width: TODO}
---
<!-- ai-generated: 70% - the assistant answer is verbatim; the student will own the measured verdicts and arithmetic -->

# The assistant's first draft, and two verdicts

## Prompt

Before I measure my service, propose histogram bucket boundaries in seconds for the RED latency histogram of
`GET /kb/search`, and propose one Prometheus multiwindow burn-rate alert rule for its availability SLO. I do not
yet know the latency distribution. Keep the ladder to at most 30 finite boundaries and use only the labels
`http_request_method`, `http_route`, and `http_response_status_code`.

## Answer

Because no measurements are available yet, start with a conventional wide-range latency ladder in seconds:

`[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]`

Treat it as a provisional ladder: after measuring p99, add tighter boundaries around the observed slow mode and
keep the SLO threshold on an explicit bucket boundary.

For a 99% availability objective, a fast-burn alert can require both a one-hour and a five-minute error ratio to
exceed 14.4 times the 1% error budget, with `for: 2m`. Define errors as non-2xx responses for `GET /kb/search`.
The PromQL shape is:

```promql
(
  sum(rate(http_server_request_duration_seconds_count{http_request_method="GET",http_route="/kb/search",http_response_status_code!~"2.."}[1h]))
  /
  sum(rate(http_server_request_duration_seconds_count{http_request_method="GET",http_route="/kb/search"}[1h]))
) > (14.4 * 0.01)
and
(
  sum(rate(http_server_request_duration_seconds_count{http_request_method="GET",http_route="/kb/search",http_response_status_code!~"2.."}[5m]))
  /
  sum(rate(http_server_request_duration_seconds_count{http_request_method="GET",http_route="/kb/search"}[5m]))
) > (14.4 * 0.01)
```

Attach labels such as `service: svcdesk`, `slo: availability`, and `severity: P1`. Add a slower, lower-burn alert
after choosing the SLO window and operational response policy.

## Verdict on the draft ladder

TODO after the first published measurement.

## The draft alert rule

TODO after the SLO and final multiwindow alert policy are defined.

## Verdict on the instructor's flawed ladder

TODO after the first published measurement.
