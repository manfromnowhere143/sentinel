# Iteration 89 - HUGSIM joint bridge/surface candidate audit

Status: `PRE_REGISTERED`

## Question

Iterations 84-88 show a selected/support split: selected objects win released path geometry, while
provenance-backed support objects either reach only borderline or remain outside the frozen
surface.

This iteration asks the next counterfactual object/geometry question:

At the fixed iteration-87 replay rows, does any logged object simultaneously have active released
surface support and foreground/provenance bridge support, or are the bridge-supported objects still
only borderline/subthreshold while active surface objects lack bridge support?

This tests whether a simple object-arbitration answer exists under the frozen released surface. It
is not a repair, threshold search, actor-causality test, interpolation, or new simulator run.

## Frozen inputs

The audit is offline only and may read:

- committed iteration-59 actor-match report and proof episode artifacts, including `eval.json`
  and `sentinel_iter48_decisions.jsonl`;
- committed iteration-85 path-horizon/provenance-timing report;
- committed iteration-87 interval bridge-time support-surface replay report;
- committed iteration-88 bridge/surface margin residual report.

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
   - iteration 85: `HUGSIM_PATH_HORIZON_BRIDGE_TIMING_SPLIT_COMPLETE`;
   - iteration 87: `HUGSIM_INTERVAL_BRIDGE_TIME_SURFACE_REPLAY_MIXED_COMPLETE`;
   - iteration 88: `HUGSIM_BRIDGE_SURFACE_MARGIN_RESIDUAL_SPLIT_COMPLETE`.
2. Cross-check that iteration 87 contains exactly the fixed replay rows above with no row
   problems and the registered replay alignments.
3. Cross-check that iteration 88 contains exactly the fixed rows above with support residual
   labels `bridge_surface_ttc_borderline_cpa_far`,
   `bridge_surface_no_finite_ttc_cpa_far`, and `bridge_surface_no_finite_ttc_cpa_far`.
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
8. Record counts for joint candidate classes:
   - active and bridge-supported;
   - borderline and bridge-supported;
   - subthreshold and bridge-supported;
   - active with no bridge support;
   - borderline with no bridge support.
9. Record the support object's joint class.
10. Assign one registered row label per fixed replay row.
11. Emit JSON and Markdown proof with compact per-row joint counts and support-object evidence.

## Registered labels

- `no_active_bridge_candidate_support_borderline`: no object is both active and bridge-supported;
  the fixed support object is bridge-supported and borderline.
- `no_active_bridge_candidate_support_subthreshold`: no object is both active and
  bridge-supported; the fixed support object is bridge-supported and subthreshold.
- `active_bridge_candidate_present`: at least one object is both active and bridge-supported.
- `no_bridge_supported_candidate`: no object in the replay row has `match` or `ambiguous` bridge
  support.
- `joint_bridge_surface_candidate_insufficient`: required source, log, object, threshold, metric,
  foreground, bridge, or fixed replay fact is missing or inconsistent.

## Registered verdicts

- `HUGSIM_JOINT_BRIDGE_SURFACE_NO_ACTIVE_CANDIDATE_SPLIT_COMPLETE`: every fixed row is either
  `no_active_bridge_candidate_support_borderline` or
  `no_active_bridge_candidate_support_subthreshold`, and both labels appear.
- `HUGSIM_JOINT_BRIDGE_SURFACE_ACTIVE_CANDIDATE_PRESENT_COMPLETE`: at least one fixed row is
  `active_bridge_candidate_present`, and no row is blocked.
- `HUGSIM_JOINT_BRIDGE_SURFACE_CANDIDATE_MIXED_COMPLETE`: all fixed rows are classified without
  blocking, but neither complete verdict above holds.
- `HUGSIM_JOINT_BRIDGE_SURFACE_CANDIDATE_BLOCKED`: source verdicts, fixed row identities,
  decision logs, per-object metrics, foreground provenance, bridge facts, or labels fail
  cross-checks, or any row is `joint_bridge_surface_candidate_insufficient`.

## Claim boundary

This is a three-row descriptive joint bridge/surface candidate audit only. It cannot claim actor
causality, repair, threshold value, transfer improvement, safety, deployment readiness,
robustness, benchmark ranking, HD-Score-invariance, population rate, retuning value, commercial
value, or real-world/first-responder behavior.
