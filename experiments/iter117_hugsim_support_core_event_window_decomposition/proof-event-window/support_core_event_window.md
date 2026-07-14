# Iteration 117 - HUGSIM support-core event-window decomposition

Verdict: `HUGSIM_SUPPORT_CORE_EVENT_WINDOW_COMPLETE`

## Summary

- `row_count`: `8`
- `problem_row_count`: `0`
- `row_label_counts`: `{'never_supported_before_collision': 1, 'post_fire_support_only': 2, 'pre_fire_support_surface_far_only': 5}`
- `first_support_surface_state_counts`: `{'far': 7}`
- `first_fire_surface_state_counts`: `{'active': 8}`
- `support_phase_counts`: `{'post_fire_pre_collision': 4, 'pre_fire': 13}`
- `support_surface_counts`: `{'active': 2, 'far': 15}`
- `support_object_present_at_fire_count`: `1`
- `support_object_same_as_selected_count`: `0`
- `support_object_same_as_fire_nearest_count`: `1`
- `support_frame_count`: `{'min': 0.0, 'max': 8.0}`
- `pre_fire_support_frame_count`: `{'min': 0.0, 'max': 8.0}`
- `fire_minus_first_support_s`: `{'min': -1.0, 'max': 6.5}`
- `support_object_distance_at_fire_m`: `{'min': 7.624207359121617, 'max': 7.624207359121617}`
- `fire_nearest_distance_m`: `{'min': 7.624207359121617, 'max': 24.812496764606966}`

## Rows

| slot | scenario | run | label | first support | support surface | fire surface | support at fire | same selected | same nearest |
|---:|---|---:|---|---|---|---|---|---|---|
| `1` | `scene-0411-hard-00` | `2` | `pre_fire_support_surface_far_only` | `pre_fire` | `far` | `active` | `False` | `False` | `False` |
| `2` | `scene-0411-extreme-00` | `1` | `pre_fire_support_surface_far_only` | `pre_fire` | `far` | `active` | `True` | `False` | `True` |
| `3` | `scene-0038-hard-00` | `1` | `never_supported_before_collision` | `never_before_collision` | `None` | `active` | `None` | `None` | `None` |
| `4` | `scene-0038-extreme-00` | `1` | `post_fire_support_only` | `post_fire_pre_collision` | `far` | `active` | `False` | `False` | `False` |
| `5` | `scene-0038-extreme-00` | `2` | `post_fire_support_only` | `post_fire_pre_collision` | `far` | `active` | `False` | `False` | `False` |
| `6` | `scene-0383-extreme-00` | `2` | `pre_fire_support_surface_far_only` | `pre_fire` | `far` | `active` | `False` | `False` | `False` |
| `7` | `scene-0411-hard-00` | `1` | `pre_fire_support_surface_far_only` | `pre_fire` | `far` | `active` | `False` | `False` | `False` |
| `8` | `scene-0411-extreme-00` | `2` | `pre_fire_support_surface_far_only` | `pre_fire` | `far` | `active` | `False` | `False` | `False` |

## Boundary

descriptive support-core event-window decomposition of eight committed rows only; no repair, actor-causality, threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate, HD-Score-invariance, real-world behavior, first-responder behavior, acquisition-value, retuning, production, or commercial claim
