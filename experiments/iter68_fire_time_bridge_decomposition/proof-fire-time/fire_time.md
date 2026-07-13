# Iteration 68 - fire-time bridge decomposition audit

Verdict: `FIRE_TIME_BRIDGE_GAP_TEMPORAL_SPLIT_COMPLETE`

## Summary

- `target_rows`: `2`
- `evaluated_rows`: `2`
- `row_label_counts`: `{'fire_gap_best_after_fire': 1, 'fire_gap_best_before_fire': 1}`
- `before_fire_rows`: `1`
- `after_fire_rows`: `1`
- `median_distance_improvement_m`: `16.86509247184937`

## Rows

- `ttc_extreme_short` / `scene-0038-extreme-00` / trigger `2`: label `fire_gap_best_before_fire`, fire distance `6.927225576937264`, best distance `1.6718236908808954`, best decision `0.25` (before), improvement `5.255401886056369`, problems `[]`
- `cpa_medium_b` / `scene-0166-medium-00` / trigger `1`: label `fire_gap_best_after_fire`, fire distance `19.69826047075051`, best distance `2.833167998901139`, best decision `2.25` (after), improvement `16.86509247184937`, problems `[]`

## Boundary

two-row fire-time bridge decomposition audit only; no transfer, safety, deployment, benchmark, actor-causality, repair, population, HD-Score-invariance, or retuning claim
