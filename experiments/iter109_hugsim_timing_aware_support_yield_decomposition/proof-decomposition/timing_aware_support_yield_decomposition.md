# Iteration 109 - HUGSIM timing-aware support-yield decomposition

Verdict: `HUGSIM_TIMING_AWARE_SUPPORT_YIELD_DECOMPOSITION_COMPLETE`

## Summary

- `slot_count`: `13`
- `residual_counts`: `{'classifiable_success': 2, 'observed_background_only': 6, 'observed_empty_collision_provenance': 1, 'observed_post_collision_fire': 4}`
- `support_counts`: `{'background_collision_only': 6, 'classifiable_foreground': 2, 'no_collision_provenance': 1, 'post_collision_fire': 4}`
- `classifiable_success`: `2`
- `unclassifiable_count`: `11`
- `foreground_absent_or_empty_count`: `7`
- `observed_post_collision_fire_count`: `4`
- `timing_inversion_count`: `4`
- `observed_fire_lead_min_s`: `-6.75`
- `observed_fire_lead_max_s`: `3.0`
- `residual_by_timing`: `{'long_lead_fire': {'classifiable_success': 1, 'observed_background_only': 6, 'observed_empty_collision_provenance': 1, 'observed_post_collision_fire': 4}, 'short_lead_fire': {'classifiable_success': 1}}`
- `residual_by_channel`: `{'cpa_only': {'observed_background_only': 5, 'observed_empty_collision_provenance': 1, 'observed_post_collision_fire': 2}, 'ttc_only': {'classifiable_success': 2, 'observed_background_only': 1, 'observed_post_collision_fire': 2}}`
- `residual_by_dataset`: `{'iter48_easy_medium': {'observed_background_only': 4, 'observed_empty_collision_provenance': 1, 'observed_post_collision_fire': 2}, 'iter49_hard_extreme': {'classifiable_success': 2, 'observed_background_only': 2, 'observed_post_collision_fire': 2}}`
- `infra_problem_count`: `0`

## Slots

| slot | scenario | run | design lead s | observed lead s | support | residual | fire delta s | foreground delta s |
|---:|---|---:|---:|---:|---|---|---:|---:|
| `1` | `scene-0138-medium-01` | `1` | `27.0` | `-2.5` | `post_collision_fire` | `observed_post_collision_fire` | `-1.75` | `-31.25` |
| `2` | `scene-0064-hard-00` | `2` | `5.5` | `None` | `background_collision_only` | `observed_background_only` | `0.75` | `None` |
| `3` | `scene-0166-easy-00` | `2` | `14.5` | `None` | `no_collision_provenance` | `observed_empty_collision_provenance` | `0.0` | `None` |
| `4` | `scene-0138-medium-01` | `2` | `18.0` | `-6.75` | `post_collision_fire` | `observed_post_collision_fire` | `-0.5` | `-25.25` |
| `5` | `scene-0064-easy-00` | `2` | `9.75` | `None` | `background_collision_only` | `observed_background_only` | `11.25` | `None` |
| `6` | `scene-0166-medium-01` | `2` | `13.0` | `None` | `background_collision_only` | `observed_background_only` | `0.0` | `None` |
| `7` | `scene-0064-hard-00` | `1` | `5.25` | `None` | `background_collision_only` | `observed_background_only` | `0.0` | `None` |
| `8` | `scene-0411-extreme-00` | `1` | `4.5` | `3.0` | `classifiable_foreground` | `classifiable_success` | `0.0` | `-1.5` |
| `9` | `scene-0071-easy-00` | `2` | `5.5` | `None` | `background_collision_only` | `observed_background_only` | `1.5` | `None` |
| `10` | `scene-0411-hard-00` | `2` | `0.25` | `0.25` | `classifiable_foreground` | `classifiable_success` | `-0.75` | `-0.75` |
| `11` | `scene-0138-hard-00` | `1` | `4.25` | `-0.75` | `post_collision_fire` | `observed_post_collision_fire` | `0.25` | `-4.75` |
| `12` | `scene-0071-extreme-00` | `1` | `4.0` | `-0.25` | `post_collision_fire` | `observed_post_collision_fire` | `1.25` | `-3.0` |
| `13` | `scene-0064-medium-01` | `1` | `3.0` | `None` | `background_collision_only` | `observed_background_only` | `-0.5` | `None` |

## Boundary

offline timing-aware support-yield decomposition only; no actor-causality, actor-match support upgrade, repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate, HD-Score-invariance, real-world behavior, first-responder behavior, acquisition-value, retuning, production, commercial, schedule-selection, or GPU-approval claim
