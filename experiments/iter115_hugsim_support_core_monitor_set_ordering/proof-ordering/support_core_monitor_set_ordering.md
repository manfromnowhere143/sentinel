# Iteration 115 - HUGSIM support-core monitor-set ordering audit

Verdict: `HUGSIM_SUPPORT_CORE_MONITOR_SET_ORDERING_COMPLETE`

## Summary

- `row_count`: `8`
- `problem_row_count`: `0`
- `temporal_label_counts`: `{'long_lead': 2, 'medium_lead': 2, 'short_lead': 4}`
- `object_set_label_counts`: `{'nearest_actor_mismatch': 8}`
- `selection_label_counts`: `{'selected_is_nearest': 5, 'selected_not_nearest': 3}`
- `combined_label_counts`: `{'whole_set_mismatch_selected_nearest': 5, 'whole_set_mismatch_selected_not_nearest': 3}`
- `lead_time_s`: `{'min': 0.25, 'max': 3.25}`
- `nearest_distance_m`: `{'min': 7.624207359121617, 'max': 24.812496764606966}`
- `selected_distance_m`: `{'min': 14.472507961609738, 'max': 36.09143899155716}`
- `first_fire_object_count`: `{'min': 1.0, 'max': 10.0}`

## Rows

| slot | scenario | run | lead | object-set | selection | combined | nearest id | nearest m | selected rank | objects |
|---:|---|---:|---|---|---|---|---|---:|---:|---:|
| `1` | `scene-0411-hard-00` | `2` | `short_lead` | `nearest_actor_mismatch` | `selected_not_nearest` | `whole_set_mismatch_selected_not_nearest` | `10` | `12.724592460878268` | `2` | `3` |
| `2` | `scene-0411-extreme-00` | `1` | `long_lead` | `nearest_actor_mismatch` | `selected_not_nearest` | `whole_set_mismatch_selected_not_nearest` | `4` | `7.624207359121617` | `3` | `3` |
| `3` | `scene-0038-hard-00` | `1` | `long_lead` | `nearest_actor_mismatch` | `selected_is_nearest` | `whole_set_mismatch_selected_nearest` | `25` | `14.472507961609738` | `1` | `5` |
| `4` | `scene-0038-extreme-00` | `1` | `medium_lead` | `nearest_actor_mismatch` | `selected_is_nearest` | `whole_set_mismatch_selected_nearest` | `2` | `15.460122021736504` | `1` | `5` |
| `5` | `scene-0038-extreme-00` | `2` | `medium_lead` | `nearest_actor_mismatch` | `selected_is_nearest` | `whole_set_mismatch_selected_nearest` | `2` | `15.541003639773562` | `1` | `4` |
| `6` | `scene-0383-extreme-00` | `2` | `short_lead` | `nearest_actor_mismatch` | `selected_not_nearest` | `whole_set_mismatch_selected_not_nearest` | `18` | `23.221048739940226` | `8` | `10` |
| `7` | `scene-0411-hard-00` | `1` | `short_lead` | `nearest_actor_mismatch` | `selected_is_nearest` | `whole_set_mismatch_selected_nearest` | `12` | `23.180715225043926` | `1` | `1` |
| `8` | `scene-0411-extreme-00` | `2` | `short_lead` | `nearest_actor_mismatch` | `selected_is_nearest` | `whole_set_mismatch_selected_nearest` | `17` | `24.812496764606966` | `1` | `1` |

## Boundary

descriptive monitor-set ordering audit of eight committed support-core mismatch rows only; no repair, actor-causality, threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate, HD-Score-invariance, real-world behavior, first-responder behavior, acquisition-value, retuning, production, or commercial claim
