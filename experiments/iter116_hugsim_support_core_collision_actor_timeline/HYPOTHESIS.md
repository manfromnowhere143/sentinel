# Iteration 116 - HUGSIM support-core collision-actor timeline audit

Frozen after iteration 115 was published and pushed, but before any iteration-116 analyzer,
timeline classification, proof artifact, result, handoff update, or claim. This is an offline
timeline audit over the committed iteration-112 proof plus the committed iteration-115 report. It
launches no GPU work, reruns no actor-match classifier, and changes no code under test.

## Process disclosure

This is not blind. Iteration 115 showed that at first monitor fire, all `8/8` support-core rows are
whole-set mismatches: the nearest logged monitor object is still outside the frozen `6.0 m`
actor-support band after propagation to the first foreground collision timestamp. It did not test
whether a close collision-actor candidate appeared before first fire, after first fire, or never
appeared before collision.

Those are bounded first-fire object-set facts only. No pre-collision timeline audit has been run
over these eight rows before this file. The bars below freeze how timeline labels will be computed.

## Research question

For each of the eight support-core mismatch rows, scanning every committed monitor decision frame
from the beginning of the episode through the first foreground collision timestamp:

1. Does any logged monitor object come within the frozen `6.0 m` actor-support band of the first
   foreground collision actor under the same coordinate bridge used by iteration 59?
2. If yes, does the first close candidate appear before first fire, at first fire, or after first
   fire but before collision?
3. What is the closest monitor-object distance to the collision actor before collision?

This iteration may answer only those timeline facts inside the eight committed rows. It does not
claim why the planner crashed, why Sentinel fired, or whether a repair exists.

## Frozen inputs

- Iteration 115 monitor-set ordering report:
  `experiments/iter115_hugsim_support_core_monitor_set_ordering/proof-ordering/support_core_monitor_set_ordering_report.json`
- Iteration 112 proof root:
  `experiments/iter112_hugsim_support_core_batch_execution/proof-execution`
- Iteration 59 actor-match analyzer:
  `experiments/iter59_hugsim_actor_match_audit/analyze_actor_match.py`

The analyzer may read only these committed files and the per-slot `eval.json` and
`sentinel_iter48_decisions.jsonl` artifacts under the iteration-112 proof root. It may not read live
GPU state, raw box paths outside committed proof, uncommitted files, or any noncommitted simulator
artifact.

## Frozen timeline rules

For each registered row:

1. Require the iteration-115 row to have no problems and an iteration-115 combined label beginning
   with `whole_set_mismatch`.
2. Load the slot's committed `eval.json` and `sentinel_iter48_decisions.jsonl` from the
   iteration-112 proof root.
3. Identify the first foreground collision provenance row exactly as iteration 59 does: the
   earliest foreground row with numeric timestamp and numeric `obs_box` position.
4. Identify the first fired monitor decision row exactly as iteration 59 does.
5. Consider only decision frames with numeric timestamp `ts <= first_foreground_ts`.
6. For every considered frame, propagate every logged monitor object by
   `first_foreground_ts - ts`, convert it into monitor ego-local frame with the iteration-59
   bridge, and compare `(monitor_local_y, monitor_local_x)` with the first foreground collision
   actor's HUGSIM `(forward, lateral)` position.
7. For each frame, record the nearest object distance to the collision actor.
8. A frame has `actor_support` if nearest object distance is `<= 6.0 m`.
9. The first support phase is the earliest actor-support frame, with phase labels:
   - `pre_fire` if `ts < first_fire_ts`;
   - `at_fire` if `ts == first_fire_ts`;
   - `post_fire_pre_collision` if `first_fire_ts < ts <= first_foreground_ts`;
   - `never_before_collision` if no actor-support frame exists.
10. The best phase is the phase of the minimum nearest-object distance before collision.

The `6.0 m` threshold is frozen from the iteration-59 actor-mismatch threshold and is not a new
model or monitor threshold. The equality test for `at_fire` uses the exact timestamps committed in
the decision log.

## Frozen bars

- `HUGSIM_SUPPORT_CORE_COLLISION_ACTOR_TIMELINE_INFRA_NULL`: the iteration-115 report has the wrong
  verdict; it does not contain exactly `8` rows; any row lacks a whole-set mismatch label; any
  committed slot proof is missing or malformed; the first foreground row or first fired monitor row
  cannot be reconstructed; no decision frame exists at or before first foreground collision; a
  frame's nearest-object distance cannot be computed; or any row lacks first-support, best-phase,
  and distance-summary labels.
- `HUGSIM_SUPPORT_CORE_COLLISION_ACTOR_TIMELINE_COMPLETE`: infrastructure passes and all `8` rows
  receive frozen first-support phase, best-distance phase, support-frame counts, and distance
  summaries.

## Required proof artifacts

- analyzer source plus unit tests;
- `proof-timeline/support_core_collision_actor_timeline_report.json`;
- `proof-timeline/support_core_collision_actor_timeline.md`;
- `proof-timeline/analyze_support_core_collision_actor_timeline.command.txt`.

## Protocol

1. Commit this `HYPOTHESIS.md` alone.
2. Add analyzer/tests; run `ruff check .`, targeted tests, and
   `python3 scripts/validate_docs.py`.
3. Run the analyzer once over the committed iteration-112/115 artifacts.
4. Publish `RESULT.md`, update docs/handoff, run `ruff check .`, `pytest -q`, and
   `python3 scripts/validate_docs.py`, then push.

## Forbidden claims

No repair, actor-causality, threshold-value, transfer, safety, deployment, robustness, benchmark,
population-rate, HD-Score-invariance, real-world behavior, first-responder behavior,
acquisition-value, retuning, production, or commercial claim. Timeline labels are descriptive
properties of committed monitor decision logs only.
