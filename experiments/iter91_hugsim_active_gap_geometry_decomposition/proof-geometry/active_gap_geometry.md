# Iteration 91 - HUGSIM active-gap geometry decomposition

Verdict: `HUGSIM_ACTIVE_GAP_PATH_PROVENANCE_DECOMPOSITION_COMPLETE`

## Summary

- `target_rows`: `3`
- `evaluated_rows`: `3`
- `row_label_counts`: `{'path_active_provenance_far_with_bridge_nonactive': 1, 'provenance_near_path_inactive': 2}`
- `active_object_events`: `1`
- `active_object_total`: `1`
- `bridge_supported_object_total`: `11`
- `active_bridge_supported_total`: `0`
- `bridge_supported_nonactive_total`: `11`

## Events

| audit id | event | replay ts | active | bridge-supported | active+bridge | nearest active bridge band | nearest active bridge distance | nearest bridge state | nearest bridge distance | label | problems |
|---|---|---:|---:|---:|---:|---|---:|---|---:|---|---|
| `both_distinct_extreme` | `pre` | `5.5` | `0` | `2` | `0` | `None` | `None` | `borderline` | `0.987644974002337` | `provenance_near_path_inactive` | `[]` |
| `ttc_medium_a` | `pre` | `4.0` | `0` | `6` | `0` | `None` | `None` | `subthreshold` | `3.2792928823035705` | `provenance_near_path_inactive` | `[]` |
| `ttc_medium_a` | `active` | `5.75` | `1` | `3` | `0` | `no_support` | `10.951828022656175` | `subthreshold` | `4.2467564543528615` | `path_active_provenance_far_with_bridge_nonactive` | `[]` |

## Boundary

three-row descriptive active-gap geometry decomposition only; no actor-causality, repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population, HD-Score-invariance, commercial-value, real-world behavior, or retuning claim
