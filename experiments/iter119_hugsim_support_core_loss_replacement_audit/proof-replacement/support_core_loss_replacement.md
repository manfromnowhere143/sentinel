# Iteration 119 - HUGSIM support-core support-loss and replacement audit

Verdict: `HUGSIM_SUPPORT_CORE_LOSS_REPLACEMENT_COMPLETE`

## Summary

- `row_count`: `8`
- `problem_row_count`: `0`
- `replacement_label_counts`: `{'never_supported_reference_selected_nearest': 1, 'post_fire_support_selected_nearest': 2, 'pre_fire_drifted_selected_not_nearest': 1, 'pre_fire_lost_absent_selected_nearest': 2, 'pre_fire_lost_absent_selected_not_nearest': 2}`
- `selected_is_fire_nearest_count`: `5`
- `selected_not_fire_nearest_count`: `3`
- `fire_nearest_is_first_support_object_count`: `1`
- `fire_minus_last_support_s`: `{'min': 1.0, 'max': 6.0}`
- `fire_minus_last_presence_s`: `{'min': 0.0, 'max': 4.75}`
- `fire_nearest_distance_m`: `{'min': 7.624207359121617, 'max': 24.812496764606966}`
- `selected_distance_m`: `{'min': 14.472507961609738, 'max': 36.09143899155716}`
- `selected_rank_by_collision_distance`: `{'min': 1.0, 'max': 8.0}`
- `first_support_object_distance_at_fire_m`: `{'min': 7.624207359121617, 'max': 7.624207359121617}`

## Rows

| slot | scenario | run | label | support object | last support gap | last presence gap | fire nearest | selected | rank |
|---:|---|---:|---|---:|---:|---:|---|---|---:|
| `1` | `scene-0411-hard-00` | `2` | `pre_fire_lost_absent_selected_not_nearest` | `2` | `4.25` | `1.25` | `10` / `12.724592460878268` | `12` / `23.793069683037515` | `2` |
| `2` | `scene-0411-extreme-00` | `1` | `pre_fire_drifted_selected_not_nearest` | `4` | `1.0` | `0.0` | `4` / `7.624207359121617` | `2` / `24.59033959495813` | `3` |
| `3` | `scene-0038-hard-00` | `1` | `never_supported_reference_selected_nearest` | `None` | `None` | `None` | `25` / `14.472507961609738` | `25` / `14.472507961609738` | `1` |
| `4` | `scene-0038-extreme-00` | `1` | `post_fire_support_selected_nearest` | `8` | `None` | `None` | `2` / `15.460122021736504` | `2` / `15.460122021736504` | `1` |
| `5` | `scene-0038-extreme-00` | `2` | `post_fire_support_selected_nearest` | `14` | `None` | `None` | `2` / `15.541003639773562` | `2` / `15.541003639773562` | `1` |
| `6` | `scene-0383-extreme-00` | `2` | `pre_fire_lost_absent_selected_not_nearest` | `2` | `6.0` | `4.75` | `18` / `23.221048739940226` | `1` / `36.09143899155716` | `8` |
| `7` | `scene-0411-hard-00` | `1` | `pre_fire_lost_absent_selected_nearest` | `2` | `5.0` | `2.25` | `12` / `23.180715225043926` | `12` / `23.180715225043926` | `1` |
| `8` | `scene-0411-extreme-00` | `2` | `pre_fire_lost_absent_selected_nearest` | `4` | `5.0` | `2.5` | `17` / `24.812496764606966` | `17` / `24.812496764606966` | `1` |

## Boundary

descriptive support-core support-loss and first-fire replacement audit of eight committed rows only; no repair, actor-causality, threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate, HD-Score-invariance, real-world behavior, first-responder behavior, acquisition-value, retuning, production, or commercial claim
