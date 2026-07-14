# Iteration 99 - HUGSIM structural bridge coverage audit

Verdict: `HUGSIM_STRUCTURAL_BRIDGE_COVERAGE_COMPLETE`

## Summary

- `target_rows`: `5`
- `evaluated_rows`: `5`
- `row_label_counts`: `{'structural_background_only_bridge_covered': 1, 'structural_late_fire_bridge_covered': 2, 'structural_surface_silent_bridge_covered': 2}`
- `bridge_source_counts`: `{'iter96_late_fire': 2, 'iter97_surface_silent': 2, 'iter98_background_only': 1}`
- `covered_rows`: `5`
- `compatible_rows`: `5`
- `uncovered_rows`: `0`
- `duplicate_or_incompatible_rows`: `0`

## Events

| audit id | scenario | structural label | bridge source | bridge label | coverage label | problems |
|---|---|---|---|---|---|---|
| `mixed_extreme` | `scene-0062-extreme-00` | `foreground_present_surface_silent` | `['iter97_surface_silent']` | `['surface_silent_far_never_active_post_foreground_near']` | `structural_surface_silent_bridge_covered` | `[]` |
| `cpa_medium_a` | `scene-0071-medium-00` | `foreground_absent_background_only` | `['iter98_background_only']` | `['background_only_ttc_fire_foreground_absent']` | `structural_background_only_bridge_covered` | `[]` |
| `both_distinct_extreme` | `scene-0138-extreme-00` | `foreground_present_late_fire` | `['iter96_late_fire']` | `['late_fire_with_provenance_ttc_branch']` | `structural_late_fire_bridge_covered` | `[]` |
| `ttc_medium_a` | `scene-0071-medium-01` | `foreground_present_late_fire` | `['iter96_late_fire']` | `['late_fire_with_path_cpa_branch']` | `structural_late_fire_bridge_covered` | `[]` |
| `nofire_hard_control` | `scene-0041-hard-00` | `foreground_present_surface_silent` | `['iter97_surface_silent']` | `['surface_silent_far_never_active_post_foreground_near']` | `structural_surface_silent_bridge_covered` | `[]` |

## Boundary

five-row descriptive structural-bridge coverage audit only; no actor-causality, repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate, HD-Score-invariance, commercial-value, real-world behavior, first-responder behavior, or retuning claim
