# Iteration 87 - HUGSIM interval bridge-time support-surface replay

Verdict: `HUGSIM_INTERVAL_BRIDGE_TIME_SURFACE_REPLAY_MIXED_COMPLETE`

## Summary

- `target_rows`: `3`
- `evaluated_rows`: `3`
- `row_label_counts`: `{'interval_support_surface_arrival': 1, 'interval_support_surface_miss': 2}`
- `state_transition_counts`: `{'subthreshold->borderline': 1, 'subthreshold->subthreshold': 2}`
- `replay_alignment_counts`: `{'exact_bridge_ts': 2, 'nearest_before_bridge_ts': 1}`

## Events

| audit id | event | support id | event ts | bridge ts | replay ts | alignment | event state | replay state | event CPA | replay CPA | transition | label | problems |
|---|---|---:|---:|---:|---:|---|---|---|---:|---:|---|---|---|
| `both_distinct_extreme` | `pre` | `9` | `5.0` | `5.5` | `5.5` | `exact_bridge_ts` | `subthreshold` | `borderline` | `21.634279246714645` | `21.520798149009224` | `subthreshold->borderline` | `interval_support_surface_arrival` | `[]` |
| `ttc_medium_a` | `pre` | `10` | `2.5` | `4.0` | `4.0` | `exact_bridge_ts` | `subthreshold` | `subthreshold` | `17.276402111954756` | `11.135406800051493` | `subthreshold->subthreshold` | `interval_support_surface_miss` | `[]` |
| `ttc_medium_a` | `active` | `10` | `5.0` | `6.0` | `5.75` | `nearest_before_bridge_ts` | `subthreshold` | `subthreshold` | `13.557766187421446` | `12.143435514611875` | `subthreshold->subthreshold` | `interval_support_surface_miss` | `[]` |

## Boundary

three-row descriptive interval bridge-time support-surface replay only; no actor-causality, repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population, HD-Score-invariance, commercial-value, real-world behavior, or retuning claim
