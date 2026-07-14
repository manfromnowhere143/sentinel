# Iteration 98 - HUGSIM background-only outcome bridge

## Research question

Does the single fixed background-only structural row join cleanly from iteration-59 collision
provenance absence to iteration-70 monitor-fire timing, explaining that branch as a foreground
support absence with a live monitor fire rather than a foreground actor mismatch or a no-fire row?

## Scope

This is an offline report-level bridge audit. It may read only these committed reports:

- `experiments/iter59_hugsim_actor_match_audit/proof-actor-match/actor_match_report.json`
- `experiments/iter69_hugsim_mechanism_taxonomy/proof-taxonomy/taxonomy_report.json`
- `experiments/iter70_hugsim_structural_timing_audit/proof-structural/structural_report.json`

It must not read raw decision logs, raw `eval.json` files, launch Docker, touch the GPU box, run
HUGSIM, modify thresholds, tune parameters, or infer counterfactual vehicle outcomes.

## Frozen row

This audit is limited to the one iteration-70 foreground-absent background-only row:

1. `cpa_medium_a` / `scene-0071-medium-00`.

## Frozen source checks

The analyzer must stop as blocked unless all checks pass:

1. Iteration 59 verdict is `ACTOR_MATCH_AUDIT_COMPLETE`.
2. Iteration 69 verdict is `HUGSIM_MECHANISM_TAXONOMY_COMPLETE`.
3. Iteration 70 verdict is `HUGSIM_STRUCTURAL_TIMING_TAXONOMY_COMPLETE`.
4. The frozen row exists exactly once in all three reports.
5. Iteration 59 row has:
   - `support_label == background_collision_only`;
   - `foreground_count == 0`;
   - `first_foreground_ts == null`;
   - `monitor_object_id == 11`;
   - `monitor_provenance_label == unique_ttc_object`;
   - `first_fire_ts == 3.5`;
   - `first_fire_channel == ttc_only`;
   - `fired_frames == 4`;
   - `brake_frames == 11`.
6. Iteration 69 row has:
   - `mechanism_label == background_collision_only`;
   - `iter59_support_label == background_collision_only`;
   - `first_fire_ts == 3.5`;
   - `first_fire_channel == ttc_only`;
   - `monitor_object_id == 11`.
7. Iteration 70 row has:
   - `structural_label == foreground_absent_background_only`;
   - `iter59_support_label == background_collision_only`;
   - `report.foreground_count == 0`;
   - `report.first_foreground_ts == null`;
   - `report.first_fire_ts == 3.5`;
   - `report.monitor_object_id == 11`;
   - `report.monitor_provenance_label == unique_ttc_object`;
   - `decision_log.first_fire_ts == 3.5`;
   - `decision_log.first_fire_channel == ttc_only`;
   - `decision_log.fired_frames == 4`;
   - `decision_log.brake_frames == 11`;
   - `pre_or_at_foreground_fire == false`.
8. No source row has row-level problems.

## Fixed measurements

For the frozen row, compute:

- support/mechanism/structural labels from iterations 59, 69, and 70;
- foreground count and first foreground timestamp from iterations 59 and 70;
- first fire timestamp and channel from iterations 59, 69, and 70;
- fired and brake frames from iterations 59 and 70;
- monitor object id and monitor provenance label from iterations 59, 69, and 70;
- whether foreground support is absent;
- whether monitor fire is present;
- whether the monitor-fire object is preserved across reports.

## Completion labels

- `background_only_ttc_fire_foreground_absent`: the row is background-only in all three reports,
  has no foreground support, has a live monitor fire at `3.5 s`, uses the `ttc_only` channel, and
  preserves monitor object `11` with `unique_ttc_object` provenance.
- `background_only_foreground_absent_no_fire`: the row is background-only in all three reports,
  has no foreground support, but has no monitor fire.
- `background_only_outcome_mixed`: source checks pass, but the row does not match either
  background-only bridge label.
- `background_only_outcome_insufficient`: required fields are missing or malformed.

## Verdicts

- `HUGSIM_BACKGROUND_ONLY_OUTCOME_BRIDGE_COMPLETE`: the frozen row classifies as
  `background_only_ttc_fire_foreground_absent`.
- `HUGSIM_BACKGROUND_ONLY_OUTCOME_NO_FIRE_COMPLETE`: the frozen row classifies as
  `background_only_foreground_absent_no_fire`.
- `HUGSIM_BACKGROUND_ONLY_OUTCOME_MIXED_COMPLETE`: the frozen row classifies as
  `background_only_outcome_mixed`.
- `HUGSIM_BACKGROUND_ONLY_OUTCOME_BRIDGE_BLOCKED`: source checks fail or the row is insufficient.

## Claim boundary

One-row descriptive background-only provenance/timing bridge only. This does not claim actor
causality, repair, threshold value, transfer, safety, deployment, robustness, benchmark
performance, population rate, HD-Score invariance, commercial value, real-world behavior,
first-responder behavior, or retuning.
