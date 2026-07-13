# Iteration 91 - HUGSIM active-gap geometry decomposition: HUGSIM_ACTIVE_GAP_PATH_PROVENANCE_DECOMPOSITION_COMPLETE

Status: `HUGSIM_ACTIVE_GAP_PATH_PROVENANCE_DECOMPOSITION_COMPLETE` (offline active-gap geometry
decomposition over the three fixed iteration-90 replay rows).

This iteration launched no GPU work, read no live box state, created no HUGSIM episodes, changed
no thresholds, and did not retune Sentinel. It used only committed iteration-59 proof/report
artifacts and the committed iteration-90 report.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer: [`analyze_active_gap_geometry.py`](analyze_active_gap_geometry.py)
- Tests: [`../../tests/test_iter91_active_gap_geometry.py`](../../tests/test_iter91_active_gap_geometry.py)
- Analyzer command: [`proof-geometry/analyze_active_gap_geometry.command.txt`](proof-geometry/analyze_active_gap_geometry.command.txt)
- JSON report: [`proof-geometry/active_gap_geometry_report.json`](proof-geometry/active_gap_geometry_report.json)
- Markdown report: [`proof-geometry/active_gap_geometry.md`](proof-geometry/active_gap_geometry.md)

## Result

The analyzer cross-checked:

- iteration-59 verdict: `ACTOR_MATCH_AUDIT_COMPLETE`;
- iteration-90 verdict: `HUGSIM_ACTIVE_SURFACE_PROVENANCE_GAP_COMPLETE`;
- exactly the three fixed iteration-90 replay rows;
- zero active+bridge-supported objects in iteration 90;
- the registered iteration-90 row-label split.

Summary:

- target rows: `3`;
- evaluated rows: `3`;
- row labels:
  - `provenance_near_path_inactive`: `2`;
  - `path_active_provenance_far_with_bridge_nonactive`: `1`;
- active object events: `1`;
- active objects: `1`;
- bridge-supported objects: `11`;
- active+bridge-supported objects: `0`;
- bridge-supported non-active objects: `11`.

| audit id | event | replay ts | active | bridge-supported | active+bridge | nearest active bridge band | nearest active bridge distance | nearest bridge state | nearest bridge distance | label |
|---|---|---:|---:|---:|---:|---|---:|---|---:|---|
| `both_distinct_extreme` | `pre` | `5.5` | `0` | `2` | `0` | `None` | `None` | `borderline` | `0.9876` | `provenance_near_path_inactive` |
| `ttc_medium_a` | `pre` | `4.0` | `0` | `6` | `0` | `None` | `None` | `subthreshold` | `3.2793` | `provenance_near_path_inactive` |
| `ttc_medium_a` | `active` | `5.75` | `1` | `3` | `0` | `no_support` | `10.9518` | `subthreshold` | `4.2468` | `path_active_provenance_far_with_bridge_nonactive` |

## Interpretation

Iteration 91 makes the Iter90 split geometric. The two rows with no active object still contain
bridge-supported objects: `both_distinct_extreme` has nearest bridge object `9` as borderline with
`0.9876 m` bridge distance, and `ttc_medium_a` pre has nearest bridge object `19` as subthreshold
with `3.2793 m` bridge distance. These are provenance-near but path-inactive rows.

The active `ttc_medium_a` row is the complementary case. Object `24` is active on path geometry
(`min_cpa=1.0010 m`, CPA rank `1`) but provenance-far (`no_support`, bridge distance `10.9518 m`).
The nearest bridge-supported object by surface margin is object `10`, which is provenance-near
(`ambiguous`, `4.2468 m`) but subthreshold (`min_cpa=12.1434 m`, CPA rank `3`, no finite TTC).

The fixed rows therefore support a path-vs-provenance geometry decomposition: released active
surface follows path-near geometry, while foreground/provenance support points to different
objects that are not active under the frozen released surface.

## Claim boundary

Three-row descriptive active-gap geometry decomposition only; no actor-causality, repair,
threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate,
HD-Score-invariance, commercial-value, real-world behavior, first-responder behavior, or retuning
claim.
