# Iteration 110 - HUGSIM support-preserving candidate design

Verdict: `HUGSIM_SUPPORT_PRESERVING_CANDIDATE_DESIGN_CORE_COMPLETE`

## Summary

- `target_slot_count`: `13`
- `min_core_floor`: `4`
- `timing_eligible_count`: `35`
- `design_label_counts`: `{'cpa_residual_risk_fallback': 19, 'exact_ttc_classifiable_anchor': 3, 'ttc_classifiable_scenario_analogue': 5, 'ttc_residual_risk_probe': 8}`
- `support_preserving_core_count`: `8`
- `exact_ttc_classifiable_anchor_count`: `3`
- `ttc_classifiable_scenario_analogue_count`: `5`
- `core_channel_counts`: `{'ttc_only': 8}`
- `core_timing_counts`: `{'long_lead_fire': 3, 'short_lead_fire': 5}`
- `fallback_pressure_count`: `27`
- `fallback_label_counts`: `{'cpa_residual_risk_fallback': 19, 'ttc_residual_risk_probe': 8}`
- `fresh_primary_count`: `3`
- `fresh_primary_channel_counts`: `{'cpa_only': 3}`
- `prior_support_scenario_count`: `27`
- `full_13_support_preserving_available`: `False`
- `infra_problem_count`: `0`

## Support-Preserving Core

| role | scenario | run | dataset | tier | timing | lead s | positive evidence | nonclass evidence |
|---|---|---:|---|---|---|---:|---|---|
| `exact_ttc_classifiable_anchor` | `scene-0411-hard-00` | `2` | `iter49_hard_extreme` | `hard` | `short_lead_fire` | `0.25` | `['iter109:classifiable_success:actor_mismatch']` | `[]` |
| `exact_ttc_classifiable_anchor` | `scene-0411-extreme-00` | `1` | `iter49_hard_extreme` | `extreme` | `long_lead_fire` | `4.5` | `['iter109:classifiable_success:actor_mismatch']` | `[]` |
| `exact_ttc_classifiable_anchor` | `scene-0038-hard-00` | `1` | `iter49_hard_extreme` | `hard` | `long_lead_fire` | `1.5` | `['iter104:classifiable_foreground:actor_mismatch']` | `[]` |
| `ttc_classifiable_scenario_analogue` | `scene-0038-extreme-00` | `1` | `iter49_hard_extreme` | `extreme` | `short_lead_fire` | `1.0` | `['iter59:classifiable_foreground:actor_mismatch']` | `[]` |
| `ttc_classifiable_scenario_analogue` | `scene-0038-extreme-00` | `2` | `iter49_hard_extreme` | `extreme` | `short_lead_fire` | `0.75` | `['iter59:classifiable_foreground:actor_mismatch']` | `[]` |
| `ttc_classifiable_scenario_analogue` | `scene-0383-extreme-00` | `2` | `iter49_hard_extreme` | `extreme` | `short_lead_fire` | `0.75` | `['iter59:classifiable_foreground:actor_mismatch']` | `[]` |
| `ttc_classifiable_scenario_analogue` | `scene-0411-hard-00` | `1` | `iter49_hard_extreme` | `hard` | `short_lead_fire` | `0.25` | `['iter109:classifiable_success:actor_mismatch']` | `[]` |
| `ttc_classifiable_scenario_analogue` | `scene-0411-extreme-00` | `2` | `iter49_hard_extreme` | `extreme` | `long_lead_fire` | `3.0` | `['iter109:classifiable_success:actor_mismatch']` | `[]` |

## Fallback Pressure

| role | scenario | run | channel | timing | lead s | scenario nonclass evidence |
|---|---|---:|---|---|---:|---|
| `ttc_residual_risk_probe` | `scene-0062-extreme-00` | `1` | `ttc_only` | `short_lead_fire` | `0.25` | `['iter59:no_monitor_fire']` |
| `ttc_residual_risk_probe` | `scene-0071-extreme-00` | `2` | `ttc_only` | `short_lead_fire` | `0.0` | `['iter109:observed_post_collision_fire']` |
| `ttc_residual_risk_probe` | `scene-0138-medium-01` | `1` | `ttc_only` | `long_lead_fire` | `27.0` | `['iter109:observed_post_collision_fire', 'iter109:observed_post_collision_fire']` |
| `ttc_residual_risk_probe` | `scene-0138-medium-01` | `2` | `ttc_only` | `long_lead_fire` | `18.0` | `['iter109:observed_post_collision_fire', 'iter109:observed_post_collision_fire']` |
| `ttc_residual_risk_probe` | `scene-0062-hard-00` | `2` | `ttc_only` | `long_lead_fire` | `16.75` | `['iter104:background_collision_only']` |
| `ttc_residual_risk_probe` | `scene-0071-easy-00` | `2` | `ttc_only` | `long_lead_fire` | `5.5` | `['iter109:observed_background_only']` |
| `ttc_residual_risk_probe` | `scene-0071-easy-00` | `1` | `ttc_only` | `long_lead_fire` | `2.25` | `['iter109:observed_background_only']` |
| `ttc_residual_risk_probe` | `scene-0071-medium-01` | `1` | `ttc_only` | `long_lead_fire` | `1.75` | `['iter59:post_collision_fire']` |
| `cpa_residual_risk_fallback` | `scene-0064-medium-00` | `2` | `cpa_only` | `short_lead_fire` | `0.0` | `[]` |
| `cpa_residual_risk_fallback` | `scene-0138-extreme-00` | `2` | `cpa_only` | `short_lead_fire` | `0.0` | `['iter104:post_collision_fire', 'iter59:post_collision_fire']` |
| `cpa_residual_risk_fallback` | `scene-0166-easy-00` | `2` | `cpa_only` | `long_lead_fire` | `14.5` | `['iter109:observed_empty_collision_provenance']` |
| `cpa_residual_risk_fallback` | `scene-0166-medium-01` | `2` | `cpa_only` | `long_lead_fire` | `13.0` | `['iter109:observed_background_only']` |
| `cpa_residual_risk_fallback` | `scene-0064-easy-00` | `2` | `cpa_only` | `long_lead_fire` | `9.75` | `['iter109:observed_background_only']` |
| `cpa_residual_risk_fallback` | `scene-0038-medium-01` | `1` | `cpa_only` | `long_lead_fire` | `6.25` | `['iter104:background_collision_only']` |
| `cpa_residual_risk_fallback` | `scene-0166-medium-00` | `2` | `cpa_only` | `long_lead_fire` | `6.0` | `[]` |
| `cpa_residual_risk_fallback` | `scene-0062-medium-00` | `2` | `cpa_only` | `long_lead_fire` | `5.75` | `['iter104:background_collision_only']` |
| `cpa_residual_risk_fallback` | `scene-0166-medium-00` | `1` | `cpa_only` | `long_lead_fire` | `5.75` | `[]` |
| `cpa_residual_risk_fallback` | `scene-0064-hard-00` | `2` | `cpa_only` | `long_lead_fire` | `5.5` | `['iter109:observed_background_only', 'iter109:observed_background_only']` |
| `cpa_residual_risk_fallback` | `scene-0064-hard-00` | `1` | `cpa_only` | `long_lead_fire` | `5.25` | `['iter109:observed_background_only', 'iter109:observed_background_only']` |
| `cpa_residual_risk_fallback` | `scene-0071-medium-00` | `2` | `cpa_only` | `long_lead_fire` | `4.75` | `['iter59:background_collision_only']` |
| `cpa_residual_risk_fallback` | `scene-0138-hard-00` | `1` | `cpa_only` | `long_lead_fire` | `4.25` | `['iter109:observed_post_collision_fire']` |
| `cpa_residual_risk_fallback` | `scene-0071-extreme-00` | `1` | `cpa_only` | `long_lead_fire` | `4.0` | `['iter109:observed_post_collision_fire']` |
| `cpa_residual_risk_fallback` | `scene-0071-medium-00` | `1` | `cpa_only` | `long_lead_fire` | `4.0` | `['iter59:background_collision_only']` |
| `cpa_residual_risk_fallback` | `scene-0064-medium-01` | `1` | `cpa_only` | `long_lead_fire` | `3.0` | `['iter109:observed_background_only']` |
| `cpa_residual_risk_fallback` | `scene-0062-extreme-00` | `2` | `cpa_only` | `long_lead_fire` | `2.0` | `['iter59:no_monitor_fire']` |
| `cpa_residual_risk_fallback` | `scene-0167-hard-00` | `2` | `cpa_only` | `long_lead_fire` | `2.0` | `[]` |
| `cpa_residual_risk_fallback` | `scene-0166-hard-00` | `2` | `cpa_only` | `long_lead_fire` | `1.25` | `[]` |

## Fresh Primary Rows

| role | scenario | run | channel | timing | lead s |
|---|---|---:|---|---|---:|
| `cpa_residual_risk_fallback` | `scene-0064-medium-00` | `2` | `cpa_only` | `short_lead_fire` | `0.0` |
| `cpa_residual_risk_fallback` | `scene-0167-hard-00` | `2` | `cpa_only` | `long_lead_fire` | `2.0` |
| `cpa_residual_risk_fallback` | `scene-0166-hard-00` | `2` | `cpa_only` | `long_lead_fire` | `1.25` |

## Boundary

offline support-preserving candidate design only; no actor-causality, actor-match support upgrade, repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate, HD-Score-invariance, real-world behavior, first-responder behavior, acquisition-value, retuning, production, commercial, schedule-selection, launch-manifest, or GPU-approval claim
