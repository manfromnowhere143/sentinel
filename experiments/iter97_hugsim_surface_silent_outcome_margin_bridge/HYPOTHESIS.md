# Iteration 97 - HUGSIM surface-silent outcome margin bridge

## Research question

Do the two fixed foreground-present surface-silent rows join to far-margin and never-active
timeline evidence, explaining the no-fire outcome as a descriptive margin/outcome bridge rather
than a near active-surface miss?

## Scope

This is an offline report-level bridge audit. It may read only these committed reports:

- `experiments/iter70_hugsim_structural_timing_audit/proof-structural/structural_report.json`
- `experiments/iter71_hugsim_surface_silent_margin_audit/proof-margin/margin_report.json`
- `experiments/iter73_hugsim_margin_transition_audit/proof-transition/transition_report.json`

It must not read raw decision logs, launch Docker, touch the GPU box, run HUGSIM, modify
thresholds, tune parameters, or infer counterfactual vehicle outcomes.

## Frozen rows

This audit is limited to the two iteration-70 foreground-present surface-silent rows:

1. `mixed_extreme` / `scene-0062-extreme-00`;
2. `nofire_hard_control` / `scene-0041-hard-00`.

## Frozen source checks

The analyzer must stop as blocked unless all checks pass:

1. Iteration 70 verdict is `HUGSIM_STRUCTURAL_TIMING_TAXONOMY_COMPLETE`.
2. Iteration 71 verdict is `HUGSIM_SURFACE_SILENT_MARGIN_COMPLETE`.
3. Iteration 73 verdict is `HUGSIM_MARGIN_TRANSITION_SPLIT_COMPLETE`.
4. Both frozen rows exist exactly once in all three reports.
5. Iteration 70 rows have:
   - `structural_label == foreground_present_surface_silent`;
   - `iter59_support_label == no_monitor_fire`;
   - `pre_or_at_foreground_fire == false`.
6. Iteration 71 rows have `row_label == surface_silent_far_margin`.
7. Iteration 73 rows have `row_label == silent_far_never_active`.
8. No source row has row-level problems.

## Fixed measurements

For each frozen row, compute:

- first foreground timestamp;
- foreground count;
- fired frame count;
- first fire timestamp;
- closest CPA margin from iteration 71;
- closest TTC margin from iteration 71;
- active CPA/TTC frame counts from iteration 71;
- first-near offset from iteration 73;
- first-active offset and relation from iteration 73;
- pre-foreground-near flags from iteration 73.

## Completion labels

- `surface_silent_far_never_active_post_foreground_near`: the row is foreground-present
  surface-silent, has zero fired frames, no first fire, iteration-71 far margin, zero active
  CPA/TTC frames, iteration-73 never-active label, no pre-foreground near flag, and a positive
  first-near offset after foreground contact.
- `surface_silent_far_never_active_no_near`: the row is foreground-present surface-silent, has
  zero fired frames, no first fire, iteration-71 far margin, zero active CPA/TTC frames,
  iteration-73 never-active label, no pre-foreground near flag, and no first-near timestamp.
- `surface_silent_outcome_margin_mixed`: source checks pass, but a row does not match either
  surface-silent bridge label.
- `surface_silent_outcome_margin_insufficient`: required fields are missing or malformed.

## Verdicts

- `HUGSIM_SURFACE_SILENT_OUTCOME_MARGIN_BRIDGE_COMPLETE`: both frozen rows classify without
  blocking as surface-silent far/never-active rows, and at least one row has a positive
  post-foreground first-near offset.
- `HUGSIM_SURFACE_SILENT_OUTCOME_MARGIN_NO_NEAR_COMPLETE`: both rows classify as
  `surface_silent_far_never_active_no_near`.
- `HUGSIM_SURFACE_SILENT_OUTCOME_MARGIN_MIXED_COMPLETE`: at least one row classifies as
  `surface_silent_outcome_margin_mixed` and none are insufficient.
- `HUGSIM_SURFACE_SILENT_OUTCOME_MARGIN_BLOCKED`: source checks fail or any row is insufficient.

## Claim boundary

Two-row descriptive surface-silent outcome/margin bridge only. This does not claim actor
causality, repair, threshold value, transfer, safety, deployment, robustness, benchmark
performance, population rate, HD-Score invariance, commercial value, real-world behavior,
first-responder behavior, or retuning.
