# Iteration 95 - HUGSIM non-active surface branch arbitration

## Research question

For the two fixed non-active replay rows from iteration 93, does the released surface follow two
different branch rules: a provenance/TTC-borderline branch in `both_distinct_extreme`, and a
path/CPA branch in the `ttc_medium_a` pre row?

## Scope

This is an offline report-level audit. It may read only these committed reports:

- `experiments/iter92_hugsim_path_proximity_arbitration/proof-arbitration/path_proximity_arbitration_report.json`
- `experiments/iter93_hugsim_surface_winner_alignment/proof-alignment/surface_winner_alignment_report.json`
- `experiments/iter94_hugsim_active_row_surface_margin_arbitration/proof-margin/active_row_surface_margin_arbitration_report.json`

It must not read raw decision logs, launch Docker, touch the GPU box, run HUGSIM, modify
thresholds, tune parameters, or infer vehicle outcomes.

## Frozen rows

1. `both_distinct_extreme` / `scene-0138-extreme-00` / `pre` / replay `5.5` /
   `exact_bridge_ts`.
2. `ttc_medium_a` / `scene-0071-medium-01` / `pre` / replay `4.0` / `exact_bridge_ts`.

The active `ttc_medium_a` row is not re-analyzed here; iteration 94 is used only as a source
check proving that branch is already closed.

## Frozen source checks

The analyzer must stop as blocked unless all checks pass:

1. Iteration 92 verdict is `HUGSIM_PATH_PROXIMITY_ARBITRATION_SPLIT_COMPLETE`.
2. Iteration 93 verdict is `HUGSIM_SURFACE_WINNER_ALIGNMENT_MIXED_COMPLETE`.
3. Iteration 94 verdict is `HUGSIM_ACTIVE_ROW_SURFACE_MARGIN_ARBITRATION_COMPLETE`.
4. Both frozen non-active rows exist exactly once in iteration 92 and iteration 93.
5. Iteration 93 row labels are:
   - `both_distinct_extreme` pre: `surface_follows_provenance_nonactive`;
   - `ttc_medium_a` pre: `surface_follows_path_nonactive`.
6. Iteration 92 row labels are:
   - `both_distinct_extreme` pre: `path_best_no_bridge_provenance_best_nonactive`;
   - `ttc_medium_a` pre: `path_best_bridge_supported_nonactive`.
7. No source row has row-level problems.

## Fixed measurements

For each frozen row, compare path-best, provenance-best, and surface-best objects:

- object id, state, bridge band, bridge distance, `min_cpa`, `cpa_rank`, `ttc`, `ttc_rank`,
  `active_cpa_margin_m`, and `active_ttc_margin_s`;
- whether surface-best equals path-best;
- whether surface-best equals provenance-best;
- whether provenance-best has finite TTC while path-best does not;
- whether path-best has lower CPA and better CPA rank than provenance-best;
- whether provenance-best has closer bridge support than path-best.

## Completion labels

- `nonactive_surface_provenance_ttc_borderline_over_path_cpa`: surface-best equals
  provenance-best, provenance-best is `borderline`, provenance-best has finite TTC, path-best has
  no finite TTC, path-best has better CPA rank or lower CPA than provenance-best, and
  provenance-best has closer bridge support than path-best.
- `nonactive_surface_path_cpa_over_provenance_bridge`: surface-best equals path-best, both
  path-best and provenance-best are `subthreshold`, neither has finite TTC, path-best has lower
  CPA and better CPA rank than provenance-best, and provenance-best has closer bridge support
  than path-best.
- `nonactive_surface_branch_mixed_other`: source checks pass, but a row does not match either
  branch label.
- `nonactive_surface_branch_insufficient`: required fields are missing or malformed.

## Verdicts

- `HUGSIM_NONACTIVE_SURFACE_BRANCH_ARBITRATION_SPLIT_COMPLETE`: both frozen rows classify
  without blocking, with one row in each of the two named branch labels.
- `HUGSIM_NONACTIVE_SURFACE_BRANCH_PROVENANCE_ONLY_COMPLETE`: both rows classify as
  `nonactive_surface_provenance_ttc_borderline_over_path_cpa`.
- `HUGSIM_NONACTIVE_SURFACE_BRANCH_PATH_ONLY_COMPLETE`: both rows classify as
  `nonactive_surface_path_cpa_over_provenance_bridge`.
- `HUGSIM_NONACTIVE_SURFACE_BRANCH_MIXED_OTHER_COMPLETE`: at least one row classifies as
  `nonactive_surface_branch_mixed_other` and none are insufficient.
- `HUGSIM_NONACTIVE_SURFACE_BRANCH_BLOCKED`: source checks fail or any row is insufficient.

## Claim boundary

Two-row descriptive non-active surface branch arbitration only. This does not claim actor
causality, repair, threshold value, transfer, safety, deployment, robustness, benchmark
performance, population rate, HD-Score invariance, commercial value, real-world behavior,
first-responder behavior, or retuning.
