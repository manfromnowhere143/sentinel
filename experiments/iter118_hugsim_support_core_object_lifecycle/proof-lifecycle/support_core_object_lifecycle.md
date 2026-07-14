# Iteration 118 - HUGSIM support-core support-object lifecycle audit

Verdict: `HUGSIM_SUPPORT_CORE_OBJECT_LIFECYCLE_COMPLETE`

## Summary

- `row_count`: `8`
- `problem_row_count`: `0`
- `lifecycle_label_counts`: `{'never_supported_reference': 1, 'post_fire_support_only_different_object_active_support': 1, 'post_fire_support_only_far_support': 1, 'pre_fire_object_absent_at_fire': 4, 'pre_fire_object_drifted_outside_support_at_fire': 1}`
- `supported_row_count`: `7`
- `object_present_at_fire_count`: `1`
- `object_supported_at_fire_count`: `0`
- `active_support_same_object_count`: `0`
- `active_support_different_object_count`: `2`
- `object_presence_frame_count`: `{'min': 1.0, 'max': 12.0}`
- `object_support_frame_count`: `{'min': 1.0, 'max': 3.0}`
- `object_support_before_or_at_fire_count`: `{'min': 0.0, 'max': 3.0}`
- `object_distance_at_fire_m`: `{'min': 7.624207359121617, 'max': 7.624207359121617}`

## Rows

| slot | scenario | run | label | object | present at fire | support at fire | same active | diff active | last support <= fire |
|---:|---|---:|---|---:|---|---|---:|---:|---:|
| `1` | `scene-0411-hard-00` | `2` | `pre_fire_object_absent_at_fire` | `2` | `False` | `False` | `0` | `0` | `0.75` |
| `2` | `scene-0411-extreme-00` | `1` | `pre_fire_object_drifted_outside_support_at_fire` | `4` | `True` | `False` | `0` | `0` | `0.75` |
| `3` | `scene-0038-hard-00` | `1` | `never_supported_reference` | `None` | `None` | `None` | `0` | `0` | `None` |
| `4` | `scene-0038-extreme-00` | `1` | `post_fire_support_only_different_object_active_support` | `8` | `False` | `False` | `0` | `1` | `None` |
| `5` | `scene-0038-extreme-00` | `2` | `post_fire_support_only_far_support` | `14` | `False` | `False` | `0` | `0` | `None` |
| `6` | `scene-0383-extreme-00` | `2` | `pre_fire_object_absent_at_fire` | `2` | `False` | `False` | `0` | `0` | `0.75` |
| `7` | `scene-0411-hard-00` | `1` | `pre_fire_object_absent_at_fire` | `2` | `False` | `False` | `0` | `0` | `0.75` |
| `8` | `scene-0411-extreme-00` | `2` | `pre_fire_object_absent_at_fire` | `4` | `False` | `False` | `0` | `1` | `0.75` |

## Boundary

descriptive support-core support-object lifecycle audit of eight committed rows only; no repair, actor-causality, threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate, HD-Score-invariance, real-world behavior, first-responder behavior, acquisition-value, retuning, production, or commercial claim
