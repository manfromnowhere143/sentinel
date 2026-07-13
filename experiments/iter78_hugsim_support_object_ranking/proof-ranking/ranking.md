# Iteration 78 - HUGSIM support-object ranking audit

Verdict: `HUGSIM_SUPPORT_OBJECT_RANKING_MIXED_COMPLETE`

## Summary

- `target_events`: `3`
- `evaluated_events`: `3`
- `event_label_counts`: `{'support_object_nonselected_subthreshold': 3}`
- `nonselected_active_events`: `0`
- `nonselected_borderline_events`: `0`
- `selected_events`: `0`

## Events

| audit id | event | support id | selected id | label | cpa rank | ttc rank | min cpa | ttc | problems |
|---|---|---:|---:|---|---:|---:|---:|---:|---|
| `both_distinct_extreme` | `pre` | `9` | `5` | `support_object_nonselected_subthreshold` | `4` | `None` | `21.634279246714645` | `None` | `[]` |
| `ttc_medium_a` | `pre` | `10` | `6` | `support_object_nonselected_subthreshold` | `7` | `None` | `17.276402111954756` | `None` | `[]` |
| `ttc_medium_a` | `active` | `10` | `24` | `support_object_nonselected_subthreshold` | `2` | `None` | `13.557766187421446` | `None` | `[]` |

## Boundary

three-event descriptive support-object ranking audit only; no actor-causality, repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population, HD-Score-invariance, commercial-value, or retuning claim
