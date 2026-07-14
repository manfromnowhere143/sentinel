# Iteration 106 - HUGSIM timing-aware launch manifest

Verdict: `HUGSIM_TIMING_AWARE_LAUNCH_MANIFEST_COMPLETE`

## Summary

- `slot_count`: `13`
- `scenario_sha_bound_count`: `13`
- `stack_gate_count`: `11`
- `selected_dataset_counts`: `{'iter48_easy_medium': 7, 'iter49_hard_extreme': 6}`
- `selected_channel_counts`: `{'cpa_only': 8, 'ttc_only': 5}`
- `selected_tier_counts`: `{'easy': 3, 'extreme': 2, 'hard': 4, 'medium': 4}`
- `selected_timing_counts`: `{'long_lead_fire': 12, 'short_lead_fire': 1}`
- `unique_scenarios`: `['scene-0064-easy-00', 'scene-0064-hard-00', 'scene-0064-medium-01', 'scene-0071-easy-00', 'scene-0071-extreme-00', 'scene-0138-hard-00', 'scene-0138-medium-01', 'scene-0166-easy-00', 'scene-0166-medium-01', 'scene-0411-extreme-00', 'scene-0411-hard-00']`
- `unique_scenario_count`: `11`
- `duplicate_scenarios`: `{'scene-0064-hard-00': 2, 'scene-0138-medium-01': 2}`
- `duplicate_scenario_count`: `2`
- `duplicate_slot_count`: `4`

## Slots

| slot | slot id | scenario | run | dataset | tier | channel | timing | sha source |
|---:|---|---|---:|---|---|---|---|---|
| `1` | `i106_s01_iter48_easy_medium_long_lead_fire_ttc_only_scene_0138_medium_01_r1` | `scene-0138-medium-01` | `1` | `iter48_easy_medium` | `medium` | `ttc_only` | `long_lead_fire` | `iter48` |
| `2` | `i106_s02_iter49_hard_extreme_long_lead_fire_cpa_only_scene_0064_hard_00_r2` | `scene-0064-hard-00` | `2` | `iter49_hard_extreme` | `hard` | `cpa_only` | `long_lead_fire` | `iter49` |
| `3` | `i106_s03_iter48_easy_medium_long_lead_fire_cpa_only_scene_0166_easy_00_r2` | `scene-0166-easy-00` | `2` | `iter48_easy_medium` | `easy` | `cpa_only` | `long_lead_fire` | `iter48` |
| `4` | `i106_s04_iter48_easy_medium_long_lead_fire_ttc_only_scene_0138_medium_01_r2` | `scene-0138-medium-01` | `2` | `iter48_easy_medium` | `medium` | `ttc_only` | `long_lead_fire` | `iter48` |
| `5` | `i106_s05_iter48_easy_medium_long_lead_fire_cpa_only_scene_0064_easy_00_r2` | `scene-0064-easy-00` | `2` | `iter48_easy_medium` | `easy` | `cpa_only` | `long_lead_fire` | `iter48` |
| `6` | `i106_s06_iter48_easy_medium_long_lead_fire_cpa_only_scene_0166_medium_01_r2` | `scene-0166-medium-01` | `2` | `iter48_easy_medium` | `medium` | `cpa_only` | `long_lead_fire` | `iter48` |
| `7` | `i106_s07_iter49_hard_extreme_long_lead_fire_cpa_only_scene_0064_hard_00_r1` | `scene-0064-hard-00` | `1` | `iter49_hard_extreme` | `hard` | `cpa_only` | `long_lead_fire` | `iter49` |
| `8` | `i106_s08_iter49_hard_extreme_long_lead_fire_ttc_only_scene_0411_extreme_00_r1` | `scene-0411-extreme-00` | `1` | `iter49_hard_extreme` | `extreme` | `ttc_only` | `long_lead_fire` | `iter49` |
| `9` | `i106_s09_iter48_easy_medium_long_lead_fire_ttc_only_scene_0071_easy_00_r2` | `scene-0071-easy-00` | `2` | `iter48_easy_medium` | `easy` | `ttc_only` | `long_lead_fire` | `iter48` |
| `10` | `i106_s10_iter49_hard_extreme_short_lead_fire_ttc_only_scene_0411_hard_00_r2` | `scene-0411-hard-00` | `2` | `iter49_hard_extreme` | `hard` | `ttc_only` | `short_lead_fire` | `iter49` |
| `11` | `i106_s11_iter49_hard_extreme_long_lead_fire_cpa_only_scene_0138_hard_00_r1` | `scene-0138-hard-00` | `1` | `iter49_hard_extreme` | `hard` | `cpa_only` | `long_lead_fire` | `iter49` |
| `12` | `i106_s12_iter49_hard_extreme_long_lead_fire_cpa_only_scene_0071_extreme_00_r1` | `scene-0071-extreme-00` | `1` | `iter49_hard_extreme` | `extreme` | `cpa_only` | `long_lead_fire` | `iter49` |
| `13` | `i106_s13_iter48_easy_medium_long_lead_fire_cpa_only_scene_0064_medium_01_r1` | `scene-0064-medium-01` | `1` | `iter48_easy_medium` | `medium` | `cpa_only` | `long_lead_fire` | `iter48` |

## Boundary

offline timing-aware launch-manifest preflight only; no GPU approval, launch authorization, actor-causality, actor-match result, repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate, HD-Score-invariance, real-world behavior, acquisition-value, retuning, production, or commercial claim
