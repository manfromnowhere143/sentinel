# Iteration 92 - HUGSIM path-proximity arbitration audit

Status: `PRE_REGISTERED`

## Question

Iteration 91 showed a path-vs-provenance geometry split at the fixed replay rows: the active
released-surface object is path-near but provenance-far, while bridge-supported objects are
provenance-near but path-inactive. This iteration asks the next arbitration question:

At each fixed replay row, is the CPA/path-best logged object different from the provenance-best
bridge-supported object, and does that explain why the released surface follows path proximity
instead of provenance support?

This is not a repair, threshold search, actor-causality test, interpolation, retuning step, or new
simulator run. It only records which logged object wins path proximity versus which logged object
wins provenance proximity under the frozen evidence.

## Frozen inputs

The audit is offline only and may read:

- committed iteration-59 actor-match report and proof episode artifacts, including `eval.json`
  and `sentinel_iter48_decisions.jsonl`;
- committed iteration-91 active-gap geometry decomposition report.

It may import already-committed helper code from earlier iterations only for deterministic report
loading, decision-row loading, foreground provenance loading, frozen bridge-variant generation,
per-object CPA/TTC metric reconstruction, threshold-state classification, compact proof
formatting, and bridge geometry extraction.

It must not launch GPU work, read live box state, create HUGSIM episodes, modify simulator code,
approve a patch, change thresholds, fit a transform, retune Sentinel, interpolate metrics, or
reinterpret simulation artifacts as live system state.

## Fixed replay rows

The fixed replay rows are exactly the three iteration-91 evaluated rows:

- `both_distinct_extreme` / `scene-0138-extreme-00` / pre event:
  support object `9`, replay timestamp `5.5 s`, alignment `exact_bridge_ts`;
- `ttc_medium_a` / `scene-0071-medium-01` / pre event:
  support object `10`, replay timestamp `4.0 s`, alignment `exact_bridge_ts`;
- `ttc_medium_a` / `scene-0071-medium-01` / active event:
  support object `10`, replay timestamp `5.75 s`, alignment `nearest_before_bridge_ts`.

## Registered selectors

- `path_best`: the logged object with the lowest numeric `cpa_rank`; ties break by lower
  `min_cpa`, then stringified `object_id`.
- `provenance_best`: the bridge-supported logged object (`match` or `ambiguous`) with the lowest
  bridge `best_distance_m`; ties break by lower `cpa_rank`, then stringified `object_id`.
- `surface_best`: the logged object with the strongest released-surface state (`active` before
  `borderline` before `subthreshold`), then lower active CPA margin, then lower active TTC margin,
  then lower `cpa_rank`, then stringified `object_id`.

The primary label uses `path_best` and `provenance_best`; `surface_best` is recorded only to keep
the released-surface interpretation auditable.

## Registered procedure

1. Cross-check source verdicts before analysis:
   - iteration 59: `ACTOR_MATCH_AUDIT_COMPLETE`;
   - iteration 91: `HUGSIM_ACTIVE_GAP_PATH_PROVENANCE_DECOMPOSITION_COMPLETE`.
2. Cross-check that iteration 91 contains exactly the fixed replay rows above with no row
   problems, zero active+bridge-supported objects, and the registered geometry labels:
   - two `provenance_near_path_inactive` rows;
   - one `path_active_provenance_far_with_bridge_nonactive` row.
3. Load only the committed iteration-59 ON decision logs and `eval.json` files for the fixed
   scenarios.
4. Select the exact replay decision row at the fixed replay timestamp.
5. Load all eligible logged foreground/provenance rows from the scenario `eval.json`.
6. For every logged object in the replay decision row:
   - recompute released state (`active`, `borderline`, or `subthreshold`);
   - recompute `min_cpa`, `cpa_rank`, finite or missing `ttc`, `ttc_rank`, `gap`, `closing`, and
     score;
   - recompute foreground/provenance bridge support against all eligible provenance rows using
     the frozen iteration-76/82 bridge procedure at the replay timestamp;
   - record bridge band, best bridge distance, and compact best-variant geometry.
7. Compute `path_best`, `provenance_best`, and `surface_best`.
8. Record whether `path_best` and `provenance_best` are the same object, whether each is active,
   and whether each is bridge-supported.
9. Assign one registered row label per fixed replay row.
10. Emit JSON and Markdown proof with compact per-row arbitration evidence.

## Registered labels

- `path_best_no_bridge_provenance_best_nonactive`: `path_best` is not bridge-supported,
  `provenance_best` is non-active, and the two objects differ.
- `path_best_bridge_supported_nonactive`: `path_best` is bridge-supported and non-active.
- `path_best_active_no_bridge`: `path_best` is active, not bridge-supported, and at least one
  non-active `provenance_best` object exists.
- `path_provenance_same_active`: `path_best` and `provenance_best` are the same active object.
- `path_provenance_same_nonactive`: `path_best` and `provenance_best` are the same non-active
  object.
- `path_proximity_arbitration_insufficient`: required source, log, object, threshold, metric,
  foreground, bridge, selector, or fixed replay fact is missing or inconsistent.

## Registered verdicts

- `HUGSIM_PATH_PROXIMITY_ARBITRATION_SPLIT_COMPLETE`: every fixed row is classified as one of
  `path_best_no_bridge_provenance_best_nonactive`, `path_best_bridge_supported_nonactive`,
  `path_best_active_no_bridge`, or `path_provenance_same_nonactive`; at least two of those labels
  appear; and no row is `path_provenance_same_active`.
- `HUGSIM_PATH_PROXIMITY_ARBITRATION_ACTIVE_COINCIDENT_COMPLETE`: at least one fixed row is
  `path_provenance_same_active`, and no row is blocked.
- `HUGSIM_PATH_PROXIMITY_ARBITRATION_MIXED_COMPLETE`: all fixed rows are classified without
  blocking, but neither complete verdict above holds.
- `HUGSIM_PATH_PROXIMITY_ARBITRATION_BLOCKED`: source verdicts, fixed row identities, decision
  logs, per-object metrics, foreground provenance, bridge facts, selectors, or labels fail
  cross-checks, or any row is `path_proximity_arbitration_insufficient`.

## Claim boundary

This is a three-row descriptive path-proximity/provenance arbitration audit only. It cannot claim
actor causality, repair, threshold value, transfer improvement, safety, deployment readiness,
robustness, benchmark ranking, HD-Score-invariance, population rate, retuning value, commercial
value, or real-world/first-responder behavior.
