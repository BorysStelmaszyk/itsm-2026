---
lab3_slo:
  service: svcdesk
  route: /kb/search
  window: 30d
  slis:
    availability:
      objective: 0.99
      good: 'sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search", http_response_status_code!~"5.."}[5m]))'
      valid: 'sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search"}[5m]))'
      error_budget: {fraction: 0.01, minutes: 432}
    latency:
      objective: 0.95
      threshold_seconds: 0.05
      good: 'sum(rate(http_server_request_duration_seconds_bucket{job="svcdesk", http_route="/kb/search", le="0.05"}[5m]))'
      valid: 'sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search"}[5m]))'
      error_budget: {fraction: 0.05, minutes: 2160}
  alerts:
    - {alert: KbSearchAvailabilityBurnFast, sli: availability, burn_rate: 14.4, long_window: 1h, short_window: 5m}
    - {alert: KbSearchAvailabilityBurnSlow, sli: availability, burn_rate: 6, long_window: 6h, short_window: 30m}
---
<!-- ai-generated: 75% - Codex drafted the structure and arithmetic; the student owns the objectives and response policy -->

# Knowledge-base search SLO

This SLO applies only to `GET /kb/search` and uses a rolling 30-day window. The availability objective is 99%:
a response is good unless its status is 5xx, and every response on the route is valid traffic. The resulting 1%
error budget is 432 minutes out of 43,200 minutes.

The latency objective is that 95% of requests complete within 50 ms. The threshold is an explicit histogram
boundary, so the SLI counts observations rather than interpolating them. The measured distribution had p95 =
47.0 ms and p99 = 175.8 ms; 50 ms therefore represents the normal mode while leaving the narrow slow mode visible
in the tailored 150-200 ms buckets. The 5% latency budget is 2,160 minutes per 30 days.

The fast availability alert combines 1 h and 5 min windows at burn rate 14.4 and pages as P1 after five minutes;
it is intended for rapid, sustained exhaustion that needs immediate response. The slow alert combines 6 h and
30 min windows at burn rate 6 and sends a P2 signal. This avoids paging on brief noise while still detecting a
steadier loss of availability before the monthly budget is consumed.

The measured p99 may move slightly on another host. Around the observed 175.8 ms, the final ladder includes
boundaries every 10 ms from 150 through 200 ms. It therefore covers at least the requested +/-10% band, while
each bucket in that band is only 10 ms wide, below 20% of the band's 158.2 ms lower end.
