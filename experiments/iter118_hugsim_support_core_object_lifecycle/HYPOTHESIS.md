# Iteration 118 - HUGSIM support-core support-object lifecycle audit

Frozen after iteration 117 was published and pushed, but before any iteration-118 analyzer,
lifecycle classification, proof artifact, result, handoff update, or claim. This is an offline
object-lifecycle audit over the committed iteration-112 proof plus the committed iteration-117
event-window report. It launches no GPU work, reruns no actor-match classifier, and changes no code
under test.

## Process disclosure

This is not blind. Iteration 117 showed that the first-support frame is released-surface `far` in
all `7` supported rows, the first-fire frame is `active` in all `8` rows, and the first-support
object persists to first fire in only `1/7` supported rows. It also showed that the first-support
object is never the first-fire selected object.

Those are event-window facts only. They do not say whether first-support objects disappear before
fire, remain visible but drift outside the frozen support band, or whether any later active support
belongs to the same object or a different post-fire object. The bars below freeze that lifecycle
audit.

## Research question

For each support-core row:

1. If a first-support object exists, when is that object last present before first fire and before
   first foreground collision?
2. When is that same object last inside the frozen `6.0 m` actor-support band before first fire and
   before first foreground collision?
3. At first fire, is the first-support object absent, present-but-outside-support, or still inside
   support?
4. For support frames with released surface state `active`, is the support object the same as the
   first-support object or a different object?

This iteration may answer only those object-lifecycle facts inside the eight committed rows. It
does not claim why the planner crashed, why Sentinel fired, or whether a repair exists.

## Frozen inputs

- Iteration 117 event-window report:
  `experiments/iter117_hugsim_support_core_event_window_decomposition/proof-event-window/support_core_event_window_report.json`
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

1. Require the iteration-117 report verdict to be
   `HUGSIM_SUPPORT_CORE_EVENT_WINDOW_COMPLETE` and to contain exactly `8` rows.
2. Require each iteration-117 row to have no problems and one of the frozen row labels from
   iteration 117.
3. Load the slot's committed `eval.json` and `sentinel_iter48_decisions.jsonl` from the
   iteration-112 proof root.
4. Reconstruct every decision frame with numeric timestamp `ts <= first_foreground_ts` using the
   same frozen iteration-59 coordinate bridge and the same object propagation rule used by
   iteration 117.
5. For every considered frame, compute both:
   - nearest-object actor support: the nearest propagated monitor object is within `6.0 m` of the
     first foreground collision actor;
   - first-support-object actor support: the iteration-117 `first_support_object_id`, if present
     in that frame, is within `6.0 m` of the first foreground collision actor.
6. For rows with `first_support_phase = never_before_collision`, assign
   `never_supported_reference` and record no object-lifecycle fields beyond row identity and
   first-fire status.
7. For supported rows, record:
   - first-support object id and first-support timestamp;
   - first and last presence timestamps for that object through first foreground collision;
   - last presence timestamp before or at first fire;
   - last object-specific support timestamp before or at first fire;
   - last object-specific support timestamp through first foreground collision;
   - first-fire object-specific distance if the object is present at fire;
   - whether the object is present at fire;
   - whether the object is inside support at fire;
   - counts of active-surface support frames where the nearest support object is the same as the
     first-support object versus a different object.
8. Assign one lifecycle label:
   - `never_supported_reference` for rows with no first-support object;
   - `pre_fire_object_absent_at_fire` for pre-fire support rows where the first-support object is
     not present at first fire;
   - `pre_fire_object_drifted_outside_support_at_fire` for pre-fire support rows where the object
     is present at fire but outside the `6.0 m` band;
   - `pre_fire_object_still_supported_at_fire` for pre-fire support rows where the object is still
     inside the band at fire;
   - `post_fire_support_only_same_object_active_support` for post-fire-support rows with any
     active-surface support frame on the first-support object;
   - `post_fire_support_only_different_object_active_support` for post-fire-support rows with
     active-surface support only on a different object;
   - `post_fire_support_only_far_support` for post-fire-support rows with no active-surface
     support frame.

The lifecycle labels are descriptive partitions of committed logs only. They are not repair
classes.

## Frozen bars

- `HUGSIM_SUPPORT_CORE_OBJECT_LIFECYCLE_INFRA_NULL`: the iteration-117 report has the wrong
  verdict; it does not contain exactly `8` rows; any row lacks required event-window fields; any
  committed slot proof is missing or malformed; first foreground or first fire cannot be
  reconstructed; first-support object lifecycle cannot be computed for a supported row; or any row
  lacks lifecycle-count, lifecycle-timestamp, active-support identity, and row-label fields.
- `HUGSIM_SUPPORT_CORE_OBJECT_LIFECYCLE_COMPLETE`: infrastructure passes and all `8` rows receive
  frozen lifecycle measurements and one lifecycle label.

## Required proof artifacts

- analyzer source plus unit tests;
- `proof-lifecycle/support_core_object_lifecycle_report.json`;
- `proof-lifecycle/support_core_object_lifecycle.md`;
- `proof-lifecycle/analyze_support_core_object_lifecycle.command.txt`.

## Protocol

1. Commit this `HYPOTHESIS.md` alone.
2. Add analyzer/tests; run `ruff check .`, targeted tests, and
   `python3 scripts/validate_docs.py`.
3. Run the analyzer once over the committed iteration-112/117 artifacts.
4. Publish `RESULT.md`, update docs/handoff, run `ruff check .`, `pytest -q`, and
   `python3 scripts/validate_docs.py`, then push.

## Forbidden claims

No repair, actor-causality, threshold-value, transfer, safety, deployment, robustness, benchmark,
population-rate, HD-Score-invariance, real-world behavior, first-responder behavior,
acquisition-value, retuning, production, or commercial claim. Lifecycle labels are descriptive
properties of committed monitor decision logs only.
