# Iteration 79 - HUGSIM selected-object surface decomposition

Verdict: `HUGSIM_SELECTED_ACTIVE_SUPPORT_SUBTHRESHOLD_COMPLETE`

## Summary

- `target_events`: `3`
- `evaluated_events`: `3`
- `event_label_counts`: `{'selected_active_support_subthreshold': 1, 'selected_borderline_support_subthreshold': 2}`
- `selected_active_events`: `1`
- `selected_borderline_events`: `2`
- `selected_subthreshold_events`: `0`

## Events

| audit id | event | selected id | selected state | selected cpa rank | selected min cpa | selected ttc | support id | support state | support cpa rank | support min cpa | support ttc | label | problems |
|---|---|---:|---|---:|---:|---:|---:|---|---:|---:|---:|---|---|
| `both_distinct_extreme` | `pre` | `5` | `borderline` | `1` | `2.035458679140406` | `None` | `9` | `subthreshold` | `4` | `21.634279246714645` | `None` | `selected_borderline_support_subthreshold` | `[]` |
| `ttc_medium_a` | `pre` | `6` | `borderline` | `3` | `9.24044996029241` | `3.274211481109643` | `10` | `subthreshold` | `7` | `17.276402111954756` | `None` | `selected_borderline_support_subthreshold` | `[]` |
| `ttc_medium_a` | `active` | `24` | `active` | `1` | `1.2791009183078823` | `None` | `10` | `subthreshold` | `2` | `13.557766187421446` | `None` | `selected_active_support_subthreshold` | `[]` |

## Boundary

three-event descriptive selected-vs-support surface audit only; no actor-causality, repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population, HD-Score-invariance, commercial-value, or retuning claim
