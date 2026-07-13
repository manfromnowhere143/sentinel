# Iteration 90 - HUGSIM active-surface provenance gap audit

Status: `PRE_REGISTERED`

## Question

Iteration 89 found no logged object that is both active under the released Sentinel surface and
foreground/provenance bridge-supported at the three fixed iteration-87 replay rows. This iteration
asks the active-side follow-up:

When the released surface has active objects, do those active objects lack foreground/provenance
bridge support while bridge-supported objects remain non-active; and when the released surface has
no active object, is the row purely bridge-supported but non-active?

This is not a repair, threshold search, actor-causality test, interpolation, retuning step, or new
simulator run. It only decomposes the active-surface side of the already frozen Iter87/Iter89 rows.

## Frozen inputs

The audit is offline only and may read:

- committed iteration-59 actor-match report and proof episode artifacts, including `eval.json`
  and `sentinel_iter48_decisions.jsonl`;
- committed iteration-87 interval bridge-time support-surface replay report;
- committed iteration-89 joint bridge/surface candidate report.

It may import already-committed helper code from earlier iterations only for deterministic report
loading, decision-row loading, foreground provenance loading, frozen bridge-variant generation,
per-object CPA/TTC metric reconstruction, threshold-state classification, and compact proof
formatting.

It must not launch GPU work, read live box state, create HUGSIM episodes, modify simulator code,
approve a patch, change thresholds, fit a transform, retune Sentinel, interpolate metrics, or
reinterpret simulation artifacts as live system state.

## Fixed replay rows

The fixed replay rows are exactly the three iteration-87 evaluated rows:

- `both_distinct_extreme` / `scene-0138-extreme-00` / pre event:
  support object `9`, replay timestamp `5.5 s`, alignment `exact_bridge_ts`;
- `ttc_medium_a` / `scene-0071-medium-01` / pre event:
  support object `10`, replay timestamp `4.0 s`, alignment `exact_bridge_ts`;
- `ttc_medium_a` / `scene-0071-medium-01` / active event:
  support object `10`, replay timestamp `5.75 s`, alignment `nearest_before_bridge_ts`.

## Registered procedure

1. Cross-check source verdicts before analysis:
   - iteration 59: `ACTOR_MATCH_AUDIT_COMPLETE`;
   - iteration 87: `HUGSIM_INTERVAL_BRIDGE_TIME_SURFACE_REPLAY_MIXED_COMPLETE`;
   - iteration 89: `HUGSIM_JOINT_BRIDGE_SURFACE_NO_ACTIVE_CANDIDATE_SPLIT_COMPLETE`.
2. Cross-check that iteration 87 contains exactly the fixed replay rows above with no row
   problems and the registered replay alignments.
3. Cross-check that iteration 89 contains exactly the fixed replay rows above, zero
   `active_bridge_supported_count` rows, and no row problems.
4. Load only the committed iteration-59 ON decision logs and `eval.json` files for the fixed
   scenarios.
5. Select the exact replay decision row at the fixed replay timestamp.
6. Load all eligible logged foreground/provenance rows from the scenario `eval.json`.
7. For every logged object in the replay decision row:
   - recompute released state (`active`, `borderline`, or `subthreshold`);
   - recompute `min_cpa`, `cpa_rank`, finite or missing `ttc`, `ttc_rank`, `gap`, `closing`, and
     score;
   - recompute foreground/provenance bridge support against all eligible provenance rows using
     the frozen iteration-76/82 bridge procedure at the replay timestamp;
   - record bridge band and best bridge distance.
8. Record counts for active objects, bridge-supported objects, active bridge-supported objects,
   bridge-supported non-active objects, and active objects with no bridge support.
9. Record compact evidence for active candidates and bridge-supported candidates.
10. Assign one registered row label per fixed replay row.
11. Emit JSON and Markdown proof with compact per-row counts and candidate evidence.

## Registered labels

- `active_surface_absent_bridge_supported_nonactive`: no object is active; at least one object is
  bridge-supported; zero objects are both active and bridge-supported.
- `active_surface_present_no_bridge_supported`: at least one object is active; no active object is
  bridge-supported; at least one non-active object is bridge-supported.
- `active_surface_bridge_supported_present`: at least one object is both active and
  bridge-supported.
- `active_surface_no_bridge_support`: no object in the replay row has `match` or `ambiguous`
  bridge support.
- `active_surface_provenance_gap_insufficient`: required source, log, object, threshold, metric,
  foreground, bridge, or fixed replay fact is missing or inconsistent.

## Registered verdicts

- `HUGSIM_ACTIVE_SURFACE_PROVENANCE_GAP_COMPLETE`: every fixed row is either
  `active_surface_absent_bridge_supported_nonactive` or
  `active_surface_present_no_bridge_supported`, both labels appear, and no row has an active
  bridge-supported object.
- `HUGSIM_ACTIVE_SURFACE_BRIDGE_SUPPORTED_PRESENT_COMPLETE`: at least one fixed row is
  `active_surface_bridge_supported_present`, and no row is blocked.
- `HUGSIM_ACTIVE_SURFACE_PROVENANCE_GAP_MIXED_COMPLETE`: all fixed rows are classified without
  blocking, but neither complete verdict above holds.
- `HUGSIM_ACTIVE_SURFACE_PROVENANCE_GAP_BLOCKED`: source verdicts, fixed row identities,
  decision logs, per-object metrics, foreground provenance, bridge facts, or labels fail
  cross-checks, or any row is `active_surface_provenance_gap_insufficient`.

## Claim boundary

This is a three-row descriptive active-surface/provenance gap audit only. It cannot claim actor
causality, repair, threshold value, transfer improvement, safety, deployment readiness, robustness,
benchmark ranking, HD-Score-invariance, population rate, retuning value, commercial value, or
real-world/first-responder behavior.
