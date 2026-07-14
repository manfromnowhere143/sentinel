# Iteration 99 - HUGSIM structural bridge coverage audit

## Research question

Do the three structural bridge results from iterations 96-98 now cover every fixed iteration-70
structural row exactly once, with no duplicate coverage, no missing row, and the expected
late-fire/surface-silent/background-only class counts?

## Scope

This is an offline report-level coverage audit. It may read only these committed reports:

- `experiments/iter70_hugsim_structural_timing_audit/proof-structural/structural_report.json`
- `experiments/iter96_hugsim_branch_outcome_bridge/proof-outcome/branch_outcome_bridge_report.json`
- `experiments/iter97_hugsim_surface_silent_outcome_margin_bridge/proof-silent-outcome/surface_silent_outcome_margin_bridge_report.json`
- `experiments/iter98_hugsim_background_only_outcome_bridge/proof-background-outcome/background_only_outcome_bridge_report.json`

It must not read raw decision logs, raw `eval.json` files, launch Docker, touch the GPU box, run
HUGSIM, modify thresholds, tune parameters, or infer counterfactual vehicle outcomes.

## Frozen rows

This audit is limited to the five iteration-70 structural rows:

1. `mixed_extreme` / `scene-0062-extreme-00`;
2. `both_distinct_extreme` / `scene-0138-extreme-00`;
3. `nofire_hard_control` / `scene-0041-hard-00`;
4. `cpa_medium_a` / `scene-0071-medium-00`;
5. `ttc_medium_a` / `scene-0071-medium-01`.

## Frozen source checks

The analyzer must stop as blocked unless all checks pass:

1. Iteration 70 verdict is `HUGSIM_STRUCTURAL_TIMING_TAXONOMY_COMPLETE`.
2. Iteration 96 verdict is `HUGSIM_BRANCH_TAXONOMY_LATE_FIRE_OUTCOME_BRIDGE_COMPLETE`.
3. Iteration 97 verdict is `HUGSIM_SURFACE_SILENT_OUTCOME_MARGIN_BRIDGE_COMPLETE`.
4. Iteration 98 verdict is `HUGSIM_BACKGROUND_ONLY_OUTCOME_BRIDGE_COMPLETE`.
5. Iteration 70 contains exactly the five frozen rows with structural-label counts:
   - `foreground_present_late_fire == 2`;
   - `foreground_present_surface_silent == 2`;
   - `foreground_absent_background_only == 1`.
6. Iteration 96 covers exactly the two iteration-70 late-fire rows and no other frozen row.
7. Iteration 97 covers exactly the two iteration-70 surface-silent rows and no other frozen row.
8. Iteration 98 covers exactly the one iteration-70 background-only row and no other frozen row.
9. No source report has infra problems, and no source event has row-level problems.

## Fixed measurements

For each frozen row, compute:

- iteration-70 structural label and support label;
- bridge source (`iter96_late_fire`, `iter97_surface_silent`, or `iter98_background_only`);
- bridge row label;
- first foreground timestamp where available;
- first fire timestamp where available;
- first-fire channel where available;
- whether the row is covered exactly once;
- whether the bridge source is compatible with the iteration-70 structural label.

## Completion labels

- `structural_late_fire_bridge_covered`: an iteration-70 `foreground_present_late_fire` row
  covered exactly once by iteration 96.
- `structural_surface_silent_bridge_covered`: an iteration-70
  `foreground_present_surface_silent` row covered exactly once by iteration 97.
- `structural_background_only_bridge_covered`: an iteration-70
  `foreground_absent_background_only` row covered exactly once by iteration 98.
- `structural_bridge_uncovered`: an iteration-70 structural row has no bridge event.
- `structural_bridge_duplicate_or_incompatible`: an iteration-70 structural row has duplicate
  bridge coverage or a bridge source that does not match its structural label.
- `structural_bridge_coverage_insufficient`: required fields are missing or malformed.

## Verdicts

- `HUGSIM_STRUCTURAL_BRIDGE_COVERAGE_COMPLETE`: all five frozen structural rows classify without
  blocking, exactly two late-fire rows are covered by iteration 96, exactly two surface-silent rows
  are covered by iteration 97, exactly one background-only row is covered by iteration 98, and no
  row is uncovered, duplicated, or incompatible.
- `HUGSIM_STRUCTURAL_BRIDGE_COVERAGE_PARTIAL_COMPLETE`: source checks pass, at least one row is
  uncovered, and no row is insufficient.
- `HUGSIM_STRUCTURAL_BRIDGE_COVERAGE_MIXED_COMPLETE`: source checks pass, at least one row is
  duplicate or incompatible, and no row is insufficient.
- `HUGSIM_STRUCTURAL_BRIDGE_COVERAGE_BLOCKED`: source checks fail or any row is insufficient.

## Claim boundary

Five-row descriptive structural-bridge coverage audit only. This does not claim actor causality,
repair, threshold value, transfer, safety, deployment, robustness, benchmark performance,
population rate, HD-Score invariance, commercial value, real-world behavior, first-responder
behavior, or retuning.
