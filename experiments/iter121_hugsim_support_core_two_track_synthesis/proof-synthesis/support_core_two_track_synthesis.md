# Iteration 121 - HUGSIM support-core two-track synthesis

Verdict: `HUGSIM_SUPPORT_CORE_TWO_TRACK_SYNTHESIS_COMPLETE`

## Summary

- `row_count`: `8`
- `problem_row_count`: `0`
- `synthesis_label_counts`: `{'two_track_never_supported_selected_nearest': 1, 'two_track_post_fire_support_selected_nearest': 2, 'two_track_pre_support_drifted_selected_not_nearest': 1, 'two_track_pre_support_lost_absent_selected_nearest': 2, 'two_track_pre_support_lost_absent_selected_not_nearest': 2}`
- `two_track_split_count`: `8`
- `support_lifecycle_counts`: `{'never_supported_reference': 1, 'post_fire_support_only_different_object_active_support': 1, 'post_fire_support_only_far_support': 1, 'pre_fire_object_absent_at_fire': 4, 'pre_fire_object_drifted_outside_support_at_fire': 1}`
- `replacement_label_counts`: `{'never_supported_reference_selected_nearest': 1, 'post_fire_support_selected_nearest': 2, 'pre_fire_drifted_selected_not_nearest': 1, 'pre_fire_lost_absent_selected_nearest': 2, 'pre_fire_lost_absent_selected_not_nearest': 2}`
- `selected_lifecycle_counts`: `{'selected_never_supported_before_collision': 8}`
- `selected_is_fire_nearest_count`: `5`
- `selected_not_fire_nearest_count`: `3`

## Rows

| slot | scenario | run | synthesis | support lifecycle | replacement | selected lifecycle | two-track |
|---:|---|---:|---|---|---|---|---|
| `1` | `scene-0411-hard-00` | `2` | `two_track_pre_support_lost_absent_selected_not_nearest` | `pre_fire_object_absent_at_fire` | `pre_fire_lost_absent_selected_not_nearest` | `selected_never_supported_before_collision` | `True` |
| `2` | `scene-0411-extreme-00` | `1` | `two_track_pre_support_drifted_selected_not_nearest` | `pre_fire_object_drifted_outside_support_at_fire` | `pre_fire_drifted_selected_not_nearest` | `selected_never_supported_before_collision` | `True` |
| `3` | `scene-0038-hard-00` | `1` | `two_track_never_supported_selected_nearest` | `never_supported_reference` | `never_supported_reference_selected_nearest` | `selected_never_supported_before_collision` | `True` |
| `4` | `scene-0038-extreme-00` | `1` | `two_track_post_fire_support_selected_nearest` | `post_fire_support_only_different_object_active_support` | `post_fire_support_selected_nearest` | `selected_never_supported_before_collision` | `True` |
| `5` | `scene-0038-extreme-00` | `2` | `two_track_post_fire_support_selected_nearest` | `post_fire_support_only_far_support` | `post_fire_support_selected_nearest` | `selected_never_supported_before_collision` | `True` |
| `6` | `scene-0383-extreme-00` | `2` | `two_track_pre_support_lost_absent_selected_not_nearest` | `pre_fire_object_absent_at_fire` | `pre_fire_lost_absent_selected_not_nearest` | `selected_never_supported_before_collision` | `True` |
| `7` | `scene-0411-hard-00` | `1` | `two_track_pre_support_lost_absent_selected_nearest` | `pre_fire_object_absent_at_fire` | `pre_fire_lost_absent_selected_nearest` | `selected_never_supported_before_collision` | `True` |
| `8` | `scene-0411-extreme-00` | `2` | `two_track_pre_support_lost_absent_selected_nearest` | `pre_fire_object_absent_at_fire` | `pre_fire_lost_absent_selected_nearest` | `selected_never_supported_before_collision` | `True` |

## Boundary

descriptive support-core two-track synthesis of committed reports only; no repair, actor-causality, threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate, HD-Score-invariance, real-world behavior, first-responder behavior, acquisition-value, retuning, production, or commercial claim
