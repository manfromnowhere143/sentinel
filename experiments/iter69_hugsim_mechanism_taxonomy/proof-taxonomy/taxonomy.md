# Iteration 69 - HUGSIM mechanism taxonomy synthesis

Verdict: `HUGSIM_MECHANISM_TAXONOMY_COMPLETE`

## Summary

- `total_rows`: `8`
- `structural_rows`: `5`
- `classifiable_rows`: `3`
- `refined_classifiable_rows`: `3`
- `unrefined_classifiable_rows`: `0`
- `mechanism_counts`: `{'background_collision_only': 1, 'no_monitor_fire': 2, 'nontrigger_visible_never_hazard': 1, 'post_collision_fire': 2, 'same_object_late_fire_after_best_bridge': 1, 'split_object_visible_never_active_fire_before_best_bridge': 1}`

## Taxonomy

| audit id | scenario | iteration-59 support | mechanism | refined | evidence |
|---|---|---|---|---:|---|
| `ttc_extreme_short` | `scene-0038-extreme-00` | `classifiable_foreground` | `same_object_late_fire_after_best_bridge` | `True` | iter61:no_monitor_object_support, iter64:pre_contact_object_match, iter65:matched_object_subthreshold, iter66:target_object_ever_active_hazard, iter67:same_object_target_trigger_match, iter68:fire_gap_best_before_fire |
| `mixed_extreme` | `scene-0062-extreme-00` | `no_monitor_fire` | `no_monitor_fire` | `False` | iter59:no_monitor_fire |
| `both_distinct_extreme` | `scene-0138-extreme-00` | `post_collision_fire` | `post_collision_fire` | `False` | iter59:post_collision_fire |
| `nofire_hard_control` | `scene-0041-hard-00` | `no_monitor_fire` | `no_monitor_fire` | `False` | iter59:no_monitor_fire |
| `cpa_medium_a` | `scene-0071-medium-00` | `background_collision_only` | `background_collision_only` | `False` | iter59:background_collision_only |
| `ttc_medium_a` | `scene-0071-medium-01` | `post_collision_fire` | `post_collision_fire` | `False` | iter59:post_collision_fire |
| `cpa_medium_b` | `scene-0166-medium-00` | `classifiable_foreground` | `split_object_visible_never_active_fire_before_best_bridge` | `True` | iter61:no_monitor_object_support, iter64:pre_contact_object_match, iter65:matched_object_subthreshold, iter66:target_object_visible_never_active, iter67:split_target_match_trigger_match, iter68:fire_gap_best_after_fire |
| `ttc_extreme_b` | `scene-0383-extreme-00` | `classifiable_foreground` | `nontrigger_visible_never_hazard` | `True` | iter61:nontrigger_object_match, iter63:visible_never_hazard |

## Boundary

eight-row evidence synthesis over committed HUGSIM audit reports only; no actor-causality, repair, transfer, safety, deployment, robustness, benchmark, population, HD-Score-invariance, commercial-value, or retuning claim
