# Iteration 116 - HUGSIM support-core collision-actor timeline audit

Verdict: `HUGSIM_SUPPORT_CORE_COLLISION_ACTOR_TIMELINE_COMPLETE`

## Summary

- `row_count`: `8`
- `problem_row_count`: `0`
- `support_any_count`: `7`
- `first_support_phase_counts`: `{'never_before_collision': 1, 'post_fire_pre_collision': 2, 'pre_fire': 5}`
- `best_phase_counts`: `{'post_fire_pre_collision': 3, 'pre_fire': 5}`
- `support_frame_count`: `{'min': 0.0, 'max': 8.0}`
- `considered_frame_count`: `{'min': 11.0, 'max': 30.0}`
- `best_distance_m`: `{'min': 1.5056697220919042, 'max': 10.051852932919369}`
- `pre_fire_min_distance_m`: `{'min': 1.5056697220919042, 'max': 11.43639711767452}`
- `at_fire_min_distance_m`: `{'min': 7.624207359121617, 'max': 24.812496764606966}`
- `post_fire_pre_collision_min_distance_m`: `{'min': 5.638200876604923, 'max': 24.666640987462266}`

## Rows

| slot | scenario | run | first support | support frames | best phase | best m | best id | frames |
|---:|---|---:|---|---:|---|---:|---|---:|
| `1` | `scene-0411-hard-00` | `2` | `pre_fire` | `1` | `pre_fire` | `2.889279073064421` | `2` | `22` |
| `2` | `scene-0411-extreme-00` | `1` | `pre_fire` | `1` | `pre_fire` | `4.259200249926439` | `4` | `20` |
| `3` | `scene-0038-hard-00` | `1` | `never_before_collision` | `0` | `post_fire_pre_collision` | `10.051852932919369` | `25` | `30` |
| `4` | `scene-0038-extreme-00` | `1` | `post_fire_pre_collision` | `2` | `post_fire_pre_collision` | `5.638200876604923` | `13` | `11` |
| `5` | `scene-0038-extreme-00` | `2` | `post_fire_pre_collision` | `1` | `post_fire_pre_collision` | `5.647095932359166` | `14` | `11` |
| `6` | `scene-0383-extreme-00` | `2` | `pre_fire` | `8` | `pre_fire` | `1.651081390885113` | `3` | `30` |
| `7` | `scene-0411-hard-00` | `1` | `pre_fire` | `2` | `pre_fire` | `1.5056697220919042` | `3` | `25` |
| `8` | `scene-0411-extreme-00` | `2` | `pre_fire` | `2` | `pre_fire` | `3.95802218200769` | `4` | `25` |

## Boundary

descriptive collision-actor monitor-set timeline audit of eight committed support-core rows only; no repair, actor-causality, threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate, HD-Score-invariance, real-world behavior, first-responder behavior, acquisition-value, retuning, production, or commercial claim
