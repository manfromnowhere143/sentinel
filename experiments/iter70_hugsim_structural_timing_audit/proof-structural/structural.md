# Iteration 70 - HUGSIM structural-row timing audit

Verdict: `HUGSIM_STRUCTURAL_TIMING_TAXONOMY_COMPLETE`

## Summary

- `target_rows`: `5`
- `evaluated_rows`: `5`
- `structural_label_counts`: `{'foreground_absent_background_only': 1, 'foreground_present_late_fire': 2, 'foreground_present_surface_silent': 2}`
- `surface_silent_rows`: `2`
- `late_fire_rows`: `2`
- `background_only_rows`: `1`

## Rows

| audit id | scenario | support | structural label | first foreground | first fire | delta | problems |
|---|---|---|---|---:|---:|---:|---|
| `mixed_extreme` | `scene-0062-extreme-00` | `no_monitor_fire` | `foreground_present_surface_silent` | `4.75` | `None` | `None` | `[]` |
| `both_distinct_extreme` | `scene-0138-extreme-00` | `post_collision_fire` | `foreground_present_late_fire` | `5.25` | `7.0` | `1.75` | `[]` |
| `nofire_hard_control` | `scene-0041-hard-00` | `no_monitor_fire` | `foreground_present_surface_silent` | `2.5` | `None` | `None` | `[]` |
| `cpa_medium_a` | `scene-0071-medium-00` | `background_collision_only` | `foreground_absent_background_only` | `None` | `3.5` | `None` | `[]` |
| `ttc_medium_a` | `scene-0071-medium-01` | `post_collision_fire` | `foreground_present_late_fire` | `3.25` | `5.0` | `1.75` | `[]` |

## Boundary

five-row structural timing/support audit only; no actor-causality, repair, transfer, safety, deployment, robustness, benchmark, population, HD-Score-invariance, commercial-value, or retuning claim
