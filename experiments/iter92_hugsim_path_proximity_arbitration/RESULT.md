# Iteration 92 - HUGSIM path-proximity arbitration audit: HUGSIM_PATH_PROXIMITY_ARBITRATION_SPLIT_COMPLETE

Status: `HUGSIM_PATH_PROXIMITY_ARBITRATION_SPLIT_COMPLETE` (offline path-proximity/provenance
arbitration audit over the three fixed iteration-91 replay rows).

This iteration launched no GPU work, read no live box state, created no HUGSIM episodes, changed
no thresholds, and did not retune Sentinel. It used only committed iteration-59 proof/report
artifacts and the committed iteration-91 report.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer: [`analyze_path_proximity_arbitration.py`](analyze_path_proximity_arbitration.py)
- Tests: [`../../tests/test_iter92_path_proximity_arbitration.py`](../../tests/test_iter92_path_proximity_arbitration.py)
- Analyzer command: [`proof-arbitration/analyze_path_proximity_arbitration.command.txt`](proof-arbitration/analyze_path_proximity_arbitration.command.txt)
- JSON report: [`proof-arbitration/path_proximity_arbitration_report.json`](proof-arbitration/path_proximity_arbitration_report.json)
- Markdown report: [`proof-arbitration/path_proximity_arbitration.md`](proof-arbitration/path_proximity_arbitration.md)

## Result

The analyzer cross-checked:

- iteration-59 verdict: `ACTOR_MATCH_AUDIT_COMPLETE`;
- iteration-91 verdict: `HUGSIM_ACTIVE_GAP_PATH_PROVENANCE_DECOMPOSITION_COMPLETE`;
- exactly the three fixed iteration-91 replay rows;
- zero active+bridge-supported objects in iteration 91;
- the registered iteration-91 row-label split.

Summary:

- target rows: `3`;
- evaluated rows: `3`;
- row labels:
  - `path_best_no_bridge_provenance_best_nonactive`: `1`;
  - `path_best_bridge_supported_nonactive`: `1`;
  - `path_best_active_no_bridge`: `1`;
- path/provenance same-object events: `0`;
- path/provenance different-object events: `3`;
- bridge-supported objects: `11`.

| audit id | event | replay ts | path best | path state | path bridge | provenance best | provenance state | provenance distance | same object | label |
|---|---|---:|---:|---|---|---:|---|---:|---|---|
| `both_distinct_extreme` | `pre` | `5.5` | `5` | `subthreshold` | `no_support` | `9` | `borderline` | `0.9876` | `False` | `path_best_no_bridge_provenance_best_nonactive` |
| `ttc_medium_a` | `pre` | `4.0` | `19` | `subthreshold` | `ambiguous` | `3` | `subthreshold` | `0.7077` | `False` | `path_best_bridge_supported_nonactive` |
| `ttc_medium_a` | `active` | `5.75` | `24` | `active` | `no_support` | `6` | `subthreshold` | `3.7598` | `False` | `path_best_active_no_bridge` |

## Interpretation

Iteration 92 shows that the path/provenance arbitration object differs in every fixed replay row.
The CPA/path-best object is never the provenance-best object.

The active row is the most important split: `ttc_medium_a` active row object `24` is both
`path_best` and `surface_best` (`min_cpa=1.0010 m`, CPA rank `1`, active CPA margin `-0.4990 m`),
but it is provenance-far (`no_support`, bridge distance `10.9518 m`). The provenance-best object
is object `6`, which is bridge-supported (`ambiguous`, `3.7598 m`) but subthreshold
(`min_cpa=19.4267 m`, CPA rank `5`, no finite TTC).

The two non-active rows split differently but preserve the same arbitration pattern. In
`both_distinct_extreme`, the path-best object `5` is subthreshold and no-support, while
provenance-best object `9` is borderline and bridge-matched. In `ttc_medium_a` pre, path-best
object `19` is itself bridge-supported but still subthreshold, while provenance-best object `3`
is a different subthreshold bridge-supported object.

The fixed rows therefore support a path-proximity/provenance arbitration split: path proximity and
released-surface strength do not select the same logged object as provenance proximity. This is a
mechanism-cause finding only; it is not a repair and does not change any threshold.

## Claim boundary

Three-row descriptive path-proximity/provenance arbitration audit only; no actor-causality,
repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate,
HD-Score-invariance, commercial-value, real-world behavior, first-responder behavior, or retuning
claim.
