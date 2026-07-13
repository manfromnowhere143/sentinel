# Iteration 75 - HUGSIM cross-channel object handoff audit

Verdict: `HUGSIM_CROSS_CHANNEL_OBJECT_SWITCH_COMPLETE`

## Summary

- `target_rows`: `2`
- `evaluated_rows`: `2`
- `row_label_counts`: `{'object_switch_cross_channel_handoff': 2}`
- `object_switch_rows`: `2`
- `same_object_rows`: `0`
- `multiobject_rows`: `0`

## Rows

| audit id | scenario | label | pre channel | pre ids | active channel | active ids | problems |
|---|---|---|---|---|---|---|---|
| `both_distinct_extreme` | `scene-0138-extreme-00` | `object_switch_cross_channel_handoff` | `cpa` | `[5]` | `ttc` | `[9]` | `[]` |
| `ttc_medium_a` | `scene-0071-medium-01` | `object_switch_cross_channel_handoff` | `ttc` | `[6]` | `cpa` | `[24]` | `[]` |

## Boundary

two-row descriptive object-handoff audit only; no actor-causality, repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population, HD-Score-invariance, commercial-value, or retuning claim
