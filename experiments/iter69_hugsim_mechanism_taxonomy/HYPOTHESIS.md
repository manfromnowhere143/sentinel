# Iteration 69 - HUGSIM mechanism taxonomy synthesis

Status: `PRE_REGISTERED`

## Question

Iteration 59 produced eight fixed HUGSIM ON actor-match audit episodes. Iterations 61 through
68 then refined the three classifiable foreground rows into object-surface, temporal-alignment,
timeline, trigger/target, and fire-time bridge mechanisms.

This iteration asks a synthesis question only:

Can the eight iteration-59 HUGSIM ON rows be assigned a single mechanism taxonomy, preserving
the original structural null labels for non-classifiable rows and refining only the
classifiable foreground rows that downstream committed evidence directly supports?

## Frozen inputs

The synthesis is offline only and may read:

- committed iteration-59 actor-match report;
- committed iteration-61 object-surface report;
- committed iteration-63 temporal-emergence report;
- committed iteration-64 unsupported-temporal report;
- committed iteration-65 temporal-alignment report;
- committed iteration-66 matched-object timeline report;
- committed iteration-67 trigger-target bridge report;
- committed iteration-68 fire-time bridge report.

It must not launch GPU work, read live box state, create HUGSIM episodes, modify simulator code,
approve a patch, change thresholds, fit a transform, retune Sentinel, or reinterpret paper-only
simulation artifacts as live system state.

## Registered procedure

1. Cross-check all source verdicts before synthesis:
   - iteration 59: `ACTOR_MATCH_AUDIT_COMPLETE`;
   - iteration 61: `OBJECT_SURFACE_NONTRIGGER_MATCH_COMPLETE`;
   - iteration 63: `TEMPORAL_VISIBLE_NEVER_HAZARD_COMPLETE`;
   - iteration 64: `UNSUPPORTED_TEMPORAL_MATCH_COMPLETE`;
   - iteration 65: `TEMPORAL_ALIGNMENT_SUBTHRESHOLD_COMPLETE`;
   - iteration 66: `MATCHED_OBJECT_TIMELINE_MIXED_COMPLETE`;
   - iteration 67: `TRIGGER_TARGET_SAME_AND_SPLIT_COMPLETE`;
   - iteration 68: `FIRE_TIME_BRIDGE_GAP_TEMPORAL_SPLIT_COMPLETE`.
2. Start from the eight iteration-59 episodes in their committed schedule order.
3. Preserve iteration-59 structural labels for rows whose support label is:
   - `no_monitor_fire`;
   - `post_collision_fire`;
   - `background_collision_only`.
4. For rows whose iteration-59 support label is `classifiable_foreground`, assign a refined
   mechanism label only when the downstream committed reports contain the required matching row
   identities and row labels.
5. Emit a JSON report and Markdown table with:
   - all eight rows;
   - per-row source labels;
   - final mechanism label;
   - refinement evidence;
   - counts by mechanism;
   - count of classifiable rows refined by downstream evidence.

## Registered mechanism labels

- `no_monitor_fire`: iteration-59 structural label; no monitor fire occurred.
- `post_collision_fire`: iteration-59 structural label; monitor first fire occurred after the
  collision timing boundary.
- `background_collision_only`: iteration-59 structural label; collision was not attributable
  to a foreground actor row under the registered actor-match audit.
- `classifiable_actor_mismatch_unrefined`: fallback for a classifiable foreground row when the
  committed downstream reports do not prove a more specific mechanism.
- `nontrigger_visible_never_hazard`: classifiable row where iteration 61 proves a non-trigger
  object match and iteration 63 proves the matched object remains visible but never an active
  hazard under the registered temporal-emergence audit.
- `same_object_late_fire_after_best_bridge`: classifiable row where the matched target and
  first-fire trigger are the same object, the target becomes active at fire time, and iteration
  68 proves the best bridge support occurred before first fire.
- `split_object_visible_never_active_fire_before_best_bridge`: classifiable row where the
  bridge-matched target remains visible-never-active, the first-fire trigger is a different
  object, and iteration 68 proves the trigger's best bridge support occurred after first fire.

## Registered verdicts

- `HUGSIM_MECHANISM_TAXONOMY_COMPLETE`: all eight iteration-59 rows are classified, no
  infrastructure or cross-check problems occur, and all three classifiable foreground rows are
  refined by downstream committed evidence.
- `HUGSIM_MECHANISM_TAXONOMY_PARTIAL`: all eight iteration-59 rows are classified, but fewer
  than three classifiable foreground rows are refined by downstream committed evidence.
- `HUGSIM_MECHANISM_TAXONOMY_BLOCKED`: source verdicts, row identities, or required committed
  artifacts fail cross-checks, preventing the eight-row taxonomy from being produced.

## Claim boundary

This is an eight-row evidence synthesis over already committed HUGSIM audit reports. It cannot
claim actor causality, repair, transfer improvement, safety, deployment readiness, robustness,
benchmark ranking, HD-Score invariance, population mismatch rate, retuning value, or commercial
value. It may only state the registered mechanism labels for the fixed eight iteration-59 rows.
