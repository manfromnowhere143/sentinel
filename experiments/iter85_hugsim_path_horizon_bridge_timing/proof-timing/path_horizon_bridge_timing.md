# Iteration 85 - HUGSIM path-horizon/provenance-timing decomposition

Verdict: `HUGSIM_PATH_HORIZON_BRIDGE_TIMING_SPLIT_COMPLETE`

## Summary

- `target_events`: `3`
- `evaluated_events`: `3`
- `event_label_counts`: `{'path_horizon_support_bridge_timing_split': 3}`
- `selected_bridge_supported_events`: `0`
- `support_bridge_supported_events`: `3`
- `timing_comparison_counts`: `{'selected_better_cpa_rank': 3, 'selected_earlier_cpa_horizon': 1, 'selected_lower_cpa': 3, 'selected_no_support_support_supported': 3, 'support_better_bridge': 3}`
- `support_bridge_timing_counts`: `{'provenance_after_event': 3}`

## Events

| audit id | event | selected id | selected state | selected CPA | selected horizon | selected bridge | support id | support state | support CPA | support horizon | support bridge | support timing | comparisons | label | problems |
|---|---|---:|---|---:|---:|---|---:|---|---:|---:|---|---|---|---|---|
| `both_distinct_extreme` | `pre` | `5` | `borderline` | `2.035458679140406` | `4` / `2.0` | `no_support` | `9` | `subthreshold` | `21.634279246714645` | `6` / `3.0` | `ambiguous` | `provenance_after_event` / `0.5` | `['selected_lower_cpa', 'selected_better_cpa_rank', 'selected_earlier_cpa_horizon', 'support_better_bridge', 'selected_no_support_support_supported']` | `path_horizon_support_bridge_timing_split` | `[]` |
| `ttc_medium_a` | `pre` | `6` | `borderline` | `9.24044996029241` | `6` / `3.0` | `no_support` | `10` | `subthreshold` | `17.276402111954756` | `6` / `3.0` | `match` | `provenance_after_event` / `1.5` | `['selected_lower_cpa', 'selected_better_cpa_rank', 'support_better_bridge', 'selected_no_support_support_supported']` | `path_horizon_support_bridge_timing_split` | `[]` |
| `ttc_medium_a` | `active` | `24` | `active` | `1.2791009183078823` | `6` / `3.0` | `no_support` | `10` | `subthreshold` | `13.557766187421446` | `6` / `3.0` | `match` | `provenance_after_event` / `1.0` | `['selected_lower_cpa', 'selected_better_cpa_rank', 'support_better_bridge', 'selected_no_support_support_supported']` | `path_horizon_support_bridge_timing_split` | `[]` |

## Boundary

three-row descriptive path-horizon/provenance-timing decomposition only; no actor-causality, repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population, HD-Score-invariance, commercial-value, real-world behavior, or retuning claim
