# Iteration 104 - HUGSIM provenance batch actor-match support audit

Verdict: `HUGSIM_PROVENANCE_BATCH_ACTOR_MATCH_SUPPORT_NULL`

## Summary

- `slot_count`: `13`
- `completed_rows`: `13`
- `classifiable_foreground`: `1`
- `support_counts`: `{'background_collision_only': 6, 'classifiable_foreground': 1, 'no_monitor_fire': 2, 'post_collision_fire': 4}`
- `bridge_counts`: `{'actor_mismatch': 1}`
- `actor_match`: `0`
- `actor_mismatch`: `1`
- `actor_ambiguous`: `0`
- `min_classifiable_bar`: `4`

## Slots

| slot | scenario | run | support | bridge | distance m | monitor object | foreground |
|---:|---|---:|---|---|---:|---|---|
| `1` | `scene-0013-easy-00` | `1` | `no_monitor_fire` | `None` | `None` | `None` | `None` |
| `2` | `scene-0013-easy-00` | `2` | `no_monitor_fire` | `None` | `None` | `None` | `None` |
| `3` | `scene-0038-medium-01` | `1` | `background_collision_only` | `None` | `None` | `51` | `None` |
| `4` | `scene-0062-medium-00` | `2` | `background_collision_only` | `None` | `None` | `93` | `None` |
| `5` | `scene-0051-easy-00` | `1` | `background_collision_only` | `None` | `None` | `25` | `None` |
| `6` | `scene-0051-easy-00` | `2` | `background_collision_only` | `None` | `None` | `33` | `None` |
| `7` | `scene-0041-extreme-00` | `2` | `post_collision_fire` | `None` | `None` | `8` | `car` |
| `8` | `scene-0062-hard-00` | `1` | `background_collision_only` | `None` | `None` | `35` | `None` |
| `9` | `scene-0013-extreme-00` | `1` | `post_collision_fire` | `None` | `None` | `12` | `car` |
| `10` | `scene-0013-extreme-00` | `2` | `post_collision_fire` | `None` | `None` | `11` | `car` |
| `11` | `scene-0038-hard-00` | `1` | `classifiable_foreground` | `actor_mismatch` | `21.19279787134973` | `21` | `car` |
| `12` | `scene-0038-hard-00` | `2` | `background_collision_only` | `None` | `None` | `21` | `None` |
| `13` | `scene-0138-extreme-00` | `1` | `post_collision_fire` | `None` | `None` | `14` | `car` |

## Boundary

bounded 13-slot actor-match support audit only; no repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate, HD-Score-invariance, real-world behavior, first-responder behavior, acquisition-value, retuning, or production claim
