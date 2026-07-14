# Iteration 111 - HUGSIM support-core launch manifest

Verdict: `HUGSIM_SUPPORT_CORE_LAUNCH_MANIFEST_COMPLETE`

## Summary

- `slot_count`: `8`
- `scenario_sha_bound_count`: `8`
- `stack_gate_count`: `11`
- `selected_dataset_counts`: `{'iter49_hard_extreme': 8}`
- `selected_channel_counts`: `{'ttc_only': 8}`
- `selected_tier_counts`: `{'extreme': 5, 'hard': 3}`
- `selected_timing_counts`: `{'long_lead_fire': 3, 'short_lead_fire': 5}`
- `selected_design_label_counts`: `{'exact_ttc_classifiable_anchor': 3, 'ttc_classifiable_scenario_analogue': 5}`
- `unique_scenarios`: `['scene-0038-extreme-00', 'scene-0038-hard-00', 'scene-0383-extreme-00', 'scene-0411-extreme-00', 'scene-0411-hard-00']`
- `unique_scenario_count`: `5`
- `duplicate_scenarios`: `{'scene-0038-extreme-00': 2, 'scene-0411-extreme-00': 2, 'scene-0411-hard-00': 2}`
- `duplicate_scenario_count`: `3`
- `duplicate_slot_count`: `6`

## Slots

| slot | slot id | scenario | run | dataset | tier | role | timing | sha source |
|---:|---|---|---:|---|---|---|---|---|
| `1` | `i111_s01_iter49_hard_extreme_exact_ttc_classifiable_anchor_short_lead_fire_ttc_only_scene_0411_hard_00_r2` | `scene-0411-hard-00` | `2` | `iter49_hard_extreme` | `hard` | `exact_ttc_classifiable_anchor` | `short_lead_fire` | `iter49` |
| `2` | `i111_s02_iter49_hard_extreme_exact_ttc_classifiable_anchor_long_lead_fire_ttc_only_scene_0411_extreme_00_r1` | `scene-0411-extreme-00` | `1` | `iter49_hard_extreme` | `extreme` | `exact_ttc_classifiable_anchor` | `long_lead_fire` | `iter49` |
| `3` | `i111_s03_iter49_hard_extreme_exact_ttc_classifiable_anchor_long_lead_fire_ttc_only_scene_0038_hard_00_r1` | `scene-0038-hard-00` | `1` | `iter49_hard_extreme` | `hard` | `exact_ttc_classifiable_anchor` | `long_lead_fire` | `iter49` |
| `4` | `i111_s04_iter49_hard_extreme_ttc_classifiable_scenario_analogue_short_lead_fire_ttc_only_scene_0038_extreme_00_r1` | `scene-0038-extreme-00` | `1` | `iter49_hard_extreme` | `extreme` | `ttc_classifiable_scenario_analogue` | `short_lead_fire` | `iter49` |
| `5` | `i111_s05_iter49_hard_extreme_ttc_classifiable_scenario_analogue_short_lead_fire_ttc_only_scene_0038_extreme_00_r2` | `scene-0038-extreme-00` | `2` | `iter49_hard_extreme` | `extreme` | `ttc_classifiable_scenario_analogue` | `short_lead_fire` | `iter49` |
| `6` | `i111_s06_iter49_hard_extreme_ttc_classifiable_scenario_analogue_short_lead_fire_ttc_only_scene_0383_extreme_00_r2` | `scene-0383-extreme-00` | `2` | `iter49_hard_extreme` | `extreme` | `ttc_classifiable_scenario_analogue` | `short_lead_fire` | `iter49` |
| `7` | `i111_s07_iter49_hard_extreme_ttc_classifiable_scenario_analogue_short_lead_fire_ttc_only_scene_0411_hard_00_r1` | `scene-0411-hard-00` | `1` | `iter49_hard_extreme` | `hard` | `ttc_classifiable_scenario_analogue` | `short_lead_fire` | `iter49` |
| `8` | `i111_s08_iter49_hard_extreme_ttc_classifiable_scenario_analogue_long_lead_fire_ttc_only_scene_0411_extreme_00_r2` | `scene-0411-extreme-00` | `2` | `iter49_hard_extreme` | `extreme` | `ttc_classifiable_scenario_analogue` | `long_lead_fire` | `iter49` |

## Boundary

offline support-core launch-manifest preflight only; no GPU approval, launch authorization, actor-causality, actor-match result, repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate, HD-Score-invariance, real-world behavior, acquisition-value, retuning, production, or commercial claim
