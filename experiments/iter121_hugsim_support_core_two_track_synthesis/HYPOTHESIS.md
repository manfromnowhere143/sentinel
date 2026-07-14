# Iteration 121 - HUGSIM support-core two-track synthesis

Frozen after iteration 120 was published and pushed, but before any iteration-121 analyzer,
synthesis classification, proof artifact, result, handoff update, or claim. This is a report-level
synthesis over the committed iteration-118, iteration-119, and iteration-120 reports. It reads no
raw decision logs, launches no GPU work, reruns no actor-match classifier, and changes no code under
test.

## Process disclosure

This is not blind. Iteration 118 showed first-support objects never remain supported at first fire.
Iteration 119 quantified support-loss gaps and first-fire replacement rank. Iteration 120 showed
that all selected first-fire objects are never supported before collision. What remains is to join
those facts into one row-level two-track taxonomy so the support-core mechanism branch has a single
portable map.

Those are descriptive synthesis facts only. The bars below freeze the exact join and label rules.

## Research question

For each of the eight support-core rows:

1. What is the first-support-object lifecycle branch from iteration 118?
2. What is the first-fire replacement branch and selected rank from iteration 119?
3. What is the selected-fire-object lifecycle branch from iteration 120?
4. Does the row preserve a two-track split: early/support-side object is not supported at fire and
   selected/fire-side object is never supported before collision?

This iteration may answer only those report-level synthesis facts inside the eight committed rows.
It does not claim why the planner crashed, why Sentinel fired, or whether a repair exists.

## Frozen inputs

- Iteration 118 support-object lifecycle report:
  `experiments/iter118_hugsim_support_core_object_lifecycle/proof-lifecycle/support_core_object_lifecycle_report.json`
- Iteration 119 support-loss and replacement report:
  `experiments/iter119_hugsim_support_core_loss_replacement_audit/proof-replacement/support_core_loss_replacement_report.json`
- Iteration 120 selected fire-object lifecycle report:
  `experiments/iter120_hugsim_support_core_selected_fire_object_lifecycle/proof-selected/selected_fire_object_lifecycle_report.json`

The analyzer may read only these committed reports. It may not read raw decision logs, raw
`eval.json`, live GPU state, raw box paths, uncommitted files, or any noncommitted simulator
artifact.

## Frozen synthesis rules

For each registered row:

1. Require iteration 118 verdict `HUGSIM_SUPPORT_CORE_OBJECT_LIFECYCLE_COMPLETE`.
2. Require iteration 119 verdict `HUGSIM_SUPPORT_CORE_LOSS_REPLACEMENT_COMPLETE`.
3. Require iteration 120 verdict `HUGSIM_SUPPORT_CORE_SELECTED_FIRE_OBJECT_COMPLETE`.
4. Require all three reports to contain exactly `8` rows and join one-to-one by `slot_id`,
   `scenario`, and `run`.
5. Require every joined row to have no problems.
6. Carry the iteration-118 `lifecycle_label`, iteration-119 `replacement_label`,
   `selected_rank_by_collision_distance`, and iteration-120 `selected_lifecycle_label`.
7. Set `two_track_split` true when:
   - the selected lifecycle label is `selected_never_supported_before_collision`; and
   - the support-object lifecycle label is one of
     `pre_fire_object_absent_at_fire`,
     `pre_fire_object_drifted_outside_support_at_fire`,
     `post_fire_support_only_different_object_active_support`,
     `post_fire_support_only_far_support`, or
     `never_supported_reference`.
8. Assign one synthesis label:
   - `two_track_pre_support_lost_absent_selected_nearest` for absent pre-fire support rows where
     selected is first-fire nearest;
   - `two_track_pre_support_lost_absent_selected_not_nearest` for absent pre-fire support rows
     where selected is not first-fire nearest;
   - `two_track_pre_support_drifted_selected_not_nearest` for drifted pre-fire support rows where
     selected is not first-fire nearest;
   - `two_track_post_fire_support_selected_nearest` for post-fire support rows where selected is
     first-fire nearest;
   - `two_track_never_supported_selected_nearest` for the never-supported reference row where
     selected is first-fire nearest;
   - `two_track_other` for any joined row that does not match the preceding labels.

The labels are descriptive report-level partitions only. They are not repair classes.

## Frozen bars

- `HUGSIM_SUPPORT_CORE_TWO_TRACK_SYNTHESIS_INFRA_NULL`: any input report has the wrong verdict;
  any report does not contain exactly `8` rows; row identity does not join one-to-one; any row lacks
  required lifecycle/replacement fields; any joined row has problems; any row lacks
  `two_track_split` or synthesis label.
- `HUGSIM_SUPPORT_CORE_TWO_TRACK_SYNTHESIS_COMPLETE`: infrastructure passes and all `8` rows
  receive frozen two-track synthesis measurements and one synthesis label.

## Required proof artifacts

- analyzer source plus unit tests;
- `proof-synthesis/support_core_two_track_synthesis_report.json`;
- `proof-synthesis/support_core_two_track_synthesis.md`;
- `proof-synthesis/analyze_support_core_two_track_synthesis.command.txt`.

## Protocol

1. Commit this `HYPOTHESIS.md` alone.
2. Add analyzer/tests; run `ruff check .`, targeted tests, and
   `python3 scripts/validate_docs.py`.
3. Run the analyzer once over the committed iteration-118/119/120 reports.
4. Publish `RESULT.md`, update docs/handoff, run `ruff check .`, `pytest -q`, and
   `python3 scripts/validate_docs.py`, then push.

## Forbidden claims

No repair, actor-causality, threshold-value, transfer, safety, deployment, robustness, benchmark,
population-rate, HD-Score-invariance, real-world behavior, first-responder behavior,
acquisition-value, retuning, production, or commercial claim. Synthesis labels are descriptive
properties of committed reports only.
