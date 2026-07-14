# Iteration 113 - HUGSIM support-core actor-match support audit

Verdict: `HUGSIM_SUPPORT_CORE_ACTOR_MATCH_AUDIT_COMPLETE`

## Summary

- `slot_count`: `8`
- `completed_rows`: `8`
- `classifiable_foreground`: `8`
- `support_counts`: `{'classifiable_foreground': 8}`
- `bridge_counts`: `{'actor_mismatch': 8}`
- `design_counts`: `{'exact_ttc_classifiable_anchor': 3, 'ttc_classifiable_scenario_analogue': 5}`
- `design_classifiable_counts`: `{'exact_ttc_classifiable_anchor': 3, 'ttc_classifiable_scenario_analogue': 5}`
- `actor_match`: `0`
- `actor_mismatch`: `8`
- `actor_ambiguous`: `0`
- `min_classifiable_bar`: `4`
- `iter108_classifiable_baseline`: `2`
- `classifiable_delta_vs_iter108`: `6`

## Slots

| slot | scenario | run | design | timing | support | bridge | distance m | monitor object | foreground |
|---:|---|---:|---|---|---|---|---:|---|---|
| `1` | `scene-0411-hard-00` | `2` | `exact_ttc_classifiable_anchor` | `short_lead_fire` | `classifiable_foreground` | `actor_mismatch` | `23.793069683037515` | `12` | `car` |
| `2` | `scene-0411-extreme-00` | `1` | `exact_ttc_classifiable_anchor` | `long_lead_fire` | `classifiable_foreground` | `actor_mismatch` | `24.59033959495813` | `2` | `car` |
| `3` | `scene-0038-hard-00` | `1` | `exact_ttc_classifiable_anchor` | `long_lead_fire` | `classifiable_foreground` | `actor_mismatch` | `14.472507961609738` | `25` | `car` |
| `4` | `scene-0038-extreme-00` | `1` | `ttc_classifiable_scenario_analogue` | `short_lead_fire` | `classifiable_foreground` | `actor_mismatch` | `15.460122021736504` | `2` | `car` |
| `5` | `scene-0038-extreme-00` | `2` | `ttc_classifiable_scenario_analogue` | `short_lead_fire` | `classifiable_foreground` | `actor_mismatch` | `15.541003639773562` | `2` | `car` |
| `6` | `scene-0383-extreme-00` | `2` | `ttc_classifiable_scenario_analogue` | `short_lead_fire` | `classifiable_foreground` | `actor_mismatch` | `36.09143899155716` | `1` | `car` |
| `7` | `scene-0411-hard-00` | `1` | `ttc_classifiable_scenario_analogue` | `short_lead_fire` | `classifiable_foreground` | `actor_mismatch` | `23.180715225043926` | `12` | `car` |
| `8` | `scene-0411-extreme-00` | `2` | `ttc_classifiable_scenario_analogue` | `long_lead_fire` | `classifiable_foreground` | `actor_mismatch` | `24.812496764606966` | `17` | `car` |

## Boundary

bounded 8-slot support-core actor-match support audit only; no repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate, HD-Score-invariance, real-world behavior, first-responder behavior, acquisition-value, retuning, production, or commercial claim
