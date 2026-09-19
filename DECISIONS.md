---
svcdesk_decisions:
  C1: wallclock      # wallclock | business
  C2: immutable      # reopen | immutable
  C3: vip            # matrix | vip
---
<!-- ai-generated: 90% - the student selected C1-C3 and approved the explanations drafted by Codex -->

# Decisions

## C1 - SLA clock for P1

**Decision:** P1 acknowledgement and resolution targets use the wall-clock continuously, including nights,
weekends, and time outside the normal service-desk business window.

**Rejected alternative:** We rejected the business-hours clock for P1, which would pause both targets outside
Monday-Friday 08:00-16:00 in the Europe/Warsaw time zone.

**Reason:** P1 represents an organisation-wide interruption where work has stopped. Waiting for the next business
window would hide the real urgency and could postpone the response to a critical outage for an entire weekend.

**Service owner:** The Service Desk Product Owner signs off this decision because that role owns the SLA policy,
the support model, and the escalation expectations for critical incidents.

**Customer outcome:** Reporters receive a deadline that reflects continuous attention to critical incidents, and
the organisation can see immediately when an after-hours P1 response is late.

## C2 - Closed tickets and reopening

**Decision:** Closed tickets are immutable. Reopen requests for a closed ticket return 409 regardless of its age;
continued work is represented by a new ticket linked through `related_to`.

**Rejected alternative:** We rejected reopening a closed ticket during the seven-day window. Resolved tickets may
still be reopened within seven days before they reach the final closed state.

**Reason:** Closure should produce a stable audit and reporting record. Creating a related ticket for a recurring
problem preserves the original resolution history while still connecting the two pieces of work.

**Service owner:** The Service Desk Product Owner signs off this decision because that role is accountable for the
ticket lifecycle, reporting integrity, and the meaning of the final closed state.

**Customer outcome:** Customers keep a clear history of what was completed and can raise a linked follow-up when a
problem returns, without silently changing the record of the original service interaction.

## C3 - VIP reporters and the priority matrix

**Decision:** After applying the impact-and-urgency matrix, a VIP ticket calculated as P3 or P4 is raised to P2.
Tickets already calculated as P1 or P2 keep their original priority.

**Rejected alternative:** We rejected storing the VIP flag without allowing it to affect priority, because that
would leave low-impact VIP reports at the matrix result of P3 or P4.

**Reason:** The stated business requirement is that executive issues must be immediately visible to the service
desk. A P2 floor supplies that visibility without incorrectly escalating every VIP report to P1.

**Service owner:** The Service Desk Product Owner signs off this decision because that role owns prioritisation
policy and balances executive visibility against the operational meaning of the P1 category.

**Customer outcome:** VIP reporters receive prompt visibility for their requests, while organisation-wide outages
continue to retain the uniquely highest P1 priority.
