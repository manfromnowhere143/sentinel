# Iteration 86 - HUGSIM bridge-time support-surface replay

Verdict: `HUGSIM_BRIDGE_TIME_SURFACE_REPLAY_BLOCKED`

## Summary

- `target_rows`: `3`
- `evaluated_rows`: `2`
- `row_label_counts`: `{'bridge_time_surface_replay_insufficient': 1, 'support_bridge_time_surface_arrival': 1, 'support_bridge_time_surface_miss': 1}`
- `state_transition_counts`: `{'subthreshold->None': 1, 'subthreshold->borderline': 1, 'subthreshold->subthreshold': 1}`

## Events

| audit id | event | support id | event ts | bridge ts | event state | bridge state | event CPA | bridge CPA | transition | label | problems |
|---|---|---:|---:|---:|---|---|---:|---:|---|---|---|
| `both_distinct_extreme` | `pre` | `9` | `5.0` | `5.5` | `subthreshold` | `borderline` | `21.634279246714645` | `21.520798149009224` | `subthreshold->borderline` | `support_bridge_time_surface_arrival` | `[]` |
| `ttc_medium_a` | `pre` | `10` | `2.5` | `4.0` | `subthreshold` | `subthreshold` | `17.276402111954756` | `11.135406800051493` | `subthreshold->subthreshold` | `support_bridge_time_surface_miss` | `[]` |
| `ttc_medium_a` | `active` | `10` | `5.0` | `6.0` | `subthreshold` | `None` | `13.557766187421446` | `None` | `subthreshold->None` | `bridge_time_surface_replay_insufficient` | `['bridge-row-count-0-for-ts-6.0']` |

## Boundary

three-row descriptive bridge-time support-surface replay only; no actor-causality, repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population, HD-Score-invariance, commercial-value, real-world behavior, or retuning claim
