# Iteration 89 - HUGSIM joint bridge/surface candidate audit: HUGSIM_JOINT_BRIDGE_SURFACE_NO_ACTIVE_CANDIDATE_SPLIT_COMPLETE

Status: `HUGSIM_JOINT_BRIDGE_SURFACE_NO_ACTIVE_CANDIDATE_SPLIT_COMPLETE` (offline full-object
joint bridge/surface candidate audit over the three fixed iteration-87 replay rows).

This iteration launched no GPU work, read no live box state, created no HUGSIM episodes, changed
no thresholds, and did not retune Sentinel. It used only committed iteration-59 proof/report
artifacts and the committed iteration-85, iteration-87, and iteration-88 reports.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer: [`analyze_joint_bridge_surface_candidate.py`](analyze_joint_bridge_surface_candidate.py)
- Tests: [`../../tests/test_iter89_joint_bridge_surface_candidate.py`](../../tests/test_iter89_joint_bridge_surface_candidate.py)
- Analyzer command: [`proof-candidates/analyze_joint_bridge_surface_candidate.command.txt`](proof-candidates/analyze_joint_bridge_surface_candidate.command.txt)
- JSON report: [`proof-candidates/joint_bridge_surface_candidate_report.json`](proof-candidates/joint_bridge_surface_candidate_report.json)
- Markdown report: [`proof-candidates/joint_bridge_surface_candidate.md`](proof-candidates/joint_bridge_surface_candidate.md)

## Result

The analyzer cross-checked:

- iteration-59 verdict: `ACTOR_MATCH_AUDIT_COMPLETE`;
- iteration-85 verdict: `HUGSIM_PATH_HORIZON_BRIDGE_TIMING_SPLIT_COMPLETE`;
- iteration-87 verdict: `HUGSIM_INTERVAL_BRIDGE_TIME_SURFACE_REPLAY_MIXED_COMPLETE`;
- iteration-88 verdict: `HUGSIM_BRIDGE_SURFACE_MARGIN_RESIDUAL_SPLIT_COMPLETE`;
- exactly the three fixed iteration-87 replay rows.

Summary:

- target rows: `3`;
- evaluated rows: `3`;
- row labels:
  - `no_active_bridge_candidate_support_borderline`: `1`;
  - `no_active_bridge_candidate_support_subthreshold`: `2`;
- active + bridge-supported candidate events: `0`;
- bridge-supported objects across the three replay rows: `11`.

| audit id | event | replay ts | objects | bridge-supported objects | active+bridge objects | support class | support bridge | label |
|---|---|---:|---:|---:|---:|---|---|---|
| `both_distinct_extreme` | `pre` | `5.5` | `3` | `2` | `0` | `borderline_bridge_supported` | `match` | `no_active_bridge_candidate_support_borderline` |
| `ttc_medium_a` | `pre` | `4.0` | `7` | `6` | `0` | `subthreshold_bridge_supported` | `match` | `no_active_bridge_candidate_support_subthreshold` |
| `ttc_medium_a` | `active` | `5.75` | `7` | `3` | `0` | `subthreshold_bridge_supported` | `ambiguous` | `no_active_bridge_candidate_support_subthreshold` |

## Interpretation

Iteration 89 closes the immediate simple object-arbitration counterfactual for the fixed replay
rows. Across all logged objects in the three replay rows, bridge support is common (`11` objects),
but no object is both active under the released surface and bridge-supported. The
`both_distinct_extreme` support object is bridge-supported only at borderline. The two
`ttc_medium_a` support rows are bridge-supported but subthreshold. In the active `ttc_medium_a`
replay row, one object is active, but it has no bridge support.

The fixed rows therefore do not contain a hidden "correct" active+provenance candidate under the
frozen surface. The mechanism remains a joint evidence conflict: provenance can identify nearby
support objects, and the released surface can identify path-geometry hazards, but those signals do
not coincide on an active object in these rows.

## Claim boundary

Three-row descriptive joint bridge/surface candidate audit only; no actor-causality, repair,
threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate,
HD-Score-invariance, commercial-value, real-world behavior, first-responder behavior, or retuning
claim.
