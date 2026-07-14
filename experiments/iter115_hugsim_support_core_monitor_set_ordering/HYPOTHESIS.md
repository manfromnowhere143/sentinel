# Iteration 115 - HUGSIM support-core monitor-set ordering audit

Frozen after iteration 114 was published and pushed, but before any iteration-115 analyzer,
object-set classification, proof artifact, result, handoff update, or claim. This is an offline
audit over the committed iteration-112 proof plus the committed iteration-113/114 reports. It
launches no GPU work, reruns no actor-match classifier, and changes no code under test.

## Process disclosure

This is not blind. Iteration 113 established that all `8/8` support-core rows are
`classifiable_foreground` and all `8/8` bridge labels are `actor_mismatch`. Iteration 114 then
showed the mismatch geometry is `8/8` forward-dominant, with `7/8` monitor objects far behind the
first foreground collision actor under the frozen bridge.

Those are bounded support and descriptive geometry facts only. No monitor-set ordering audit has
been run over these rows before this file. The bars below freeze how object-set and temporal labels
will be computed.

## Research question

For each of the eight support-core actor-mismatch rows, at the first monitor-fire frame:

1. Is the first foreground collision actor represented anywhere in the monitor's logged object set
   under the same frozen coordinate bridge used by iteration 59?
2. Is the selected first-fire monitor object the nearest logged monitor object to that collision
   actor after propagation to the first foreground collision timestamp?
3. What is the temporal lead bucket between first monitor fire and first foreground collision?

This iteration may answer only those object-set and temporal ordering facts inside the eight
committed rows. It does not claim why the planner crashed, why Sentinel fired, or whether a repair
exists.

## Frozen inputs

- Iteration 113 actor-match report:
  `experiments/iter113_hugsim_support_core_actor_match_audit/proof-actor-match/support_core_actor_match_report.json`
- Iteration 114 mismatch-geometry report:
  `experiments/iter114_hugsim_support_core_mismatch_geometry_decomposition/proof-geometry/support_core_mismatch_geometry_report.json`
- Iteration 112 proof root:
  `experiments/iter112_hugsim_support_core_batch_execution/proof-execution`
- Iteration 59 actor-match analyzer:
  `experiments/iter59_hugsim_actor_match_audit/analyze_actor_match.py`

The analyzer may read only these committed files and the per-slot `eval.json` and
`sentinel_iter48_decisions.jsonl` artifacts under the iteration-112 proof root. It may not read live
GPU state, raw box paths outside committed proof, uncommitted files, or any noncommitted simulator
artifact.

## Frozen ordering rules

For each registered row:

1. Require the iteration-113 row to be `classifiable_foreground` and `actor_mismatch`.
2. Require the iteration-114 row to have no problems and the same `slot_id`.
3. Load the slot's committed `eval.json` and `sentinel_iter48_decisions.jsonl` from the
   iteration-112 proof root.
4. Identify the first foreground collision provenance row exactly as iteration 59 does: the
   earliest foreground row with numeric timestamp and numeric `obs_box` position.
5. Identify the first fired monitor decision row exactly as iteration 59 does.
6. Require `first_fire_ts <= first_foreground_ts`; compute `lead_time_s`.
7. Using the first-fire row's logged `l2g_r_mat`, `l2g_t`, object `world`, and object `vel`, propagate
   every logged monitor object by `lead_time_s`, convert it into monitor ego-local frame with the
   iteration-59 bridge, and compare `(monitor_local_y, monitor_local_x)` with the first foreground
   collision actor's HUGSIM `(forward, lateral)` position.
8. Compute the nearest logged monitor object to the first foreground collision actor.
9. Compute the selected object's rank by collision-actor distance, using the selected
   `monitor_object_id` from the iteration-113 report.

Frozen temporal labels:

- `short_lead` if `lead_time_s <= 0.5`;
- `medium_lead` if `0.5 < lead_time_s <= 1.5`;
- `long_lead` if `lead_time_s > 1.5`.

Frozen object-set labels:

- `nearest_actor_match` if nearest object distance is `<= 3.0 m`;
- `nearest_actor_ambiguous` if nearest object distance is in `(3.0 m, 6.0 m]`;
- `nearest_actor_mismatch` if nearest object distance is `> 6.0 m`.

Frozen selection labels:

- `selected_is_nearest` if the iteration-113 selected object is the nearest object to the collision
  actor;
- `selected_not_nearest` otherwise.

Frozen combined labels:

- `whole_set_mismatch_selected_nearest` if nearest object distance is `> 6.0 m` and the selected
  object is nearest;
- `whole_set_mismatch_selected_not_nearest` if nearest object distance is `> 6.0 m` and the
  selected object is not nearest;
- `nonselected_collision_candidate_available` if nearest object distance is `<= 6.0 m` and the
  selected object is not nearest;
- `selected_collision_candidate` if nearest object distance is `<= 6.0 m` and the selected object is
  nearest.

The `3.0 m` and `6.0 m` thresholds are frozen from the iteration-59 actor-match thresholds and are
not new model or monitor thresholds.

## Frozen bars

- `HUGSIM_SUPPORT_CORE_MONITOR_SET_ORDERING_INFRA_NULL`: either input report has the wrong verdict;
  the reports do not contain exactly `8` matching `slot_id` rows; any row is not an iteration-113
  classifiable foreground actor mismatch; any committed slot proof is missing or malformed; the
  first foreground row or first fired monitor row cannot be reconstructed; the selected
  `monitor_object_id` is absent from the first-fire object set; first fire is after first foreground
  collision; or any row lacks frozen temporal, object-set, selection, and combined labels.
- `HUGSIM_SUPPORT_CORE_MONITOR_SET_ORDERING_COMPLETE`: infrastructure passes and all `8` rows
  receive frozen temporal, object-set, selection, and combined labels.

## Required proof artifacts

- analyzer source plus unit tests;
- `proof-ordering/support_core_monitor_set_ordering_report.json`;
- `proof-ordering/support_core_monitor_set_ordering.md`;
- `proof-ordering/analyze_support_core_monitor_set_ordering.command.txt`.

## Protocol

1. Commit this `HYPOTHESIS.md` alone.
2. Add analyzer/tests; run `ruff check .`, targeted tests, and
   `python3 scripts/validate_docs.py`.
3. Run the analyzer once over the committed iteration-112/113/114 artifacts.
4. Publish `RESULT.md`, update docs/handoff, run `ruff check .`, `pytest -q`, and
   `python3 scripts/validate_docs.py`, then push.

## Forbidden claims

No repair, actor-causality, threshold-value, transfer, safety, deployment, robustness, benchmark,
population-rate, HD-Score-invariance, real-world behavior, first-responder behavior,
acquisition-value, retuning, production, or commercial claim. Object-set labels are descriptive
properties of the eight committed first-fire object sets only.
