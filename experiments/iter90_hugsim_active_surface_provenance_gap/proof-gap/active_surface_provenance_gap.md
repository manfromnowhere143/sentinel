# Iteration 90 - HUGSIM active-surface provenance gap audit

Verdict: `HUGSIM_ACTIVE_SURFACE_PROVENANCE_GAP_COMPLETE`

## Summary

- `target_rows`: `3`
- `evaluated_rows`: `3`
- `row_label_counts`: `{'active_surface_absent_bridge_supported_nonactive': 2, 'active_surface_present_no_bridge_supported': 1}`
- `active_object_events`: `1`
- `active_object_total`: `1`
- `bridge_supported_object_total`: `11`
- `active_bridge_supported_total`: `0`
- `active_no_bridge_total`: `1`
- `bridge_supported_nonactive_total`: `11`

## Events

| audit id | event | replay ts | objects | active | bridge-supported | active+bridge | active/no-bridge | bridge/non-active | label | problems |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| `both_distinct_extreme` | `pre` | `5.5` | `3` | `0` | `2` | `0` | `0` | `2` | `active_surface_absent_bridge_supported_nonactive` | `[]` |
| `ttc_medium_a` | `pre` | `4.0` | `7` | `0` | `6` | `0` | `0` | `6` | `active_surface_absent_bridge_supported_nonactive` | `[]` |
| `ttc_medium_a` | `active` | `5.75` | `7` | `1` | `3` | `0` | `1` | `3` | `active_surface_present_no_bridge_supported` | `[]` |

## Boundary

three-row descriptive active-surface/provenance gap audit only; no actor-causality, repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population, HD-Score-invariance, commercial-value, real-world behavior, or retuning claim
