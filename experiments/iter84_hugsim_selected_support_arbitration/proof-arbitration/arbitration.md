# Iteration 84 - HUGSIM selected/support path-arbitration decomposition

Verdict: `HUGSIM_SELECTED_SURFACE_SUPPORT_BRIDGE_SPLIT_COMPLETE`

## Summary

- `target_events`: `3`
- `evaluated_events`: `3`
- `event_label_counts`: `{'selected_surface_support_bridge_split': 3}`
- `support_better_bridge_events`: `3`
- `selected_bridge_supported_events`: `0`
- `support_bridge_supported_events`: `3`
- `hazard_advantage_counts`: `{'selected_better_cpa_rank': 3, 'selected_finite_ttc_support_missing': 1, 'selected_lower_cpa': 3}`

## Events

| audit id | event | selected id | selected state | selected cpa | selected ttc | selected bridge | support id | support state | support cpa | support ttc | support bridge | advantages | label | problems |
|---|---|---:|---|---:|---:|---|---:|---|---:|---:|---|---|---|---|
| `both_distinct_extreme` | `pre` | `5` | `borderline` | `2.035458679140406` | `None` | `no_support` | `9` | `subthreshold` | `21.634279246714645` | `None` | `ambiguous` | `['selected_lower_cpa', 'selected_better_cpa_rank']` | `selected_surface_support_bridge_split` | `[]` |
| `ttc_medium_a` | `pre` | `6` | `borderline` | `9.24044996029241` | `3.274211481109643` | `no_support` | `10` | `subthreshold` | `17.276402111954756` | `None` | `match` | `['selected_lower_cpa', 'selected_better_cpa_rank', 'selected_finite_ttc_support_missing']` | `selected_surface_support_bridge_split` | `[]` |
| `ttc_medium_a` | `active` | `24` | `active` | `1.2791009183078823` | `None` | `no_support` | `10` | `subthreshold` | `13.557766187421446` | `None` | `match` | `['selected_lower_cpa', 'selected_better_cpa_rank']` | `selected_surface_support_bridge_split` | `[]` |

## Boundary

three-row descriptive selected/support arbitration decomposition only; no actor-causality, repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population, HD-Score-invariance, commercial-value, real-world behavior, or retuning claim
