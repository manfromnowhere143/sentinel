# Iteration 73 - HUGSIM structural margin transition audit

Verdict: `HUGSIM_MARGIN_TRANSITION_SPLIT_COMPLETE`

## Summary

- `target_rows`: `4`
- `evaluated_rows`: `4`
- `row_label_counts`: `{'late_prefire_near_postcontact_active': 2, 'silent_far_never_active': 2}`
- `silent_far_never_active_rows`: `2`
- `late_prefire_near_postcontact_active_rows`: `2`

## Rows

| audit id | scenario | structural | label | first near offset | first active offset | active channel | problems |
|---|---|---|---|---:|---:|---|---|
| `mixed_extreme` | `scene-0062-extreme-00` | `foreground_present_surface_silent` | `silent_far_never_active` | `0.25` | `None` | `None` | `[]` |
| `nofire_hard_control` | `scene-0041-hard-00` | `foreground_present_surface_silent` | `silent_far_never_active` | `3.5` | `None` | `None` | `[]` |
| `both_distinct_extreme` | `scene-0138-extreme-00` | `foreground_present_late_fire` | `late_prefire_near_postcontact_active` | `-0.25` | `1.75` | `ttc` | `[]` |
| `ttc_medium_a` | `scene-0071-medium-01` | `foreground_present_late_fire` | `late_prefire_near_postcontact_active` | `-0.75` | `1.75` | `cpa` | `[]` |

## Boundary

four-row descriptive margin-transition audit only; no actor-causality, repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population, HD-Score-invariance, commercial-value, or retuning claim
