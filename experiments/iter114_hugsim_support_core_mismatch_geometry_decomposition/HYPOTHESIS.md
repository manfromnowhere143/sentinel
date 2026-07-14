# Iteration 114 - HUGSIM support-core mismatch-geometry decomposition

Frozen after iteration 113 was published and pushed, but before any iteration-114 analyzer,
geometry classification, proof artifact, result, handoff update, or claim. This is an offline
decomposition over the committed iteration-113 support-core actor-match report only. It launches no
GPU work, reruns no actor-match classifier, and changes no code under test.

## Process disclosure

This is not blind. Iteration 113 has already published the actor-match support audit:

- `8/8` registered support-core slots were `classifiable_foreground`;
- `8/8` bridge labels were `actor_mismatch`;
- `0` bridge labels were `actor_match`;
- `0` bridge labels were `actor_ambiguous`;
- all `3` exact anchors and all `5` scenario analogues remained classifiable.

Those are bounded support and descriptive bridge-label facts only. No mismatch-geometry
decomposition has been run over the iteration-113 report before this file. The bars below freeze
how geometry labels will be computed.

## Research question

For the eight iteration-113 `actor_mismatch` rows, what is the signed geometry of the mismatch
between:

1. the monitor object's propagated HUGSIM-frame position (`monitor_forward_lateral`); and
2. the first foreground collision actor's HUGSIM-frame position (`hugsim_forward_lateral`)?

This iteration may answer only the descriptive geometry of the eight already-classified mismatch
vectors. It does not claim why the planner crashed, why Sentinel fired, or whether a repair exists.

## Frozen input

- Iteration 113 actor-match report:
  `experiments/iter113_hugsim_support_core_actor_match_audit/proof-actor-match/support_core_actor_match_report.json`

The analyzer may read only that committed report. It may not read live GPU state, raw box paths,
raw episode directories, uncommitted files, or any data not already summarized in the iteration-113
report.

## Frozen geometry rules

For each episode row:

1. Require `support_label == "classifiable_foreground"`.
2. Require `bridge_label == "actor_mismatch"`.
3. Require `bridge_distance_m > 6.0`.
4. Require numeric `monitor_forward_lateral = [monitor_forward_m, monitor_lateral_m]`.
5. Require numeric `hugsim_forward_lateral = [hugsim_forward_m, hugsim_lateral_m]`.
6. Compute:
   - `delta_forward_m = monitor_forward_m - hugsim_forward_m`;
   - `delta_lateral_m = monitor_lateral_m - hugsim_lateral_m`;
   - `abs_forward_delta_m = abs(delta_forward_m)`;
   - `abs_lateral_delta_m = abs(delta_lateral_m)`.
7. Classify the signed forward relation:
   - `monitor_far_ahead` if `delta_forward_m > 6.0`;
   - `monitor_far_behind` if `delta_forward_m < -6.0`;
   - `monitor_forward_near` otherwise.
8. Classify the signed lateral relation:
   - `monitor_far_left` if `delta_lateral_m > 6.0`;
   - `monitor_far_right` if `delta_lateral_m < -6.0`;
   - `monitor_lateral_near` otherwise.
9. Classify the dominant component:
   - `forward_dominant` if `abs_forward_delta_m > abs_lateral_delta_m`;
   - `lateral_dominant` if `abs_lateral_delta_m > abs_forward_delta_m`;
   - `balanced` if equal.
10. Classify the combined geometry:
    - `far_behind_lateral_near` for `monitor_far_behind` plus `monitor_lateral_near`;
    - `far_ahead_lateral_near` for `monitor_far_ahead` plus `monitor_lateral_near`;
    - `forward_near_lateral_far` for `monitor_forward_near` plus a far lateral relation;
    - `far_behind_lateral_far` for `monitor_far_behind` plus a far lateral relation;
    - `far_ahead_lateral_far` for `monitor_far_ahead` plus a far lateral relation;
    - `diagonal_near_components` otherwise.

The `6.0 m` threshold is frozen from the iteration-59 actor-mismatch threshold and is not a new
model or monitor threshold.

## Frozen bars

- `HUGSIM_SUPPORT_CORE_MISMATCH_GEOMETRY_INFRA_NULL`: the iteration-113 report is not
  `HUGSIM_SUPPORT_CORE_ACTOR_MATCH_AUDIT_COMPLETE`; the report does not contain exactly `8`
  episode rows; any row is not `classifiable_foreground`; any row is not `actor_mismatch`; any row
  has `bridge_distance_m <= 6.0`; any row lacks numeric monitor/collision coordinates; or the
  geometry label counts do not sum to `8`.
- `HUGSIM_SUPPORT_CORE_MISMATCH_GEOMETRY_COMPLETE`: infrastructure passes and all `8` mismatch
  rows receive frozen forward, lateral, dominant-component, and combined-geometry labels.

## Required proof artifacts

- analyzer source plus unit tests;
- `proof-geometry/support_core_mismatch_geometry_report.json`;
- `proof-geometry/support_core_mismatch_geometry.md`;
- `proof-geometry/analyze_support_core_mismatch_geometry.command.txt`.

## Protocol

1. Commit this `HYPOTHESIS.md` alone.
2. Add analyzer/tests; run `ruff check .`, targeted tests, and
   `python3 scripts/validate_docs.py`.
3. Run the analyzer once over the committed iteration-113 report.
4. Publish `RESULT.md`, update docs/handoff, run `ruff check .`, `pytest -q`, and
   `python3 scripts/validate_docs.py`, then push.

## Forbidden claims

No repair, actor-causality, threshold-value, transfer, safety, deployment, robustness, benchmark,
population-rate, HD-Score-invariance, real-world behavior, first-responder behavior,
acquisition-value, retuning, production, or commercial claim. Geometry labels are descriptive
properties of the eight committed mismatch vectors only.
