# Iteration 119 - HUGSIM support-core support-loss and replacement audit

Frozen after iteration 118 was published and pushed, but before any iteration-119 analyzer,
replacement classification, proof artifact, result, handoff update, or claim. This is an offline
support-loss and first-fire replacement audit over the committed iteration-112 proof plus the
committed iteration-117 and iteration-118 reports. It launches no GPU work, reruns no actor-match
classifier, and changes no code under test.

## Process disclosure

This is not blind. Iteration 118 showed that first-support objects are never still supported at
first fire (`0/7` supported rows): four pre-fire support objects are absent at fire, one has drifted
outside the frozen support band, and later active support is different-object only. It did not
quantify the exact loss gaps from last same-object support or last same-object presence to first
fire, nor did it identify the first-fire replacement object's distance and relationship to the
selected object.

Those are descriptive support-loss facts only. The bars below freeze the exact replacement audit.

## Research question

For each support-core row:

1. What is the time gap from last first-support-object support to first fire?
2. What is the time gap from last first-support-object presence to first fire?
3. Which object is nearest to the first foreground collision actor at first fire, what is its
   frozen-bridge distance, and is it the selected first-fire object?
4. If the selected object is present at first fire, what is its frozen-bridge distance and rank by
   collision-actor distance?
5. Does the first-fire object set represent an absent/dropped support object, a present-but-drifted
   support object, or a no-prior-support/post-fire-support replacement case?

This iteration may answer only those support-loss and replacement facts inside the eight committed
rows. It does not claim why the planner crashed, why Sentinel fired, or whether a repair exists.

## Frozen inputs

- Iteration 117 event-window report:
  `experiments/iter117_hugsim_support_core_event_window_decomposition/proof-event-window/support_core_event_window_report.json`
- Iteration 118 support-object lifecycle report:
  `experiments/iter118_hugsim_support_core_object_lifecycle/proof-lifecycle/support_core_object_lifecycle_report.json`
- Iteration 112 proof root:
  `experiments/iter112_hugsim_support_core_batch_execution/proof-execution`
- Iteration 59 actor-match analyzer:
  `experiments/iter59_hugsim_actor_match_audit/analyze_actor_match.py`

The analyzer may read only these committed files and the per-slot `eval.json` and
`sentinel_iter48_decisions.jsonl` artifacts under the iteration-112 proof root. It may not read live
GPU state, raw box paths outside committed proof, uncommitted files, or any noncommitted simulator
artifact.

## Frozen replacement rules

For each registered row:

1. Require the iteration-117 report verdict to be
   `HUGSIM_SUPPORT_CORE_EVENT_WINDOW_COMPLETE`.
2. Require the iteration-118 report verdict to be
   `HUGSIM_SUPPORT_CORE_OBJECT_LIFECYCLE_COMPLETE`.
3. Require both reports to contain exactly `8` rows and join one-to-one by `slot_id`, `scenario`,
   and `run`.
4. Require each joined row to have no problems.
5. Load the slot's committed `eval.json` and `sentinel_iter48_decisions.jsonl` from the
   iteration-112 proof root.
6. Reconstruct the first-fire frame object set with the same frozen iteration-59 coordinate bridge
   and object-propagation rule used by iterations 117 and 118.
7. Compute first-fire object distances to the first foreground collision actor, sorted by
   `(distance_m, object_id)`.
8. Carry the iteration-117 `selected_object_id`; require it to be present in the first-fire object
   set.
9. Record:
   - first-fire nearest object id and distance;
   - selected object distance and rank by collision-actor distance;
   - whether selected equals the nearest object;
   - whether nearest equals the first-support object;
   - first-support-object distance at fire if present;
   - `fire_minus_last_support_s` from iteration 118;
   - `fire_minus_last_presence_s` from iteration 118.
10. Assign one replacement label:
    - `never_supported_reference_selected_nearest` if no first-support object existed and the
      selected first-fire object is also nearest;
    - `pre_fire_lost_absent_selected_nearest` if a pre-fire support object is absent at fire and
      selected is nearest;
    - `pre_fire_lost_absent_selected_not_nearest` if a pre-fire support object is absent at fire
      and selected is not nearest;
    - `pre_fire_drifted_selected_not_nearest` if the first-support object is present at fire but
      outside the support band and selected is not nearest;
    - `pre_fire_drifted_selected_nearest` if the first-support object is present at fire but
      outside the support band and selected is nearest;
    - `post_fire_support_selected_nearest` if first support occurs after fire and selected is
      nearest;
    - `post_fire_support_selected_not_nearest` if first support occurs after fire and selected is
      not nearest.

The labels are descriptive partitions of committed logs only. They are not repair classes.

## Frozen bars

- `HUGSIM_SUPPORT_CORE_LOSS_REPLACEMENT_INFRA_NULL`: either input report has the wrong verdict;
  either report does not contain exactly `8` rows; row identity does not join one-to-one; any row
  lacks required event-window or lifecycle fields; any committed slot proof is missing or malformed;
  first foreground or first fire cannot be reconstructed; the selected first-fire object is absent;
  first-fire object distances cannot be computed; or any row lacks replacement label, selected-rank,
  nearest-object, and support-loss-gap fields.
- `HUGSIM_SUPPORT_CORE_LOSS_REPLACEMENT_COMPLETE`: infrastructure passes and all `8` rows receive
  frozen support-loss gaps, first-fire replacement-object measurements, selected-object rank, and
  one replacement label.

## Required proof artifacts

- analyzer source plus unit tests;
- `proof-replacement/support_core_loss_replacement_report.json`;
- `proof-replacement/support_core_loss_replacement.md`;
- `proof-replacement/analyze_support_core_loss_replacement.command.txt`.

## Protocol

1. Commit this `HYPOTHESIS.md` alone.
2. Add analyzer/tests; run `ruff check .`, targeted tests, and
   `python3 scripts/validate_docs.py`.
3. Run the analyzer once over the committed iteration-112/117/118 artifacts.
4. Publish `RESULT.md`, update docs/handoff, run `ruff check .`, `pytest -q`, and
   `python3 scripts/validate_docs.py`, then push.

## Forbidden claims

No repair, actor-causality, threshold-value, transfer, safety, deployment, robustness, benchmark,
population-rate, HD-Score-invariance, real-world behavior, first-responder behavior,
acquisition-value, retuning, production, or commercial claim. Replacement labels are descriptive
properties of committed monitor decision logs only.
