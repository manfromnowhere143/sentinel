# Iteration 88 - HUGSIM bridge/surface margin residual decomposition

Verdict: `HUGSIM_BRIDGE_SURFACE_MARGIN_RESIDUAL_SPLIT_COMPLETE`

## Summary

- `target_rows`: `3`
- `evaluated_rows`: `3`
- `row_label_counts`: `{'bridge_surface_no_finite_ttc_cpa_far': 2, 'bridge_surface_ttc_borderline_cpa_far': 1}`
- `support_bridge_band_counts`: `{'ambiguous': 1, 'match': 2}`
- `replay_state_counts`: `{'borderline': 1, 'subthreshold': 2}`

## Events

| audit id | event | support id | bridge band | bridge distance | replay state | CPA margin | TTC | TTC margin | label | problems |
|---|---|---:|---|---:|---|---:|---:|---:|---|---|
| `both_distinct_extreme` | `pre` | `9` | `ambiguous` | `3.689944827919669` | `borderline` | `20.020798149009224` | `4.776101409133555` | `2.276101409133555` | `bridge_surface_ttc_borderline_cpa_far` | `[]` |
| `ttc_medium_a` | `pre` | `10` | `match` | `1.124455029493122` | `subthreshold` | `9.635406800051493` | `None` | `None` | `bridge_surface_no_finite_ttc_cpa_far` | `[]` |
| `ttc_medium_a` | `active` | `10` | `match` | `1.2931299560453504` | `subthreshold` | `10.643435514611875` | `None` | `None` | `bridge_surface_no_finite_ttc_cpa_far` | `[]` |

## Boundary

three-row descriptive bridge/surface margin residual decomposition only; no actor-causality, repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population, HD-Score-invariance, commercial-value, real-world behavior, or retuning claim
