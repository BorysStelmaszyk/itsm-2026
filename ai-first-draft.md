---
lab3_first_draft:
  source: ai
  tool: "OpenAI Codex (GPT-5), desktop app, 2026-10-10"
  ladder: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
  verdict: refuted
  evidence: {p99_seconds: 0.1758, bucket: [0.1, 0.25], relative_width: 0.853}
lab3_flawed_ladder:
  verdict: refuted
  evidence: {p99_seconds: 0.1758, bucket: [0.04, 0.5], relative_width: 2.617}
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

Refuted. The published `load 3` measurement for login `borysstelmaszyk` gave p99 = 0.1758 s. The draft ladder
places that value in `(0.1, 0.25]`, whose relative width is `(0.25 - 0.1) / 0.1758 = 0.853`. This is well above
the M-11 limit of 0.20, so it does not resolve the measured p99.

## The draft alert rule

I kept the two-window `and` condition, the 14.4 fast-burn factor, the `/kb/search` route restriction, and the
service/SLO/severity labels because they express the intended fast-budget page without mixing other traffic into
the ratio. I changed the bad-event definition from every non-2xx response to 5xx responses so that it matches the
availability SLI in `slo.md`, used `for: 5m`, and added a 6 h / 30 min rule at burn rate 6 for a slower P2 signal.

## Verdict on the instructor's flawed ladder

Refuted. The same p99 = 0.1758 s falls in `(0.04, 0.5]`. Its relative width is
`(0.5 - 0.04) / 0.1758 = 2.617`, over thirteen times the permitted 0.20, so the ladder is blind to the slow mode.
