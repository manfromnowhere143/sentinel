# Iteration 77 - HUGSIM event object-set foreground bridge audit

Verdict: `HUGSIM_EVENT_SET_FOREGROUND_SUPPORT_MIXED_COMPLETE`

## Summary

- `target_rows`: `2`
- `evaluated_rows`: `2`
- `row_label_counts`: `{'both_sets_foreground_match': 1, 'pre_set_foreground_ambiguous': 1}`
- `active_set_match_rows`: `0`
- `pre_set_match_rows`: `0`
- `no_support_rows`: `0`

## Rows

| audit id | scenario | label | pre best object | pre distance | active best object | active distance | delta active-pre | problems |
|---|---|---|---:|---:|---:|---:|---:|---|
| `both_distinct_extreme` | `scene-0138-extreme-00` | `pre_set_foreground_ambiguous` | `9` | `3.689944827919669` | `9` | `10.834714044531188` | `7.144769216611518` | `[]` |
| `ttc_medium_a` | `scene-0071-medium-01` | `both_sets_foreground_match` | `10` | `1.124455029493122` | `10` | `1.2931299560453504` | `0.1686749265522285` | `[]` |

## Boundary

two-row descriptive event-object-set foreground-bridge audit only; no actor-causality, repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population, HD-Score-invariance, commercial-value, or retuning claim
