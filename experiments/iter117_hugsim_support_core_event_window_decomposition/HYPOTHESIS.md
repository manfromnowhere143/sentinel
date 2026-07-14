# Iteration 117 - HUGSIM support-core event-window decomposition

Frozen after iteration 116 was published and pushed, but before any iteration-117 analyzer,
event-window classification, proof artifact, result, handoff update, or claim. This is an offline
event-window decomposition over the committed iteration-112 proof plus the committed iteration-115
and iteration-116 reports. It launches no GPU work, reruns no actor-match classifier, and changes
no code under test.

## Process disclosure

This is not blind. Iteration 115 showed that at first monitor fire all `8/8` support-core rows are
whole-set mismatches: no first-fire monitor object lies inside the frozen `6.0 m` actor-support
band. Iteration 116 then showed that `7/8` rows have at least one close collision-actor candidate
somewhere before the first foreground collision, with first support split across `pre_fire`,
`post_fire_pre_collision`, and `never_before_collision`.

Those are timeline facts only. They do not explain why close-candidate frames and first-fire
frames separate. The bars below freeze a descriptive event-window audit of that separation.

## Research question

For each of the eight support-core mismatch rows, using the same committed decision logs and frozen
iteration-59 bridge:

1. What is the released monitor's frame-level CPA/TTC surface state at the first-support frame and
   the first-fire frame?
2. Does the first-support object identity persist to first fire, and if so what is its propagated
   distance to the first foreground collision actor at first fire?
3. Does the first-support object match the first-fire selected object or the first-fire nearest
   object?
4. How many support frames occur before fire, at fire, and after fire but before collision, and how
   do those support frames split by released surface state?

This iteration may answer only those event-window facts inside the eight committed rows. It does
not claim why the planner crashed, why Sentinel fired, or whether a repair exists.

## Frozen inputs

- Iteration 115 monitor-set ordering report:
  `experiments/iter115_hugsim_support_core_monitor_set_ordering/proof-ordering/support_core_monitor_set_ordering_report.json`
- Iteration 116 timeline report:
  `experiments/iter116_hugsim_support_core_collision_actor_timeline/proof-timeline/support_core_collision_actor_timeline_report.json`
- Iteration 112 proof root:
  `experiments/iter112_hugsim_support_core_batch_execution/proof-execution`
- Iteration 59 actor-match analyzer:
  `experiments/iter59_hugsim_actor_match_audit/analyze_actor_match.py`

The analyzer may read only these committed files and the per-slot `eval.json` and
`sentinel_iter48_decisions.jsonl` artifacts under the iteration-112 proof root. It may not read live
GPU state, raw box paths outside committed proof, uncommitted files, or any noncommitted simulator
artifact.

## Frozen event-window rules

For each registered row:

1. Require the iteration-115 row to have no problems and a `combined_label` beginning with
   `whole_set_mismatch`.
2. Require the iteration-116 row to have no problems and matching `slot_id`, `scenario`, and `run`.
3. Load the slot's committed `eval.json` and `sentinel_iter48_decisions.jsonl` from the
   iteration-112 proof root.
4. Reconstruct every decision frame with numeric timestamp `ts <= first_foreground_ts` exactly as
   iteration 116 did: propagate every logged object to the first foreground collision timestamp,
   convert it into monitor ego-local frame with the iteration-59 bridge, and compare it with the
   first foreground collision actor's HUGSIM `(forward, lateral)` position.
5. A frame has `actor_support` when its nearest propagated monitor object is within the frozen
   `6.0 m` actor-support band. This threshold is inherited from iteration 59 and is not a new
   monitor threshold.
6. For every considered frame, compute the released frame-level surface state from the committed
   row fields and row-local `params`:
   - `active` if `min_cpa <= cpa_margin` or finite `min_ttc <= ttc_thresh`;
   - `borderline` if not active and either `min_cpa <= 3.0 m` or finite `min_ttc <= 5.0 s`;
   - `far` otherwise.
7. Also record the committed boolean `fired` and `brake` fields for the frame. These are descriptive
   latch/action fields, not independent causal labels.
8. The event frames are:
   - first support frame from iteration 116, if any;
   - first fired monitor frame from the committed decision log;
   - first foreground collision timestamp frame if it exists in the decision log.
9. At first fire, compute:
   - selected object id from iteration 115;
   - nearest object id and distance under the same frozen bridge;
   - whether the first-support object is present in the first-fire object set;
   - the first-support object's first-fire distance if present;
   - whether the first-support object equals the selected object;
   - whether the first-support object equals the first-fire nearest object.
10. Count support frames by phase (`pre_fire`, `at_fire`, `post_fire_pre_collision`) and by surface
    state (`active`, `borderline`, `far`).
11. Assign one row label:
    - `never_supported_before_collision` if iteration 116 found no support frame;
    - `post_fire_support_only` if the first support phase is `post_fire_pre_collision`;
    - `pre_fire_support_surface_active` if support exists before first fire and any pre-fire
      support frame is `active`;
    - `pre_fire_support_surface_borderline_only` if support exists before first fire, no pre-fire
      support frame is `active`, and at least one pre-fire support frame is `borderline`;
    - `pre_fire_support_surface_far_only` if support exists before first fire and all pre-fire
      support frames are `far`.

The row labels are descriptive partitions of committed logs only. They are not repair classes.

## Frozen bars

- `HUGSIM_SUPPORT_CORE_EVENT_WINDOW_INFRA_NULL`: the iteration-115 or iteration-116 report has the
  wrong verdict; either report does not contain exactly `8` rows; row identity does not join
  one-to-one by `slot_id`; any row lacks the required whole-set mismatch and timeline labels; any
  committed slot proof is missing or malformed; first foreground or first fire cannot be
  reconstructed; the first-fire frame cannot be matched; released surface state cannot be computed;
  or any row lacks event-window, identity-persistence, support-count, and row-label fields.
- `HUGSIM_SUPPORT_CORE_EVENT_WINDOW_COMPLETE`: infrastructure passes and all `8` rows receive
  frozen event-window measurements, support-frame surface counts, identity-persistence fields, and
  one row label.

## Required proof artifacts

- analyzer source plus unit tests;
- `proof-event-window/support_core_event_window_report.json`;
- `proof-event-window/support_core_event_window.md`;
- `proof-event-window/analyze_support_core_event_window.command.txt`.

## Protocol

1. Commit this `HYPOTHESIS.md` alone.
2. Add analyzer/tests; run `ruff check .`, targeted tests, and
   `python3 scripts/validate_docs.py`.
3. Run the analyzer once over the committed iteration-112/115/116 artifacts.
4. Publish `RESULT.md`, update docs/handoff, run `ruff check .`, `pytest -q`, and
   `python3 scripts/validate_docs.py`, then push.

## Forbidden claims

No repair, actor-causality, threshold-value, transfer, safety, deployment, robustness, benchmark,
population-rate, HD-Score-invariance, real-world behavior, first-responder behavior,
acquisition-value, retuning, production, or commercial claim. Event-window labels are descriptive
properties of committed monitor decision logs only.
