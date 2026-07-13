# Iteration 89 - HUGSIM joint bridge/surface candidate audit

Verdict: `HUGSIM_JOINT_BRIDGE_SURFACE_NO_ACTIVE_CANDIDATE_SPLIT_COMPLETE`

## Summary

- `target_rows`: `3`
- `evaluated_rows`: `3`
- `row_label_counts`: `{'no_active_bridge_candidate_support_borderline': 1, 'no_active_bridge_candidate_support_subthreshold': 2}`
- `active_bridge_candidate_events`: `0`
- `bridge_supported_object_total`: `11`

## Events

| audit id | event | replay ts | objects | bridge-supported | active+bridge | support class | support state | support bridge | label | problems |
|---|---|---:|---:|---:|---:|---|---|---|---|---|
| `both_distinct_extreme` | `pre` | `5.5` | `3` | `2` | `0` | `borderline_bridge_supported` | `borderline` | `match` | `no_active_bridge_candidate_support_borderline` | `[]` |
| `ttc_medium_a` | `pre` | `4.0` | `7` | `6` | `0` | `subthreshold_bridge_supported` | `subthreshold` | `match` | `no_active_bridge_candidate_support_subthreshold` | `[]` |
| `ttc_medium_a` | `active` | `5.75` | `7` | `3` | `0` | `subthreshold_bridge_supported` | `subthreshold` | `ambiguous` | `no_active_bridge_candidate_support_subthreshold` | `[]` |

## Boundary

three-row descriptive joint bridge/surface candidate audit only; no actor-causality, repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population, HD-Score-invariance, commercial-value, real-world behavior, or retuning claim
