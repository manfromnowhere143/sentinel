# Iteration 105 - HUGSIM timing-aware provenance batch design

Verdict: `HUGSIM_TIMING_AWARE_BATCH_DESIGN_COMPLETE`

## Summary

- `target_slot_count`: `13`
- `primary_eligible_count`: `20`
- `excluded_eligible_count`: `15`
- `selected_slot_count`: `13`
- `selected_unique_scenario_count`: `11`
- `selected_dataset_counts`: `{'iter48_easy_medium': 7, 'iter49_hard_extreme': 6}`
- `selected_channel_counts`: `{'cpa_only': 8, 'ttc_only': 5}`
- `selected_tier_counts`: `{'easy': 3, 'extreme': 2, 'hard': 4, 'medium': 4}`
- `selected_timing_counts`: `{'long_lead_fire': 12, 'short_lead_fire': 1}`
- `primary_timing_counts`: `{'long_lead_fire': 16, 'short_lead_fire': 4}`

## Selected Future Slots

| slot | scenario | run | dataset | tier | channel | timing | lead s | brake frames | reason |
|---:|---|---:|---|---|---|---|---:|---:|---|
| `1` | `scene-0138-medium-01` | `1` | `iter48_easy_medium` | `medium` | `ttc_only` | `long_lead_fire` | `27.0` | `71` | `coverage_dataset_iter48_easy_medium` |
| `2` | `scene-0064-hard-00` | `2` | `iter49_hard_extreme` | `hard` | `cpa_only` | `long_lead_fire` | `5.5` | `29` | `coverage_dataset_iter49_hard_extreme` |
| `3` | `scene-0166-easy-00` | `2` | `iter48_easy_medium` | `easy` | `cpa_only` | `long_lead_fire` | `14.5` | `12` | `coverage_channel_cpa_only` |
| `4` | `scene-0138-medium-01` | `2` | `iter48_easy_medium` | `medium` | `ttc_only` | `long_lead_fire` | `18.0` | `51` | `coverage_channel_ttc_only` |
| `5` | `scene-0064-easy-00` | `2` | `iter48_easy_medium` | `easy` | `cpa_only` | `long_lead_fire` | `9.75` | `12` | `coverage_tier_easy` |
| `6` | `scene-0166-medium-01` | `2` | `iter48_easy_medium` | `medium` | `cpa_only` | `long_lead_fire` | `13.0` | `37` | `coverage_tier_medium` |
| `7` | `scene-0064-hard-00` | `1` | `iter49_hard_extreme` | `hard` | `cpa_only` | `long_lead_fire` | `5.25` | `27` | `coverage_tier_hard` |
| `8` | `scene-0411-extreme-00` | `1` | `iter49_hard_extreme` | `extreme` | `ttc_only` | `long_lead_fire` | `4.5` | `10` | `coverage_tier_extreme` |
| `9` | `scene-0071-easy-00` | `2` | `iter48_easy_medium` | `easy` | `ttc_only` | `long_lead_fire` | `5.5` | `18` | `coverage_timing_long_lead_fire` |
| `10` | `scene-0411-hard-00` | `2` | `iter49_hard_extreme` | `hard` | `ttc_only` | `short_lead_fire` | `0.25` | `7` | `coverage_timing_short_lead_fire` |
| `11` | `scene-0138-hard-00` | `1` | `iter49_hard_extreme` | `hard` | `cpa_only` | `long_lead_fire` | `4.25` | `19` | `priority_fill` |
| `12` | `scene-0071-extreme-00` | `1` | `iter49_hard_extreme` | `extreme` | `cpa_only` | `long_lead_fire` | `4.0` | `26` | `priority_fill` |
| `13` | `scene-0064-medium-01` | `1` | `iter48_easy_medium` | `medium` | `cpa_only` | `long_lead_fire` | `3.0` | `28` | `priority_fill` |

## Boundary

offline timing-aware candidate-schedule design only; no GPU approval, launch authorization, actor-causality, actor-match result, repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate, HD-Score-invariance, real-world behavior, first-responder behavior, acquisition-value, retuning, production, or commercial claim
