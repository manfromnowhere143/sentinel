# Iteration 83 - HUGSIM bridge-supported surface-miss decomposition

Verdict: `HUGSIM_BRIDGE_SUPPORTED_SURFACE_MISS_MIXED_COMPLETE`

## Summary

- `target_objects`: `2`
- `evaluated_objects`: `2`
- `object_label_counts`: `{'bridge_supported_borderline_ttc_only': 1, 'bridge_supported_subthreshold_no_finite_ttc': 1}`
- `bridge_supported_frames`: `18`
- `active_bridge_supported_frames`: `0`
- `borderline_bridge_supported_frames`: `1`
- `finite_ttc_bridge_supported_frames`: `2`

## Objects

| audit id | support id | label | bridge frames | active | borderline | subthreshold | finite ttc | min active cpa margin | min active ttc margin | min borderline ttc margin | problems |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `both_distinct_extreme` | `9` | `bridge_supported_borderline_ttc_only` | `3` | `0` | `1` | `2` | `2` | `17.671817055919078` | `2.276101409133555` | `-0.2238985908664448` | `[]` |
| `ttc_medium_a` | `10` | `bridge_supported_subthreshold_no_finite_ttc` | `15` | `0` | `0` | `15` | `0` | `5.746414433836578` | `None` | `None` | `[]` |

## Boundary

two-object descriptive bridge-supported surface-miss decomposition only; no actor-causality, repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population, HD-Score-invariance, commercial-value, or retuning claim
