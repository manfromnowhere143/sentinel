# Iteration 108 - HUGSIM timing-aware batch actor-match support audit

Verdict: `HUGSIM_TIMING_AWARE_BATCH_ACTOR_MATCH_SUPPORT_NULL`

## Summary

- `slot_count`: `13`
- `completed_rows`: `13`
- `classifiable_foreground`: `2`
- `support_counts`: `{'background_collision_only': 6, 'classifiable_foreground': 2, 'no_collision_provenance': 1, 'post_collision_fire': 4}`
- `bridge_counts`: `{'actor_mismatch': 2}`
- `actor_match`: `0`
- `actor_mismatch`: `2`
- `actor_ambiguous`: `0`
- `min_classifiable_bar`: `4`
- `iter104_classifiable_baseline`: `1`
- `classifiable_delta_vs_iter104`: `1`

## Slots

| slot | scenario | run | timing | channel | support | bridge | distance m | monitor object | foreground |
|---:|---|---:|---|---|---|---|---:|---|---|
| `1` | `scene-0138-medium-01` | `1` | `long_lead_fire` | `ttc_only` | `post_collision_fire` | `None` | `None` | `24` | `car` |
| `2` | `scene-0064-hard-00` | `2` | `long_lead_fire` | `cpa_only` | `background_collision_only` | `None` | `None` | `24` | `None` |
| `3` | `scene-0166-easy-00` | `2` | `long_lead_fire` | `cpa_only` | `no_collision_provenance` | `None` | `None` | `1` | `None` |
| `4` | `scene-0138-medium-01` | `2` | `long_lead_fire` | `ttc_only` | `post_collision_fire` | `None` | `None` | `32` | `car` |
| `5` | `scene-0064-easy-00` | `2` | `long_lead_fire` | `cpa_only` | `background_collision_only` | `None` | `None` | `84` | `None` |
| `6` | `scene-0166-medium-01` | `2` | `long_lead_fire` | `cpa_only` | `background_collision_only` | `None` | `None` | `2` | `None` |
| `7` | `scene-0064-hard-00` | `1` | `long_lead_fire` | `cpa_only` | `background_collision_only` | `None` | `None` | `24` | `None` |
| `8` | `scene-0411-extreme-00` | `1` | `long_lead_fire` | `ttc_only` | `classifiable_foreground` | `actor_mismatch` | `33.51390083849024` | `2` | `car` |
| `9` | `scene-0071-easy-00` | `2` | `long_lead_fire` | `ttc_only` | `background_collision_only` | `None` | `None` | `1` | `None` |
| `10` | `scene-0411-hard-00` | `2` | `short_lead_fire` | `ttc_only` | `classifiable_foreground` | `actor_mismatch` | `31.29909111075036` | `6` | `car` |
| `11` | `scene-0138-hard-00` | `1` | `long_lead_fire` | `cpa_only` | `post_collision_fire` | `None` | `None` | `6` | `car` |
| `12` | `scene-0071-extreme-00` | `1` | `long_lead_fire` | `cpa_only` | `post_collision_fire` | `None` | `None` | `2` | `car` |
| `13` | `scene-0064-medium-01` | `1` | `long_lead_fire` | `cpa_only` | `background_collision_only` | `None` | `None` | `18` | `None` |

## Boundary

bounded 13-slot timing-aware actor-match support audit only; no repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate, HD-Score-invariance, real-world behavior, first-responder behavior, acquisition-value, retuning, production, or commercial claim
