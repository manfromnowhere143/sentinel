# Iteration 74 - HUGSIM late-fire delay barrier audit

Verdict: `HUGSIM_LATE_FIRE_CROSS_CHANNEL_DELAY_COMPLETE`

## Summary

- `target_rows`: `2`
- `evaluated_rows`: `2`
- `row_label_counts`: `{'cross_channel_late_activation': 2}`
- `cross_channel_late_activation_rows`: `2`
- `same_channel_late_activation_rows`: `0`
- `dual_near_late_activation_rows`: `0`

## Rows

| audit id | scenario | label | pre near channels | first active channels | first active offset | closest pre TTC margin | closest pre CPA margin | problems |
|---|---|---|---|---|---:|---:|---:|---|
| `both_distinct_extreme` | `scene-0138-extreme-00` | `cross_channel_late_activation` | `['cpa']` | `['ttc']` | `1.75` | `None` | `0.5354586791404059` | `[]` |
| `ttc_medium_a` | `scene-0071-medium-01` | `cross_channel_late_activation` | `['ttc']` | `['cpa']` | `1.75` | `0.7742114811096417` | `3.0137256446355645` | `[]` |

## Boundary

two-row descriptive delay-barrier audit only; no actor-causality, repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population, HD-Score-invariance, commercial-value, or retuning claim
