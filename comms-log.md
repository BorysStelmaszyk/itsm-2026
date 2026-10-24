---
lab4_comms:
  awareness: 2026-10-12T05:06:56Z
  detection: 2026-10-12T05:06:19Z
  classification: 2026-10-12T05:07:30Z
  nis2:
    early_warning_due: 2026-10-13T05:06:56Z
    notification_due: 2026-10-15T05:06:56Z
    notification_sent: 2026-10-12T09:00:00Z
    final_report_due: 2026-11-12T09:00:00Z
  ksc:
    early_warning_due: 2026-10-13T05:06:19Z
    notification_due: 2026-10-15T05:06:19Z
    notification_sent: 2026-10-12T09:00:00Z
    final_report_due: 2026-11-12T09:00:00Z
  dora:
    initial_due: 2026-10-12T09:07:30Z
    initial_sent: 2026-10-12T09:00:00Z
    intermediate_due: 2026-10-15T09:00:00Z
    intermediate_sent: 2026-10-15T08:30:00Z
    final_due: 2026-11-15T08:30:00Z
  log:
    - {at: 2026-10-12T09:00:00Z, to: CSIRT, what: NIS2 and KSC incident notification}
    - {at: 2026-10-12T09:00:00Z, to: financial supervisor, what: DORA initial notification}
    - {at: 2026-10-15T08:30:00Z, to: financial supervisor, what: DORA intermediate report}
---
<!-- ai-generated: 95% - Codex calculated the regulatory deadlines from the incident clocks; the student owns the chosen reporting instants -->

# Communications log: regulatory clocks

## The three instants defended

KSC detection is 2026-10-12T05:06:19Z because that is when `ShopCheckoutSlow` first fired and the monitoring system detected the incident. NIS2 awareness is 2026-10-12T05:06:56Z because acknowledgement of the P1 ticket is the first durable evidence that the on-call engineer had received the page and recognized the incident as significant. DORA classification is 2026-10-12T05:07:30Z, when the concurrent checkout, ad, and resource symptoms justified treating the event as a major ICT-related incident rather than a single transient alert.

## The log

At 09:00:00Z on 12 October, the CSIRT would receive the combined NIS2 early information and KSC notification, and the financial supervisor would receive the DORA initial notification. The same timestamp is before the NIS2, KSC, and DORA deadlines. At 08:30:00Z on 15 October, the financial supervisor would receive the DORA intermediate report containing the recovered service state, the three identified feature flags, the verified clocks, and the open corrective actions. Final NIS2 and KSC reports are due one UTC calendar month after their notification, while the DORA final report is due one UTC calendar month after the intermediate report.
