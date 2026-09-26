---
lab2_edge_cases:
  E1: {rule: R-08, count: 3}
  E2: {rule: R-06, count: 2}
  E3: {rule: R-09, count: 4}
  E4: {rule: R-10, count: 4}
  E5: {rule: R-12, count: 1}
  E6: {rule: R-13, count: 11}
---
<!-- ai-generated: 80% - Codex drafted the analysis from the specification and I verified it against my service -->

# Edge cases in the practice event log

## E1 - clock skew produces a negative lead time

- What the log contains: Three commit/deployment pairs have commit timestamps later than the successful deployment that carried them, so their raw lead times are negative.
- What a default definition would have done: A naive calculation would report negative durations or discard the three records, making delivery appear faster while silently changing the measured population.
- Why the rule is defensible: Clamping each duration to zero preserves every delivered pair, while the anomaly count makes the clock-quality problem visible to the dashboard reader.

## E2 - a revert of a revert

- What the log contains: Commit `sha-0070` reverts `sha-0069`, and `sha-0071` then reverts `sha-0070`; both revert commits resolve transitively to the original change.
- What a default definition would have done: A one-hop or commit-counting definition would create extra changes for operational undo work and could count one underlying change two or three times.
- Why the rule is defensible: Following the complete revert chain preserves the business identity of the original change and prevents revert activity from inflating throughput.

## E3 - a hotfix that never touched `main`

- What the log contains: Four distinct deployed commits came from hotfix branches rather than `main`, but each was nevertheless carried by a production deployment in the window.
- What a default definition would have done: Filtering commits by branch name would omit real production work, reduce the delivered population and bias lead-time and throughput reporting.
- Why the rule is defensible: A production deployment is stronger evidence of delivery than a branch label, so the branch must not decide whether the commit counts.

## E4 - a deployment with zero linked commits

- What the log contains: Four in-scope production deployments have an empty `commits` array; two succeeded and two failed, so they are real operational events without linked code.
- What a default definition would have done: Dropping empty deployments would alter frequency and the failure and rework denominators, concealing deployments with poor traceability.
- Why the rule is defensible: The deployment happened regardless of linkage quality; counting it preserves operational truth while the anomaly exposes the missing provenance.

## E5 - a deployment that failed and never recovered

- What the log contains: Failed deployment `DEP-0015` is covered by open incident `INC-0004`, which has no resolved event and therefore no observable recovery instant.
- What a default definition would have done: Using the window end or current time would invent a recovery, while silently ignoring the failure would make reliability look better than it was.
- Why the rule is defensible: Excluding it from the recovery median but retaining it as an open failure and in change fail rate separates unknown recovery time from known failure.

## E6 - overlapping incidents

- What the log contains: The incident intervals form eleven unordered overlapping pairs, including the long-running open incident that intersects several resolved incidents.
- What a default definition would have done: Merging overlaps or summing incident durations would change attribution and could either hide independent failures or double-count shared clock time.
- Why the rule is defensible: Computing recovery per failed deployment preserves causal attribution, while the separate overlap count communicates simultaneous operational load.

## Gaming demonstration

I improved `deployment_frequency_per_day` by exploiting R-11: I moved the original successful deployments to the end of the measurement window, where the half-open interval excludes them, and added many empty successful production deployments just before the boundary. The dashboard therefore rewards more deployment records even though none of the original changes is delivered inside the window. A target based on deployment frequency would encourage teams to split or manufacture empty deployments and postpone substantial releases. The team or manager assessed on the frequency target would be rewarded, while customers and owners of the delayed changes would bear the cost.
