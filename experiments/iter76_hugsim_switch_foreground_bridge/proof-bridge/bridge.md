# Iteration 76 - HUGSIM switch foreground bridge audit

Verdict: `HUGSIM_SWITCH_FOREGROUND_BOTH_OR_AMBIGUOUS_COMPLETE`

## Summary

- `target_rows`: `2`
- `evaluated_rows`: `2`
- `row_label_counts`: `{'no_foreground_bridge_support': 2}`
- `active_object_match_rows`: `0`
- `pre_object_match_rows`: `0`
- `no_support_rows`: `2`

## Rows

| audit id | scenario | label | pre id | pre distance | active id | active distance | delta active-pre | problems |
|---|---|---|---:|---:|---:|---:|---:|---|
| `both_distinct_extreme` | `scene-0138-extreme-00` | `no_foreground_bridge_support` | `5` | `13.448307863726438` | `9` | `10.834714044531188` | `-2.61359381919525` | `[]` |
| `ttc_medium_a` | `scene-0071-medium-01` | `no_foreground_bridge_support` | `6` | `8.123927089172518` | `24` | `8.440810417005599` | `0.3168833278330805` | `[]` |

## Boundary

two-row descriptive foreground-bridge audit only; no actor-causality, repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population, HD-Score-invariance, commercial-value, or retuning claim
