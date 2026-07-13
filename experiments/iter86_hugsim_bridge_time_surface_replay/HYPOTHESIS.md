# Iteration 86 - HUGSIM bridge-time support-surface replay

Status: `PRE_REGISTERED`

## Question

Iteration 85 showed that the support object has the better provenance bridge after the event in
all three fixed selected/support rows, while the selected object has the stronger event-row path
geometry.

This iteration asks the immediate follow-up:

At the support object's own best provenance-bridge timestamp, does that same support object become
active or borderline under the released CPA/TTC surface, or does it remain a surface miss?

This is a timing replay at already-logged decision rows. It is not a repair, threshold search,
actor-causality test, or new simulator run.

## Frozen inputs

The audit is offline only and may read:

- committed iteration-59 actor-match report and proof episode artifacts, including `eval.json`
  and `sentinel_iter48_decisions.jsonl`;
- committed iteration-81 support-object temporal surface report;
- committed iteration-83 bridge-supported surface-miss decomposition report;
- committed iteration-85 path-horizon/provenance-timing report.

It may import already-committed helper code from earlier iterations only for deterministic report
loading, decision-row loading, per-object CPA/TTC metric reconstruction, threshold-state
classification, and compact proof formatting.

It must not launch GPU work, read live box state, create HUGSIM episodes, modify simulator code,
approve a patch, change thresholds, fit a transform, retune Sentinel, or reinterpret simulation
artifacts as live system state.

## Fixed bridge-time rows

The fixed rows are exactly the three iteration-85 support-object best provenance bridge rows:

- `both_distinct_extreme` / `scene-0138-extreme-00` / pre event at `5.0 s`:
  support object `9`, event state `subthreshold`, support bridge `ambiguous`, bridge timestamp
  `5.5 s`;
- `ttc_medium_a` / `scene-0071-medium-01` / pre event at `2.5 s`:
  support object `10`, event state `subthreshold`, support bridge `match`, bridge timestamp
  `4.0 s`;
- `ttc_medium_a` / `scene-0071-medium-01` / active event at `5.0 s`:
  support object `10`, event state `subthreshold`, support bridge `match`, bridge timestamp
  `6.0 s`.

## Registered procedure

1. Cross-check source verdicts before analysis:
   - iteration 59: `ACTOR_MATCH_AUDIT_COMPLETE`;
   - iteration 81: `HUGSIM_SUPPORT_OBJECT_EVER_ACTIVE_COMPLETE`;
   - iteration 83: `HUGSIM_BRIDGE_SUPPORTED_SURFACE_MISS_MIXED_COMPLETE`;
   - iteration 85: `HUGSIM_PATH_HORIZON_BRIDGE_TIMING_SPLIT_COMPLETE`.
2. Cross-check that iteration 85 contains exactly the fixed rows above, with selected bridge
   support absent, support bridge support present, support bridge timing after the event, and
   support object state `subthreshold` at the event row.
3. Load only the committed iteration-59 ON decision logs for the fixed scenarios.
4. For each fixed row, select:
   - the exact event decision row at the fixed event timestamp;
   - the exact bridge-time decision row at the support bridge timestamp.
5. Recompute, for the support object at both rows:
   - released state (`active`, `borderline`, or `subthreshold`);
   - `min_cpa`, `cpa_rank`, finite or missing `ttc`, `ttc_rank`, `gap`, `closing`, and score;
   - active CPA/TTC margins and registered borderline CPA/TTC margins;
   - `cpa_horizon_index`.
6. Record bridge-time deltas relative to the event row:
   - state transition;
   - `min_cpa` delta;
   - finite-TTC transition;
   - CPA-rank delta when both ranks are finite.
7. Assign one registered row label per fixed row.
8. Emit JSON and Markdown proof with per-row event/bridge-time metrics and compact transition
   evidence.

## Registered labels

- `support_bridge_time_surface_arrival`: support object is subthreshold at the event row and
  active or borderline at the support bridge-time row.
- `support_bridge_time_surface_miss`: support object is subthreshold at the event row and remains
  subthreshold at the support bridge-time row.
- `support_bridge_time_object_missing`: support object is present at the event row but missing at
  the support bridge-time row.
- `bridge_time_surface_replay_insufficient`: required source, log, object, threshold, metric, or
  fixed bridge-time fact is missing or inconsistent.

## Registered verdicts

- `HUGSIM_BRIDGE_TIME_SURFACE_REPLAY_ARRIVAL_COMPLETE`: every fixed row is
  `support_bridge_time_surface_arrival`.
- `HUGSIM_BRIDGE_TIME_SURFACE_REPLAY_MISS_COMPLETE`: every fixed row is
  `support_bridge_time_surface_miss`.
- `HUGSIM_BRIDGE_TIME_SURFACE_REPLAY_MIXED_COMPLETE`: all fixed rows are classified without
  blocking, and both `support_bridge_time_surface_arrival` and `support_bridge_time_surface_miss`
  appear.
- `HUGSIM_BRIDGE_TIME_SURFACE_REPLAY_BLOCKED`: source verdicts, fixed row identities, decision
  logs, per-object metrics, thresholds, or bridge-time facts fail cross-checks, or any row is
  `bridge_time_surface_replay_insufficient`.

## Claim boundary

This is a three-row descriptive bridge-time support-surface replay only. It cannot claim actor
causality, repair, threshold value, transfer improvement, safety, deployment readiness,
robustness, benchmark ranking, HD-Score-invariance, population rate, retuning value, commercial
value, or real-world/first-responder behavior.
