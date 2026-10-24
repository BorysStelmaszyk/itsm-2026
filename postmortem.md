---
lab4_postmortem:
  ticket: "3ba75e92-1b55-483b-a69e-6097c02b182c"
  detecting_alert: ShopCheckoutSlow
  onset: 2026-10-12T05:01:00Z
  detection: 2026-10-12T05:06:19Z
  acknowledgement: 2026-10-12T05:06:56Z
  recovery: 2026-10-12T05:08:19Z
  mttd_seconds: 319
  mtta_seconds: 37
  mttr_seconds: 439
  identified_flags: [adFailure, intlShippingSlowdown, emailMemoryLeak]
---
<!-- ai-generated: 90% - Codex drafted the postmortem from the verified snapshot queries; the student owns the conclusions and actions -->

# Postmortem: checkout latency during concurrent feature-flag failures

## Date

The incident occurred on 12 October 2026, and this postmortem was prepared after the recorded telemetry and ticket were verified.

## Authors

Borys Stelmaszyk prepared this record in the role of the on-call engineer responsible for incident coordination and review.

## Status

The postmortem is complete, service has recovered, and the corrective action items remain open and in progress.

## Summary

At 05:01:00Z three feature flags began degrading the shop. Checkout became slow, ad requests began failing, and email memory grew. The `ShopCheckoutSlow` alert fired at 05:06:19Z, the P1 incident was acknowledged 37 seconds later, and the detecting alert recovered at 05:08:19Z after the flags were disabled.

## Impact

Customers experienced multi-second checkout responses for 439 seconds from onset to alert recovery. At 05:06:30Z checkout p99 was approximately 8,800 ms, compared with approximately 50 ms on the healthy baseline. This was measured with `histogram_quantile(0.99, sum by (le) (rate(traces_span_metrics_duration_milliseconds_bucket{service_name="checkout",span_kind="SPAN_KIND_SERVER"}[5m])))`. A concurrent ad degradation produced an approximately 4.76% server-error ratio, measured as the five-minute error rate divided by all ad server calls. Email container memory was 1.448 times its value ten minutes earlier, which increased the risk of an out-of-memory restart even though checkout latency was the paging symptom.

## Root Causes

Three independently seeded feature flags were active. `intlShippingSlowdown` introduced multi-second shipping tail latency and propagated it into checkout; shipping p99 reached approximately 8.1 seconds. `adFailure` caused ad server errors that also surfaced through frontend calls. `emailMemoryLeak` increased email container memory by about 44.8% over ten minutes. The common control-plane weakness was that hazardous flag variants could be activated together without an automatic symptom-based rollback.

## Trigger

The trigger was the scheduled activation of the seeded fault at 2026-10-12T05:01:00Z after the healthy baseline. No deployment or operator action changed the application binaries at that instant.

## Resolution

The incident was mitigated by returning `intlShippingSlowdown`, `adFailure`, and `emailMemoryLeak` to their safe `off` variants. The response prioritized the shipping flag because it matched the customer-facing checkout page, followed by the ad and email faults. The recording does not expose individual flag-change timestamps, so their exact transitions cannot be reconstructed independently; all mitigation occurred after acknowledgement and before the detecting alert ended at 05:08:19Z.

## Detection

Prometheus detected the incident through `ShopCheckoutSlow` at 05:06:19Z, 319 seconds after onset. The alert measured a customer-visible symptom rather than an injector signal. Without this alert, the likely detection path would have been synthetic checkout monitoring or customer reports, both slower and less precise.

## Action Items

| Action Item | Type | Owner | Bug |
|---|---|---|---|
| Add a checkout dependency-latency panel and an alert that isolates shipping tail latency before the end-to-end window expires. | mitigate | Observability team | ITSM-42 |
| Add guardrails and automatic rollback for hazardous feature-flag combinations when checkout latency or error objectives are breached. | prevent | Platform team | ITSM-43 |
| Add PromQL linting and counter-semantics examples to the AI investigator workflow so invalid aggregation syntax and raw-counter conclusions are rejected. | process | SRE team | ITSM-44 |

## Lessons Learned

### What went well

The symptom alert paged on customer impact, the P1 ticket was acknowledged within 37 seconds, and the immutable snapshot preserved enough evidence to distinguish all three concurrent faults.

### What went wrong

The five-minute metric window delayed detection, concurrent flag failures obscured the causal chain, and the recorded AI investigator spent most of its tool budget on invalid PromQL before drawing conclusions from raw counters.

### Where we got lucky

The shipping slowdown was visible in both shipping and checkout histograms, the email leak had not yet caused an out-of-memory restart, and the ad failure did not prevent checkout recovery.

## Timeline

- 05:00:00Z — The last full minute before onset remained healthy; the checkout latency comparison was below the paging threshold.
- 05:01:00Z — The sealed fault became active; this is the authoritative onset in `seeded_fault_active`.
- 05:06:19Z — `ShopCheckoutSlow` began its first firing run and detected the incident.
- 05:06:36Z — P1 ticket `3ba75e92-1b55-483b-a69e-6097c02b182c` was created for slow checkout.
- 05:06:56Z — The on-call engineer acknowledged the P1 ticket and began mitigation.
- 05:07:00Z — Telemetry review isolated shipping tail latency, ad errors, and email memory growth; the three corresponding flags were returned to safe variants.
- 05:08:19Z — The detecting alert's first firing run ended, marking recovery.

## Supporting information

The immutable evidence is `incident/tsdb-snapshot.tar.gz` and `incident/ticket.json`; `itsmlab incident 4` recomputed every clock above. The fault identification used server error rates by `service_name`, p99 latency from `traces_span_metrics_duration_milliseconds_bucket`, and the ratio of `container_memory_usage_total_bytes` to its ten-minute offset. `ai-rca-eval.json` records the official investigator's seven hypotheses, while `ai-rca-eval-2.json` records the independent comparison. The latter's S1–S3 predictions were each true during the incident and false at 04:56:00Z.

## Problem record

- Incident record: P1 ticket 3ba75e92-1b55-483b-a69e-6097c02b182c restored service and can close at recovery.
- Root cause: Unsafe feature-flag variants could activate concurrently without dependency-aware guardrails or automatic rollback.
- Known error: The shop remains vulnerable to the same flag combination until the preventive control in ITSM-43 is deployed.
- Workaround: Return the implicated flags to `off`, prioritizing the flag matching the customer-facing symptom, and watch the detecting alert resolve.
