# Iteration 68 - fire-time bridge decomposition audit

Status: `PRE_REGISTERED`

## Question

Iteration 67 showed that both first-fire trigger objects lack bridge support at the actual
first-fire timestamp, even though each trigger object has a bridge match somewhere in the
pre-contact window. This iteration asks the narrower timing question:

When first-fire trigger support is absent at the fire timestamp, does the same trigger object's
best bridge support occur before first fire, after first fire, or remain unsupported?

The fixed rows are the two iteration-67 rows:

- `ttc_extreme_short` / `scene-0038-extreme-00` / trigger `object_id=2`;
- `cpa_medium_b` / `scene-0166-medium-00` / trigger `object_id=1`.

## Frozen inputs

The audit is offline only and may read:

- committed iteration-59 proof artifacts and report;
- committed iteration-61 object-surface report;
- committed iteration-64 unsupported-temporal report;
- committed iteration-65 temporal-alignment report;
- committed iteration-66 matched-object timeline report;
- committed iteration-67 trigger-target bridge report.

It must not launch GPU work, read live box state, create HUGSIM episodes, modify simulator code,
approve a patch, change thresholds, fit a transform, or retune Sentinel.

## Registered procedure

For each fixed row:

1. Cross-check iteration-59, iteration-61, iteration-64, iteration-65, iteration-66, and
   iteration-67 verdicts and row identities before analysis.
2. From the iteration-67 report, read:
   - first-fire timestamp;
   - trigger object ID;
   - full-window trigger bridge surface;
   - first-fire-only trigger bridge surface.
3. Confirm that the first-fire-only trigger surface is unsupported (`distance > 6.0 m`).
4. Compare the full-window trigger surface's best bridge decision timestamp to the first-fire
   timestamp.
5. Record:
   - fire-time best distance;
   - full-window best distance;
   - best decision timestamp;
   - best foreground timestamp;
   - temporal source;
   - lead time;
   - distance improvement from fire-time to best full-window support.

Bridge labels are frozen:

- `match`: distance `<= 3.0 m`;
- `ambiguous`: distance `> 3.0 m` and `<= 6.0 m`;
- `no_support`: distance `> 6.0 m`;
- `missing`: no evaluable object/foreground pair.

## Registered row labels

- `fire_gap_best_before_fire`: first-fire trigger is unsupported at fire time, and the same
  trigger object's best full-window bridge match occurs before first fire.
- `fire_gap_best_after_fire`: first-fire trigger is unsupported at fire time, and the same
  trigger object's best full-window bridge match occurs after first fire.
- `fire_gap_best_at_fire`: first-fire trigger is unsupported at fire time, but the best
  full-window support is at the same fire timestamp.
- `fire_gap_no_full_window_match`: first-fire trigger is unsupported at fire time, and the same
  trigger object has no full-window bridge match.
- `fire_gap_decomposition_insufficient`: committed artifacts cannot evaluate the required
  surfaces.

## Registered verdicts

- `FIRE_TIME_BRIDGE_GAP_TEMPORAL_SPLIT_COMPLETE`: evaluated rows include both before-fire and
  after-fire best full-window bridge matches.
- `FIRE_TIME_BRIDGE_GAP_ALL_BEFORE_COMPLETE`: all evaluated rows have before-fire best
  full-window bridge matches.
- `FIRE_TIME_BRIDGE_GAP_ALL_AFTER_COMPLETE`: all evaluated rows have after-fire best full-window
  bridge matches.
- `FIRE_TIME_BRIDGE_GAP_NO_MATCH_COMPLETE`: all evaluated rows have no full-window bridge match.
- `FIRE_TIME_BRIDGE_DECOMPOSITION_BLOCKED`: committed artifacts cannot reconstruct the required
  decomposition without new data.

## Claim boundary

This is a two-row fire-time bridge decomposition audit only. It cannot claim actor identity,
actor causality, repair, transfer, safety, deployment readiness, robustness, benchmark ranking,
HD-Score invariance, population mismatch rate, or threshold retuning value.
