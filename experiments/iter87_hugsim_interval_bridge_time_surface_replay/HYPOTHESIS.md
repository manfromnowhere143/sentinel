# Iteration 87 - HUGSIM interval bridge-time support-surface replay

Status: `PRE_REGISTERED`

## Question

Iteration 86 attempted an exact bridge-time support-surface replay and blocked because the active
`ttc_medium_a` support bridge timestamp `6.0 s` has no exact committed ON decision row.

This iteration asks the registered successor:

If exact bridge timestamps are replayed when available, and otherwise the nearest logged decision
row at-or-before the bridge timestamp is used within a fixed `0.5 s` window, do the three
support-object bridge-time rows show surface arrival or surface miss under the released CPA/TTC
surface?

This is a logged-row interval replay only. It is not interpolation, threshold search, actor
causality, repair, or a new simulator run.

## Frozen inputs

The audit is offline only and may read:

- committed iteration-59 actor-match report and proof episode artifacts, including
  `sentinel_iter48_decisions.jsonl`;
- committed iteration-85 path-horizon/provenance-timing report;
- committed iteration-86 exact bridge-time support-surface replay report.

It may import already-committed helper code from earlier iterations only for deterministic report
loading, decision-row loading, per-object CPA/TTC metric reconstruction, threshold-state
classification, and compact proof formatting.

It must not launch GPU work, read live box state, create HUGSIM episodes, modify simulator code,
approve a patch, change thresholds, fit a transform, retune Sentinel, interpolate metrics, or
reinterpret simulation artifacts as live system state.

## Fixed interval replay rows

The fixed target rows are exactly the three iteration-85 support-object best provenance bridge
rows carried into iteration 86:

- `both_distinct_extreme` / `scene-0138-extreme-00` / pre event at `5.0 s`:
  support object `9`, bridge timestamp `5.5 s`;
- `ttc_medium_a` / `scene-0071-medium-01` / pre event at `2.5 s`:
  support object `10`, bridge timestamp `4.0 s`;
- `ttc_medium_a` / `scene-0071-medium-01` / active event at `5.0 s`:
  support object `10`, bridge timestamp `6.0 s`.

## Registered row-selection rule

For each fixed target row:

1. Load the committed ON decision log for the fixed scenario.
2. Select the exact event decision row at the fixed event timestamp.
3. Select the replay decision row with this deterministic rule:
   - if exactly one decision row exists at the bridge timestamp, use it and label alignment
     `exact_bridge_ts`;
   - otherwise, among decision rows with `event_ts <= row_ts <= bridge_ts`, choose the row with
     the largest `row_ts`;
   - the fallback row is valid only if `0.0 < bridge_ts - row_ts <= 0.5`;
   - a valid fallback is labeled `nearest_before_bridge_ts`;
   - if no valid exact or fallback row exists, the row is
     `interval_bridge_time_surface_replay_insufficient`.
4. Do not use future-after-bridge rows, interpolation, object-presence-conditioned row choice,
   nearest absolute timestamp, per-row tolerance tuning, or scenario-specific exceptions.

## Registered procedure

1. Cross-check source verdicts before analysis:
   - iteration 59: `ACTOR_MATCH_AUDIT_COMPLETE`;
   - iteration 85: `HUGSIM_PATH_HORIZON_BRIDGE_TIMING_SPLIT_COMPLETE`;
   - iteration 86: `HUGSIM_BRIDGE_TIME_SURFACE_REPLAY_BLOCKED`.
2. Cross-check that iteration 85 contains exactly the fixed rows above, with selected bridge
   support absent, support bridge support present, support bridge timing after the event, and
   support object state `subthreshold` at the event row.
3. Cross-check that iteration 86 blocked specifically because the active `ttc_medium_a` row had
   `bridge-row-count-0-for-ts-6.0`.
4. Apply the registered row-selection rule to each fixed row.
5. Recompute, for the support object at the event row and selected replay row:
   - released state (`active`, `borderline`, or `subthreshold`);
   - `min_cpa`, `cpa_rank`, finite or missing `ttc`, `ttc_rank`, `gap`, `closing`, and score;
   - active CPA/TTC margins and registered borderline CPA/TTC margins;
   - `cpa_horizon_index`.
6. Record replay deltas relative to the event row:
   - state transition;
   - replay alignment label;
   - bridge-to-replay offset;
   - `min_cpa` delta;
   - finite-TTC transition;
   - CPA-rank delta when both ranks are finite.
7. Assign one registered row label per fixed row.
8. Emit JSON and Markdown proof with per-row event/replay metrics and compact transition evidence.

## Registered labels

- `interval_support_surface_arrival`: support object is subthreshold at the event row and active
  or borderline at the selected replay row.
- `interval_support_surface_miss`: support object is subthreshold at the event row and remains
  subthreshold at the selected replay row.
- `interval_support_object_missing`: support object is present at the event row but missing at
  the selected replay row.
- `interval_bridge_time_surface_replay_insufficient`: required source, log, row-selection,
  object, threshold, metric, or fixed bridge-time fact is missing or inconsistent.

## Registered verdicts

- `HUGSIM_INTERVAL_BRIDGE_TIME_SURFACE_REPLAY_ARRIVAL_COMPLETE`: every fixed row is
  `interval_support_surface_arrival`.
- `HUGSIM_INTERVAL_BRIDGE_TIME_SURFACE_REPLAY_MISS_COMPLETE`: every fixed row is
  `interval_support_surface_miss`.
- `HUGSIM_INTERVAL_BRIDGE_TIME_SURFACE_REPLAY_MIXED_COMPLETE`: all fixed rows are classified
  without blocking, and both `interval_support_surface_arrival` and
  `interval_support_surface_miss` appear.
- `HUGSIM_INTERVAL_BRIDGE_TIME_SURFACE_REPLAY_BLOCKED`: source verdicts, fixed row identities,
  row selection, decision logs, per-object metrics, thresholds, or bridge-time facts fail
  cross-checks, or any row is `interval_bridge_time_surface_replay_insufficient`.

## Claim boundary

This is a three-row descriptive interval bridge-time support-surface replay only. It cannot claim
actor causality, repair, threshold value, transfer improvement, safety, deployment readiness,
robustness, benchmark ranking, HD-Score-invariance, population rate, retuning value, commercial
value, or real-world/first-responder behavior.
