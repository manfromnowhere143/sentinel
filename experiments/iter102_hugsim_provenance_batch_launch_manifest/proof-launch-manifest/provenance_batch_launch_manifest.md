# Iteration 102 - HUGSIM provenance batch launch manifest

Verdict: `HUGSIM_PROVENANCE_BATCH_LAUNCH_MANIFEST_COMPLETE`

## Summary

- `slot_count`: `13`
- `selected_new_count`: `12`
- `carried_singleton_count`: `1`
- `scenario_sha_bound_count`: `13`
- `stack_gate_count`: `11`
- `unique_scenarios`: `['scene-0013-easy-00', 'scene-0013-extreme-00', 'scene-0038-hard-00', 'scene-0038-medium-01', 'scene-0041-extreme-00', 'scene-0051-easy-00', 'scene-0062-hard-00', 'scene-0062-medium-00', 'scene-0138-extreme-00']`
- `unique_scenario_count`: `9`
- `duplicate_scenarios`: `{'scene-0013-easy-00': 2, 'scene-0013-extreme-00': 2, 'scene-0038-hard-00': 2, 'scene-0051-easy-00': 2}`
- `duplicate_scenario_count`: `4`
- `duplicate_slot_count`: `8`

## Launch Slots

| slot | slot id | dataset | stratum | scenario | run | sha source | scenario sha |
|---:|---|---|---|---|---:|---|---|
| `1` | `i102_s01_iter48_easy_medium_no_fire_scene_0013_easy_00_r1` | `iter48_easy_medium` | `no_fire` | `scene-0013-easy-00` | `1` | `iter48` | `22d30c2a3dadf59451ff3704b50c412fb6fa74d261ee96dd4e6bf17c9a064735` |
| `2` | `i102_s02_iter48_easy_medium_no_fire_scene_0013_easy_00_r2` | `iter48_easy_medium` | `no_fire` | `scene-0013-easy-00` | `2` | `iter48` | `22d30c2a3dadf59451ff3704b50c412fb6fa74d261ee96dd4e6bf17c9a064735` |
| `3` | `i102_s03_iter48_easy_medium_unique_cpa_object_scene_0038_medium_01_r1` | `iter48_easy_medium` | `unique_cpa_object` | `scene-0038-medium-01` | `1` | `iter48` | `cbc56796e802e964bca700662f34c77fb2500ee8ee32225820276521d4a230e2` |
| `4` | `i102_s04_iter48_easy_medium_unique_cpa_object_scene_0062_medium_00_r2` | `iter48_easy_medium` | `unique_cpa_object` | `scene-0062-medium-00` | `2` | `iter48` | `8ab4eaa941cf292710701f1a8e0d791ee81fede1874c985d0bf126951018e2ae` |
| `5` | `i102_s05_iter48_easy_medium_unique_ttc_object_scene_0051_easy_00_r1` | `iter48_easy_medium` | `unique_ttc_object` | `scene-0051-easy-00` | `1` | `iter48` | `48ed82b0b0700803e77940fbfd401b34fe2f40d5d5d1f7deaa2e23053c3990f1` |
| `6` | `i102_s06_iter48_easy_medium_unique_ttc_object_scene_0051_easy_00_r2` | `iter48_easy_medium` | `unique_ttc_object` | `scene-0051-easy-00` | `2` | `iter48` | `48ed82b0b0700803e77940fbfd401b34fe2f40d5d5d1f7deaa2e23053c3990f1` |
| `7` | `i102_s07_iter49_hard_extreme_no_fire_scene_0041_extreme_00_r2` | `iter49_hard_extreme` | `no_fire` | `scene-0041-extreme-00` | `2` | `iter49` | `7d186ac9491de1cc3aab58a3a636ab0eb00088179f68d8a563214aaada3aa8af` |
| `8` | `i102_s08_iter49_hard_extreme_no_fire_scene_0062_hard_00_r1` | `iter49_hard_extreme` | `no_fire` | `scene-0062-hard-00` | `1` | `iter49` | `a318c5a49a43fc50e66b6b1b73bd53df165cca3c49e409e7b22f65276361e90e` |
| `9` | `i102_s09_iter49_hard_extreme_unique_cpa_object_scene_0013_extreme_00_r1` | `iter49_hard_extreme` | `unique_cpa_object` | `scene-0013-extreme-00` | `1` | `iter49` | `7b4b374bda9c9520114c9fdcb8ce8f3f91686dc9c0caacc261838ae4fe2a3442` |
| `10` | `i102_s10_iter49_hard_extreme_unique_cpa_object_scene_0013_extreme_00_r2` | `iter49_hard_extreme` | `unique_cpa_object` | `scene-0013-extreme-00` | `2` | `iter49` | `7b4b374bda9c9520114c9fdcb8ce8f3f91686dc9c0caacc261838ae4fe2a3442` |
| `11` | `i102_s11_iter49_hard_extreme_unique_ttc_object_scene_0038_hard_00_r1` | `iter49_hard_extreme` | `unique_ttc_object` | `scene-0038-hard-00` | `1` | `iter49` | `5e1dafedccdde485834d5809dee2fcd3cc0b5c31f7315e454d6b4bd8b04b146d` |
| `12` | `i102_s12_iter49_hard_extreme_unique_ttc_object_scene_0038_hard_00_r2` | `iter49_hard_extreme` | `unique_ttc_object` | `scene-0038-hard-00` | `2` | `iter49` | `5e1dafedccdde485834d5809dee2fcd3cc0b5c31f7315e454d6b4bd8b04b146d` |
| `13` | `i102_s13_iter49_hard_extreme_both_distinct_objects_scene_0138_extreme_00_r1` | `iter49_hard_extreme` | `both_distinct_objects` | `scene-0138-extreme-00` | `1` | `iter49` | `d4e83c49e3240c8091294a5b545920f0c6f3b0e3498cb49c8b132e824c7cf1d9` |

## Duplicate-Slot Policy

Slot id is the primary execution key. Scenario-level deduplication is not allowed for this future batch because the iteration-101 schedule contains repeated scenarios with distinct selected run slots.

## Boundary

offline launch-manifest preflight only; no GPU approval, launch authorization, actor-causality, repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate, HD-Score-invariance, real-world behavior, acquisition-value, or retuning claim
