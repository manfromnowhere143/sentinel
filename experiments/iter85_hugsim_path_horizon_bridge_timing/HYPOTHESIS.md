# Iteration 85 - HUGSIM path-horizon/provenance-timing decomposition

Status: `PRE_REGISTERED`

## Question

Iteration 84 proved a clean selected/support split in the three fixed HUGSIM rows:
the released monitor surface selected the object with stronger logged path geometry, while the
foreground/provenance bridge pointed to a different surface-ineligible support object.

This iteration asks the next timing question:

At those same event rows, does the selected object win because its closest approach to the logged
plan occurs on the released path horizon, while the support object wins the foreground/provenance
bridge on a different timing channel?

The goal is not to repair or retune Sentinel. The goal is to decompose the Iter84 split into
plan-horizon geometry versus logged-provenance timing, with the closest-path horizon index/time
made explicit for the selected and support objects.

## Frozen inputs

The audit is offline only and may read:

- committed iteration-59 actor-match report and proof episode artifacts, including `eval.json`
  and `sentinel_iter48_decisions.jsonl`;
- committed iteration-80 selected-object all-provenance bridge report;
- committed iteration-83 bridge-supported surface-miss decomposition report;
- committed iteration-84 selected/support arbitration report.

It may import already-committed helper code from earlier iterations only for deterministic report
loading, decision-row loading, foreground provenance loading, frozen bridge-variant generation,
per-object CPA/TTC metric reconstruction, threshold-state classification, and compact proof
formatting.

It must not launch GPU work, read live box state, create HUGSIM episodes, modify simulator code,
approve a patch, change thresholds, fit a transform, retune Sentinel, or reinterpret simulation
artifacts as live system state.

## Fixed comparison rows

The fixed rows are exactly the three iteration-84 selected/support events:

- `both_distinct_extreme` / `scene-0138-extreme-00` / pre event at `5.0 s`:
  selected object `5`, support object `9`;
- `ttc_medium_a` / `scene-0071-medium-01` / pre event at `2.5 s`:
  selected object `6`, support object `10`;
- `ttc_medium_a` / `scene-0071-medium-01` / active event at `5.0 s`:
  selected object `24`, support object `10`.

## Registered procedure

1. Cross-check source verdicts before analysis:
   - iteration 59: `ACTOR_MATCH_AUDIT_COMPLETE`;
   - iteration 80: `HUGSIM_SELECTED_ALL_PROVENANCE_NO_SUPPORT_COMPLETE`;
   - iteration 83: `HUGSIM_BRIDGE_SUPPORTED_SURFACE_MISS_MIXED_COMPLETE`;
   - iteration 84: `HUGSIM_SELECTED_SURFACE_SUPPORT_BRIDGE_SPLIT_COMPLETE`.
2. Cross-check that iteration 84 contains exactly the fixed rows above, with selected objects
   active or borderline, support objects subthreshold, selected bridge support absent, and support
   bridge support present.
3. Load only the committed iteration-59 ON decision logs and `eval.json` files for the fixed
   scenarios.
4. Select the exact decision row for each fixed event timestamp.
5. Recompute, for both selected and support objects at that event row:
   - released state (`active`, `borderline`, or `subthreshold`);
   - `min_cpa`, `cpa_rank`, finite or missing `ttc`, `ttc_rank`, `gap`, `closing`, and score;
   - `cpa_horizon_index`;
   - `cpa_horizon_time_s = cpa_horizon_index * dt`;
   - `cpa_horizon_offset_s = cpa_horizon_time_s - event_ts`.
6. Recompute foreground/provenance bridge support for both selected and support objects at the
   same event row using the frozen iteration-76/82 bridge procedure, and record:
   - bridge band;
   - best distance;
   - compact best variant;
   - provenance timestamp when present;
   - provenance/event offset when present.
7. For each row, record directional comparisons:
   - whether the selected object has lower CPA than the support object;
   - whether the selected object has a better CPA rank;
   - whether the selected object's closest CPA horizon is earlier than the support object's
     closest CPA horizon;
   - whether the selected object's closest CPA horizon is closer to the event timestamp;
   - whether the support object has better foreground/provenance bridge support;
   - whether the selected object has no bridge support while the support object has `match` or
     `ambiguous` bridge support.
8. Assign one registered row label per fixed comparison row.
9. Emit JSON and Markdown proof with per-row horizon/provenance timing evidence and compact
   bridge/metric comparisons.

## Registered labels

- `path_horizon_support_bridge_timing_split`: selected object is active or borderline, support
  object is subthreshold, selected object has no `match` or `ambiguous` bridge support, support
  object has `match` or `ambiguous` bridge support, the selected object has lower CPA and better
  CPA rank, and both objects have finite `cpa_horizon_index` values.
- `path_horizon_support_bridge_no_horizon_advantage`: selected/support surface and bridge split
  is present, but lower CPA or better CPA rank does not favor the selected object.
- `selected_and_support_both_bridge_supported`: both selected and support objects have `match` or
  `ambiguous` bridge support at the event row.
- `support_surface_or_selected_subthreshold`: the selected object is subthreshold or the support
  object is active/borderline at the event row.
- `path_horizon_bridge_timing_insufficient`: required source, log, object, threshold, metric,
  horizon, foreground, or bridge timing facts are missing or inconsistent.

## Registered verdicts

- `HUGSIM_PATH_HORIZON_BRIDGE_TIMING_SPLIT_COMPLETE`: every fixed row is
  `path_horizon_support_bridge_timing_split`.
- `HUGSIM_PATH_HORIZON_BRIDGE_TIMING_NO_ADVANTAGE_COMPLETE`: at least one fixed row is
  `path_horizon_support_bridge_no_horizon_advantage`, no row is blocked, and no row is
  `path_horizon_support_bridge_timing_split`.
- `HUGSIM_PATH_HORIZON_BRIDGE_TIMING_MIXED_COMPLETE`: all fixed rows are classified without
  blocking, but neither complete verdict above holds.
- `HUGSIM_PATH_HORIZON_BRIDGE_TIMING_BLOCKED`: source verdicts, fixed row identities, decision
  logs, per-object metrics, thresholds, horizon facts, foreground provenance, or bridge timing
  facts fail cross-checks, or any row is `path_horizon_bridge_timing_insufficient`.

## Claim boundary

This is a three-row descriptive path-horizon/provenance-timing decomposition only. It cannot
claim actor causality, repair, threshold value, transfer improvement, safety, deployment
readiness, robustness, benchmark ranking, HD-Score-invariance, population rate, retuning value,
commercial value, or real-world/first-responder behavior.
