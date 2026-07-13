# Iteration 90 - HUGSIM active-surface provenance gap audit: HUGSIM_ACTIVE_SURFACE_PROVENANCE_GAP_COMPLETE

Status: `HUGSIM_ACTIVE_SURFACE_PROVENANCE_GAP_COMPLETE` (offline active-surface/provenance gap
audit over the three fixed iteration-87 replay rows).

This iteration launched no GPU work, read no live box state, created no HUGSIM episodes, changed
no thresholds, and did not retune Sentinel. It used only committed iteration-59 proof/report
artifacts and the committed iteration-87 and iteration-89 reports.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer: [`analyze_active_surface_provenance_gap.py`](analyze_active_surface_provenance_gap.py)
- Tests: [`../../tests/test_iter90_active_surface_provenance_gap.py`](../../tests/test_iter90_active_surface_provenance_gap.py)
- Analyzer command: [`proof-gap/analyze_active_surface_provenance_gap.command.txt`](proof-gap/analyze_active_surface_provenance_gap.command.txt)
- JSON report: [`proof-gap/active_surface_provenance_gap_report.json`](proof-gap/active_surface_provenance_gap_report.json)
- Markdown report: [`proof-gap/active_surface_provenance_gap.md`](proof-gap/active_surface_provenance_gap.md)

## Result

The analyzer cross-checked:

- iteration-59 verdict: `ACTOR_MATCH_AUDIT_COMPLETE`;
- iteration-87 verdict: `HUGSIM_INTERVAL_BRIDGE_TIME_SURFACE_REPLAY_MIXED_COMPLETE`;
- iteration-89 verdict: `HUGSIM_JOINT_BRIDGE_SURFACE_NO_ACTIVE_CANDIDATE_SPLIT_COMPLETE`;
- exactly the three fixed iteration-87 replay rows;
- zero active+bridge candidate events in iteration 89.

Summary:

- target rows: `3`;
- evaluated rows: `3`;
- row labels:
  - `active_surface_absent_bridge_supported_nonactive`: `2`;
  - `active_surface_present_no_bridge_supported`: `1`;
- active object events: `1`;
- active objects: `1`;
- bridge-supported objects: `11`;
- active+bridge-supported objects: `0`;
- active/no-bridge objects: `1`;
- bridge-supported non-active objects: `11`.

| audit id | event | replay ts | objects | active | bridge-supported | active+bridge | active/no-bridge | bridge/non-active | label |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `both_distinct_extreme` | `pre` | `5.5` | `3` | `0` | `2` | `0` | `0` | `2` | `active_surface_absent_bridge_supported_nonactive` |
| `ttc_medium_a` | `pre` | `4.0` | `7` | `0` | `6` | `0` | `0` | `6` | `active_surface_absent_bridge_supported_nonactive` |
| `ttc_medium_a` | `active` | `5.75` | `7` | `1` | `3` | `0` | `1` | `3` | `active_surface_present_no_bridge_supported` |

## Interpretation

Iteration 90 confirms the active-side provenance gap at the fixed replay rows. The rows contain
`11` bridge-supported objects, and all `11` are non-active under the released surface at their
replay timestamps. The only active object in the three replay rows is `ttc_medium_a` active-row
object `24`; it has no bridge support (`no_support`, best distance `10.9518 m`) while the
bridge-supported support object `10` remains subthreshold.

The fixed rows therefore do not just lack a hidden active+provenance candidate. They split
directionally: bridge/provenance support lands on non-active objects, while the one active
released-surface object lacks provenance support. This strengthens the mechanism diagnosis as an
active-surface/provenance alignment gap, not a simple object enumeration miss.

## Claim boundary

Three-row descriptive active-surface/provenance gap audit only; no actor-causality, repair,
threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate,
HD-Score-invariance, commercial-value, real-world behavior, first-responder behavior, or retuning
claim.
