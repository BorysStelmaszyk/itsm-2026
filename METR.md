---
feature: DORA metrics computation from JSON event logs
feature_path: src/svcdesk/dora.py
predicted_minutes: 75
actual_minutes: 10.04
ratio: 0.13
prediction_receipt: https://github.com/swasik/itsm-2026-submissions/issues/138
completed_at: 2026-09-26T16:17:30+02:00
---

# METR n=1 outcome

The prediction was 75 minutes and the measured implementation time was 10.04 minutes. The resulting ratio is **actual/predicted: 0.13**. I measured from the timestamp recorded in `PREDICTION.md` until the checker first reported passes for the DORA API, every practice metric, all six edge-case consistency checks and all three gaming gates. The work included the pure event-log calculation in `src/svcdesk/dora.py`, integration of both HTTP endpoints, generation of the required metric artifacts and verification in the same Docker Compose environment used by the course checker.

The implementation finished substantially faster than predicted because the metric specification and its expected practice values were complete enough to serve as executable acceptance criteria. The first containerized run of the implementation passed the endpoint contract and every numerical field, so no debugging loop was needed for the metric engine. The remaining time was spent constructing and checking the Goodhart demonstration and writing the reasoning artifact. This is a single observation, not evidence that similar features will always take thirteen percent of their estimate; it mainly shows how much a precise specification and immediate automated feedback reduced uncertainty in this instance.
