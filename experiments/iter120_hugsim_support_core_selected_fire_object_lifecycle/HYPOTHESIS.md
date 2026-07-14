# Iteration 120 - HUGSIM support-core selected fire-object backward lifecycle audit

Frozen after iteration 119 was published and pushed, but before any iteration-120 analyzer,
selected-object lifecycle classification, proof artifact, result, handoff update, or claim. This is
an offline backward lifecycle audit of the selected first-fire object over the committed
iteration-112 proof plus the committed iteration-119 replacement report. It launches no GPU work,
reruns no actor-match classifier, and changes no code under test.

## Process disclosure

This is not blind. Iteration 119 showed that first-fire replacements remain outside the frozen
support band in every row, even when the selected first-fire object is nearest. It did not test
whether the selected first-fire object had ever entered the frozen actor-support band earlier in
the decision log, or whether selected-nearest rows differ from selected-not-nearest rows in their
backward lifecycle.

Those are descriptive selected-object lifecycle facts only. The bars below freeze the exact audit.

## Research question

For each support-core row, following the selected first-fire object backward and forward through the
committed decision log up to first foreground collision:

1. When does the selected first-fire object first appear before first fire?
2. Does the selected first-fire object ever enter the frozen `6.0 m` actor-support band before
   first fire?
3. Does it enter the frozen support band after fire but before first foreground collision?
4. What are its closest distances to the first foreground collision actor before fire, at fire, and
   before collision?
5. How many frames containing that selected object are frame-level released-surface `active`,
   `borderline`, or `far` before first fire?

This iteration may answer only those selected-object lifecycle facts inside the eight committed
rows. It does not claim why the planner crashed, why Sentinel fired, or whether a repair exists.

## Frozen inputs

- Iteration 119 support-loss and replacement report:
  `experiments/iter119_hugsim_support_core_loss_replacement_audit/proof-replacement/support_core_loss_replacement_report.json`
- Iteration 112 proof root:
  `experiments/iter112_hugsim_support_core_batch_execution/proof-execution`
- Iteration 59 actor-match analyzer:
  `experiments/iter59_hugsim_actor_match_audit/analyze_actor_match.py`

The analyzer may read only these committed files and the per-slot `eval.json` and
`sentinel_iter48_decisions.jsonl` artifacts under the iteration-112 proof root. It may not read live
GPU state, raw box paths outside committed proof, uncommitted files, or any noncommitted simulator
artifact.

## Frozen lifecycle rules

For each registered row:

1. Require the iteration-119 report verdict to be
   `HUGSIM_SUPPORT_CORE_LOSS_REPLACEMENT_COMPLETE` and to contain exactly `8` rows.
2. Require each iteration-119 row to have no problems and a `selected_object_id`.
3. Load the slot's committed `eval.json` and `sentinel_iter48_decisions.jsonl` from the
   iteration-112 proof root.
4. Reconstruct every decision frame with numeric timestamp `ts <= first_foreground_ts` using the
   same frozen iteration-59 coordinate bridge and object-propagation rule used by iterations
   117-119.
5. For every frame where the selected first-fire object is present, compute its propagated distance
   to the first foreground collision actor at the first foreground timestamp.
6. Compute frame-level released surface state from committed `min_cpa`, `min_ttc`, and row-local
   `params` exactly as iteration 117 did:
   - `active` if `min_cpa <= cpa_margin` or finite `min_ttc <= ttc_thresh`;
   - `borderline` if not active and either `min_cpa <= 3.0 m` or finite `min_ttc <= 5.0 s`;
   - `far` otherwise.
7. Record:
   - first and last selected-object presence timestamps before first foreground collision;
   - first selected-object presence timestamp before or at first fire;
   - closest selected-object distance before fire, at fire, and before collision;
   - first and last selected-object support timestamps before fire and before collision, if any;
   - selected-object support-frame counts by phase (`pre_fire`, `at_fire`,
     `post_fire_pre_collision`);
   - selected-object containing-frame surface-state counts by phase.
8. Assign one selected-object lifecycle label:
   - `selected_pre_fire_supported_then_lost_by_fire` if the selected object has support before
     fire but not at fire;
   - `selected_supported_at_fire` if the selected object is inside the support band at fire;
   - `selected_post_fire_support_only` if it has no support before or at fire but has support after
     fire before collision;
   - `selected_never_supported_before_collision` if it never enters support before first
     foreground collision.

The labels are descriptive partitions of committed logs only. They are not repair classes.

## Frozen bars

- `HUGSIM_SUPPORT_CORE_SELECTED_FIRE_OBJECT_INFRA_NULL`: the iteration-119 report has the wrong
  verdict; it does not contain exactly `8` rows; any row lacks selected-object or replacement
  fields; any committed slot proof is missing or malformed; first foreground or first fire cannot
  be reconstructed; the selected first-fire object is not present at first fire; selected-object
  lifecycle distances cannot be computed; or any row lacks selected-object lifecycle label,
  support counts, surface counts, and closest-distance fields.
- `HUGSIM_SUPPORT_CORE_SELECTED_FIRE_OBJECT_COMPLETE`: infrastructure passes and all `8` rows
  receive frozen selected-object lifecycle measurements and one lifecycle label.

## Required proof artifacts

- analyzer source plus unit tests;
- `proof-selected/selected_fire_object_lifecycle_report.json`;
- `proof-selected/selected_fire_object_lifecycle.md`;
- `proof-selected/analyze_selected_fire_object_lifecycle.command.txt`.

## Protocol

1. Commit this `HYPOTHESIS.md` alone.
2. Add analyzer/tests; run `ruff check .`, targeted tests, and
   `python3 scripts/validate_docs.py`.
3. Run the analyzer once over the committed iteration-112/119 artifacts.
4. Publish `RESULT.md`, update docs/handoff, run `ruff check .`, `pytest -q`, and
   `python3 scripts/validate_docs.py`, then push.

## Forbidden claims

No repair, actor-causality, threshold-value, transfer, safety, deployment, robustness, benchmark,
population-rate, HD-Score-invariance, real-world behavior, first-responder behavior,
acquisition-value, retuning, production, or commercial claim. Selected-object lifecycle labels are
descriptive properties of committed monitor decision logs only.
