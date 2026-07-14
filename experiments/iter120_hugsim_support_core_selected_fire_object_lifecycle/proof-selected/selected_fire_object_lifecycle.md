# Iteration 120 - HUGSIM selected fire-object backward lifecycle audit

Verdict: `HUGSIM_SUPPORT_CORE_SELECTED_FIRE_OBJECT_COMPLETE`

## Summary

- `row_count`: `8`
- `problem_row_count`: `0`
- `selected_lifecycle_label_counts`: `{'selected_never_supported_before_collision': 8}`
- `selected_support_phase_counts`: `{}`
- `selected_supported_before_fire_count`: `0`
- `selected_supported_at_fire_count`: `0`
- `selected_supported_post_fire_count`: `0`
- `selected_presence_frame_count`: `{'min': 3.0, 'max': 30.0}`
- `selected_support_frame_count`: `{'min': 0.0, 'max': 0.0}`
- `selected_pre_fire_closest_distance_m`: `{'min': 9.814849860027191, 'max': 26.576615026308698}`
- `selected_at_fire_distance_m`: `{'min': 14.472507961609738, 'max': 36.09143899155716}`
- `selected_before_collision_closest_distance_m`: `{'min': 9.814849860027191, 'max': 23.793069683037515}`
- `pre_fire_selected_active_frame_count`: `{'min': 0.0, 'max': 0.0}`
- `pre_fire_selected_borderline_frame_count`: `{'min': 0.0, 'max': 9.0}`
- `pre_fire_selected_far_frame_count`: `{'min': 0.0, 'max': 18.0}`

## Rows

| slot | scenario | run | label | selected | rank | pre best | fire m | global best | support phases |
|---:|---|---:|---|---:|---:|---:|---:|---:|---|
| `1` | `scene-0411-hard-00` | `2` | `selected_never_supported_before_collision` | `12` | `2` | `26.576615026308698` | `23.793069683037515` | `23.793069683037515` | `{}` |
| `2` | `scene-0411-extreme-00` | `1` | `selected_never_supported_before_collision` | `2` | `3` | `12.192824650458231` | `24.59033959495813` | `12.192824650458231` | `{}` |
| `3` | `scene-0038-hard-00` | `1` | `selected_never_supported_before_collision` | `25` | `1` | `12.714470083636659` | `14.472507961609738` | `10.051852932919369` | `{}` |
| `4` | `scene-0038-extreme-00` | `1` | `selected_never_supported_before_collision` | `2` | `1` | `9.814849860027191` | `15.460122021736504` | `9.814849860027191` | `{}` |
| `5` | `scene-0038-extreme-00` | `2` | `selected_never_supported_before_collision` | `2` | `1` | `9.846701909939755` | `15.541003639773562` | `9.846701909939755` | `{}` |
| `6` | `scene-0383-extreme-00` | `2` | `selected_never_supported_before_collision` | `1` | `8` | `17.82467248647331` | `36.09143899155716` | `17.82467248647331` | `{}` |
| `7` | `scene-0411-hard-00` | `1` | `selected_never_supported_before_collision` | `12` | `1` | `22.74246925010588` | `23.180715225043926` | `22.74246925010588` | `{}` |
| `8` | `scene-0411-extreme-00` | `2` | `selected_never_supported_before_collision` | `17` | `1` | `21.056817761623456` | `24.812496764606966` | `21.056817761623456` | `{}` |

## Boundary

descriptive support-core selected fire-object backward lifecycle audit of eight committed rows only; no repair, actor-causality, threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate, HD-Score-invariance, real-world behavior, first-responder behavior, acquisition-value, retuning, production, or commercial claim
