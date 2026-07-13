# Iteration 91 - HUGSIM active-gap geometry decomposition

Status: `PRE_REGISTERED`

## Question

Iteration 90 showed that, at the fixed replay rows, bridge/provenance support lands only on
non-active objects while the one active released-surface object lacks bridge support. This
iteration asks the immediate geometry question:

Is the Iter90 split a path-vs-provenance geometry decomposition, where active released-surface
objects are path-near but provenance-far, while bridge-supported objects are provenance-near but
path-inactive under the frozen surface?

This is not a repair, threshold search, actor-causality test, interpolation, retuning step, or new
simulator run. It only records the already frozen geometry behind the active/provenance split.

## Frozen inputs

The audit is offline only and may read:

- committed iteration-59 actor-match report and proof episode artifacts, including `eval.json`
  and `sentinel_iter48_decisions.jsonl`;
- committed iteration-90 active-surface provenance gap report.

It may import already-committed helper code from earlier iterations only for deterministic report
loading, decision-row loading, foreground provenance loading, frozen bridge-variant generation,
per-object CPA/TTC metric reconstruction, threshold-state classification, compact proof
formatting, and coordinate extraction from existing bridge variants.

It must not launch GPU work, read live box state, create HUGSIM episodes, modify simulator code,
approve a patch, change thresholds, fit a transform, retune Sentinel, interpolate metrics, or
reinterpret simulation artifacts as live system state.

## Fixed replay rows

The fixed replay rows are exactly the three iteration-90 evaluated rows:

- `both_distinct_extreme` / `scene-0138-extreme-00` / pre event:
  support object `9`, replay timestamp `5.5 s`, alignment `exact_bridge_ts`;
- `ttc_medium_a` / `scene-0071-medium-01` / pre event:
  support object `10`, replay timestamp `4.0 s`, alignment `exact_bridge_ts`;
- `ttc_medium_a` / `scene-0071-medium-01` / active event:
  support object `10`, replay timestamp `5.75 s`, alignment `nearest_before_bridge_ts`.

## Registered procedure

1. Cross-check source verdicts before analysis:
   - iteration 59: `ACTOR_MATCH_AUDIT_COMPLETE`;
   - iteration 90: `HUGSIM_ACTIVE_SURFACE_PROVENANCE_GAP_COMPLETE`.
2. Cross-check that iteration 90 contains exactly the fixed replay rows above with no row
   problems, zero active+bridge-supported objects, and the registered labels:
   - two `active_surface_absent_bridge_supported_nonactive` rows;
   - one `active_surface_present_no_bridge_supported` row.
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
   - record bridge band, best bridge distance, and compact best-variant geometry including
     monitor-forward/lateral and HUGSIM foreground-forward/lateral coordinates.
7. For each replay row, record compact evidence for:
   - active objects, if any;
   - bridge-supported objects;
   - the nearest active object by bridge distance, if any;
   - the nearest bridge-supported object by active-surface margin, if any.
8. Assign one registered row label per fixed replay row.
9. Emit JSON and Markdown proof with compact per-row geometry evidence.

## Registered labels

- `provenance_near_path_inactive`: no object is active; at least one object is bridge-supported;
  every bridge-supported object is non-active.
- `path_active_provenance_far_with_bridge_nonactive`: at least one object is active; no active
  object is bridge-supported; at least one non-active object is bridge-supported.
- `path_provenance_coincident`: at least one object is both active and bridge-supported.
- `geometry_no_bridge_support`: no object in the replay row has `match` or `ambiguous` bridge
  support.
- `active_gap_geometry_insufficient`: required source, log, object, threshold, metric,
  foreground, bridge, best-variant geometry, or fixed replay fact is missing or inconsistent.

## Registered verdicts

- `HUGSIM_ACTIVE_GAP_PATH_PROVENANCE_DECOMPOSITION_COMPLETE`: every fixed row is either
  `provenance_near_path_inactive` or `path_active_provenance_far_with_bridge_nonactive`, both
  labels appear, and no row has an active bridge-supported object.
- `HUGSIM_ACTIVE_GAP_PATH_PROVENANCE_COINCIDENT_COMPLETE`: at least one fixed row is
  `path_provenance_coincident`, and no row is blocked.
- `HUGSIM_ACTIVE_GAP_GEOMETRY_MIXED_COMPLETE`: all fixed rows are classified without blocking,
  but neither complete verdict above holds.
- `HUGSIM_ACTIVE_GAP_GEOMETRY_BLOCKED`: source verdicts, fixed row identities, decision logs,
  per-object metrics, foreground provenance, bridge facts, best-variant geometry, or labels fail
  cross-checks, or any row is `active_gap_geometry_insufficient`.

## Claim boundary

This is a three-row descriptive active-gap geometry decomposition only. It cannot claim actor
causality, repair, threshold value, transfer improvement, safety, deployment readiness, robustness,
benchmark ranking, HD-Score-invariance, population rate, retuning value, commercial value, or
real-world/first-responder behavior.
