# Iteration 59 - HUGSIM actor-match support audit

Verdict: `ACTOR_MATCH_AUDIT_COMPLETE`

## Summary

- `completed_rows`: `8`
- `classifiable_foreground`: `3`
- `support_counts`: `{'background_collision_only': 1, 'classifiable_foreground': 3, 'no_monitor_fire': 2, 'post_collision_fire': 2}`
- `bridge_counts`: `{'actor_mismatch': 3}`

## Episodes

- `ttc_extreme_short` / `scene-0038-extreme-00`: support `classifiable_foreground`, bridge `actor_mismatch`, distance `15.433032797668899`, problems `[]`
- `mixed_extreme` / `scene-0062-extreme-00`: support `no_monitor_fire`, bridge `None`, distance `None`, problems `[]`
- `both_distinct_extreme` / `scene-0138-extreme-00`: support `post_collision_fire`, bridge `None`, distance `None`, problems `[]`
- `nofire_hard_control` / `scene-0041-hard-00`: support `no_monitor_fire`, bridge `None`, distance `None`, problems `[]`
- `cpa_medium_a` / `scene-0071-medium-00`: support `background_collision_only`, bridge `None`, distance `None`, problems `[]`
- `ttc_medium_a` / `scene-0071-medium-01`: support `post_collision_fire`, bridge `None`, distance `None`, problems `[]`
- `cpa_medium_b` / `scene-0166-medium-00`: support `classifiable_foreground`, bridge `actor_mismatch`, distance `21.986342860073755`, problems `[]`
- `ttc_extreme_b` / `scene-0383-extreme-00`: support `classifiable_foreground`, bridge `actor_mismatch`, distance `37.038033481762156`, problems `[]`

## Boundary

bounded eight-episode actor-match support audit only; no transfer, safety, benchmark, HD-Score-invariance, all-HUGSIM, deployment, or retuning claim
