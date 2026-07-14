# Iteration 96 - HUGSIM branch taxonomy outcome bridge

## Research question

Do the fixed surface-branch explanations from iterations 94-95 both join to the same HUGSIM
structural outcome class for the two post-collision-fire rows: `foreground_present_late_fire`
with no monitor fire before or at foreground contact?

## Scope

This is an offline report-level bridge audit. It may read only these committed reports:

- `experiments/iter70_hugsim_structural_timing_audit/proof-structural/structural_report.json`
- `experiments/iter94_hugsim_active_row_surface_margin_arbitration/proof-margin/active_row_surface_margin_arbitration_report.json`
- `experiments/iter95_hugsim_nonactive_surface_branch_arbitration/proof-branch/nonactive_surface_branch_arbitration_report.json`

It must not read raw decision logs, launch Docker, touch the GPU box, run HUGSIM, modify
thresholds, tune parameters, or infer counterfactual vehicle outcomes.

## Frozen rows

This audit is limited to the two iteration-70 late-fire structural rows:

1. `both_distinct_extreme` / `scene-0138-extreme-00`;
2. `ttc_medium_a` / `scene-0071-medium-01`.

For `both_distinct_extreme`, the branch source is iteration 95's non-active pre row. For
`ttc_medium_a`, the branch sources are iteration 95's non-active pre row and iteration 94's
active row.

## Frozen source checks

The analyzer must stop as blocked unless all checks pass:

1. Iteration 70 verdict is `HUGSIM_STRUCTURAL_TIMING_TAXONOMY_COMPLETE`.
2. Iteration 94 verdict is `HUGSIM_ACTIVE_ROW_SURFACE_MARGIN_ARBITRATION_COMPLETE`.
3. Iteration 95 verdict is `HUGSIM_NONACTIVE_SURFACE_BRANCH_ARBITRATION_SPLIT_COMPLETE`.
4. Both frozen rows exist exactly once in iteration 70 and have:
   - `structural_label == foreground_present_late_fire`;
   - `iter59_support_label == post_collision_fire`;
   - `pre_or_at_foreground_fire == false`;
   - `fire_minus_foreground_s == 1.75`.
5. Iteration 95 contains:
   - `both_distinct_extreme` / `pre` label
     `nonactive_surface_provenance_ttc_borderline_over_path_cpa`;
   - `ttc_medium_a` / `pre` label
     `nonactive_surface_path_cpa_over_provenance_bridge`.
6. Iteration 94 contains:
   - `ttc_medium_a` / `active` label `active_row_cpa_margin_overrides_provenance`.
7. No source row has row-level problems.

## Fixed measurements

For each frozen structural row, compute:

- first foreground timestamp;
- first fire timestamp;
- fire-minus-foreground seconds;
- first-fire channel;
- pre-or-at-foreground-fire flag;
- branch labels joined from iteration 94 and/or iteration 95;
- branch label count;
- whether the row has any provenance/TTC branch;
- whether the row has any path/CPA branch;
- whether the row has any active CPA/path branch.

## Completion labels

- `late_fire_with_provenance_ttc_branch`: the structural row is late-fire, has no pre-or-at
  foreground fire, and has a joined provenance/TTC branch.
- `late_fire_with_path_cpa_branch`: the structural row is late-fire, has no pre-or-at foreground
  fire, and has a joined path/CPA or active CPA/path branch, with no joined provenance/TTC branch.
- `late_fire_branch_outcome_mixed`: source checks pass, but a row has a late-fire outcome with a
  branch combination outside the two labels above.
- `late_fire_branch_outcome_insufficient`: required fields are missing or malformed.

## Verdicts

- `HUGSIM_BRANCH_TAXONOMY_LATE_FIRE_OUTCOME_BRIDGE_COMPLETE`: both frozen rows classify without
  blocking, both are late-fire/no-pre-fire outcome rows, and the joined branches include one
  provenance/TTC row and one path/CPA row.
- `HUGSIM_BRANCH_TAXONOMY_LATE_FIRE_PATH_ONLY_COMPLETE`: both rows classify as
  `late_fire_with_path_cpa_branch`.
- `HUGSIM_BRANCH_TAXONOMY_LATE_FIRE_PROVENANCE_ONLY_COMPLETE`: both rows classify as
  `late_fire_with_provenance_ttc_branch`.
- `HUGSIM_BRANCH_TAXONOMY_LATE_FIRE_MIXED_OTHER_COMPLETE`: at least one row classifies as
  `late_fire_branch_outcome_mixed` and none are insufficient.
- `HUGSIM_BRANCH_TAXONOMY_OUTCOME_BRIDGE_BLOCKED`: source checks fail or any row is insufficient.

## Claim boundary

Two-row descriptive branch-taxonomy/outcome bridge only. This does not claim actor causality,
repair, threshold value, transfer, safety, deployment, robustness, benchmark performance,
population rate, HD-Score invariance, commercial value, real-world behavior, first-responder
behavior, or retuning.
