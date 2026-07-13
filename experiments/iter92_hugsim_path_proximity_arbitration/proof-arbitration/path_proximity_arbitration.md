# Iteration 92 - HUGSIM path-proximity arbitration audit

Verdict: `HUGSIM_PATH_PROXIMITY_ARBITRATION_SPLIT_COMPLETE`

## Summary

- `target_rows`: `3`
- `evaluated_rows`: `3`
- `row_label_counts`: `{'path_best_active_no_bridge': 1, 'path_best_bridge_supported_nonactive': 1, 'path_best_no_bridge_provenance_best_nonactive': 1}`
- `path_provenance_same_object_events`: `0`
- `path_provenance_different_object_events`: `3`
- `bridge_supported_object_total`: `11`

## Events

| audit id | event | replay ts | path best | path state | path bridge | provenance best | provenance state | provenance distance | same object | label | problems |
|---|---|---:|---:|---|---|---:|---|---:|---|---|---|
| `both_distinct_extreme` | `pre` | `5.5` | `5` | `subthreshold` | `no_support` | `9` | `borderline` | `0.987644974002337` | `False` | `path_best_no_bridge_provenance_best_nonactive` | `[]` |
| `ttc_medium_a` | `pre` | `4.0` | `19` | `subthreshold` | `ambiguous` | `3` | `subthreshold` | `0.7077149882625609` | `False` | `path_best_bridge_supported_nonactive` | `[]` |
| `ttc_medium_a` | `active` | `5.75` | `24` | `active` | `no_support` | `6` | `subthreshold` | `3.7598179926411346` | `False` | `path_best_active_no_bridge` | `[]` |

## Boundary

three-row descriptive path-proximity/provenance arbitration audit only; no actor-causality, repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population, HD-Score-invariance, commercial-value, real-world behavior, or retuning claim
