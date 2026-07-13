# Iteration 84 - HUGSIM selected/support path-arbitration decomposition

Status: `PRE_REGISTERED`

## Question

Iterations 79-83 show a persistent split in the fixed HUGSIM foreground-supported rows:

- the selected monitor objects are active or borderline under the released CPA/TTC surface;
- the foreground-supported objects are nonselected and subthreshold;
- the selected objects do not bridge to logged provenance;
- the support objects do bridge to logged foreground provenance, but never with active same-frame
  released-surface co-occurrence.

This iteration asks the immediate arbitration question:

At the same fixed event rows, does the released monitor surface consistently select the object
with stronger logged path/hazard geometry while the foreground provenance bridge points to a
different, surface-ineligible object?

## Frozen inputs

The audit is offline only and may read:

- committed iteration-59 actor-match report and proof episode artifacts, including `eval.json`
  and `sentinel_iter48_decisions.jsonl`;
- committed iteration-79 selected-object surface decomposition report;
- committed iteration-80 selected-object all-provenance bridge report;
- committed iteration-83 bridge-supported surface-miss decomposition report.

It may import already-committed helper code from earlier iterations only for deterministic report
loading, decision-row loading, foreground provenance loading, frozen bridge-variant generation,
per-object CPA/TTC metric reconstruction, threshold-state classification, and compact proof
formatting.

It must not launch GPU work, read live box state, create HUGSIM episodes, modify simulator code,
approve a patch, change thresholds, fit a transform, retune Sentinel, or reinterpret simulation
artifacts as live system state.

## Fixed comparison rows

The fixed rows are exactly the three iteration-79 selected-vs-support events:

- `both_distinct_extreme` / `scene-0138-extreme-00` / pre event at `5.0 s`:
  selected object `5`, support object `9`;
- `ttc_medium_a` / `scene-0071-medium-01` / pre event at `2.5 s`:
  selected object `6`, support object `10`;
- `ttc_medium_a` / `scene-0071-medium-01` / active event at `5.0 s`:
  selected object `24`, support object `10`.

## Registered procedure

1. Cross-check source verdicts before analysis:
   - iteration 59: `ACTOR_MATCH_AUDIT_COMPLETE`;
   - iteration 79: `HUGSIM_SELECTED_ACTIVE_SUPPORT_SUBTHRESHOLD_COMPLETE`;
   - iteration 80: `HUGSIM_SELECTED_ALL_PROVENANCE_NO_SUPPORT_COMPLETE`;
   - iteration 83: `HUGSIM_BRIDGE_SUPPORTED_SURFACE_MISS_MIXED_COMPLETE`.
2. Cross-check that iteration 79 contains exactly the fixed comparison rows above, with selected
   objects active or borderline and support objects subthreshold.
3. Cross-check that iteration 80 contains the same selected object identities for the two fixed
   scenario/event roles it covers, and that no selected object has foreground/provenance bridge
   support under its registered all-provenance bridge procedure.
4. Cross-check that iteration 83 contains exactly the two fixed support objects above and no
   object-level problems.
5. Load only the committed iteration-59 ON decision logs and `eval.json` files for the fixed
   scenarios.
6. Select the exact decision row for each fixed event timestamp.
7. Recompute, for both selected and support objects at that event row:
   - released state (`active`, `borderline`, or `subthreshold`);
   - `min_cpa`, finite or missing `ttc`, `cpa_rank`, `ttc_rank`, `gap`, `closing`, and score;
   - active CPA margin: `min_cpa - cpa_margin`;
   - active TTC margin: `ttc - ttc_thresh` when TTC is finite, else `None`;
   - borderline CPA/TTC margins under the registered `3.0 m` and `5.0 s` descriptive bands.
8. Recompute foreground/provenance bridge support for both selected and support objects at the
   same event row using the frozen iteration-76/82 bridge procedure, and record bridge band,
   best distance, and compact best variant.
9. For each row, record directional comparisons:
   - whether the selected object has lower CPA than the support object;
   - whether the selected object has a better CPA rank;
   - whether the selected object has finite TTC while the support object does not;
   - whether both objects have finite TTC and the selected object has lower TTC;
   - whether the selected object has a better TTC rank;
   - whether the support object has better foreground bridge support.
10. Assign one registered row label per fixed comparison row.
11. Emit JSON and Markdown proof with per-row arbitration comparisons and compact bridge/metric
    evidence.

## Registered labels

- `selected_surface_support_bridge_split`: selected object is active or borderline, support object
  is subthreshold, support object has `match` or `ambiguous` bridge support, selected object does
  not have `match` or `ambiguous` bridge support, and at least one registered hazard-geometry
  advantage favors the selected object.
- `selected_surface_support_bridge_no_hazard_advantage`: selected/support surface and bridge
  split is present, but no registered hazard-geometry advantage favors the selected object.
- `selected_and_support_both_bridge_supported`: both selected and support objects have `match` or
  `ambiguous` bridge support at the event row.
- `support_surface_or_selected_subthreshold`: the selected object is subthreshold or the support
  object is active/borderline at the event row.
- `selected_support_arbitration_insufficient`: required source, log, object, threshold, metric,
  foreground, or bridge facts are missing or inconsistent.

## Registered verdicts

- `HUGSIM_SELECTED_SURFACE_SUPPORT_BRIDGE_SPLIT_COMPLETE`: every fixed row is
  `selected_surface_support_bridge_split`.
- `HUGSIM_SELECTED_SURFACE_SUPPORT_BRIDGE_NO_ADVANTAGE_COMPLETE`: at least one fixed row is
  `selected_surface_support_bridge_no_hazard_advantage`, no row is blocked, and no row is
  `selected_surface_support_bridge_split`.
- `HUGSIM_SELECTED_SUPPORT_ARBITRATION_MIXED_COMPLETE`: all fixed rows are classified without
  blocking, but neither complete verdict above holds.
- `HUGSIM_SELECTED_SUPPORT_ARBITRATION_BLOCKED`: source verdicts, fixed row identities,
  decision logs, per-object metrics, thresholds, foreground provenance, or bridge facts fail
  cross-checks, or any row is `selected_support_arbitration_insufficient`.

## Claim boundary

This is a three-row descriptive selected/support arbitration decomposition only. It cannot claim
actor causality, repair, threshold value, transfer improvement, safety, deployment readiness,
robustness, benchmark ranking, HD-Score-invariance, population rate, retuning value, commercial
value, or real-world/first-responder behavior.
