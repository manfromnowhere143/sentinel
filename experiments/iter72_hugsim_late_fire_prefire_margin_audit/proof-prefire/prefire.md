# Iteration 72 - HUGSIM late-fire prefire margin audit

Verdict: `HUGSIM_LATE_FIRE_PREFIRE_MARGIN_COMPLETE`

## Summary

- `target_rows`: `2`
- `evaluated_rows`: `2`
- `row_label_counts`: `{'late_fire_prefire_near_cpa_margin': 1, 'late_fire_prefire_near_ttc_margin': 1}`
- `near_margin_rows`: `2`
- `far_margin_rows`: `0`
- `no_object_rows`: `0`

## Rows

| audit id | scenario | label | delay | min valid TTC | TTC margin | min CPA | CPA margin | problems |
|---|---|---|---:|---:|---:|---:|---:|---|
| `both_distinct_extreme` | `scene-0138-extreme-00` | `late_fire_prefire_near_cpa_margin` | `1.75` | `None` | `None` | `2.035458679140406` | `0.5354586791404059` | `[]` |
| `ttc_medium_a` | `scene-0071-medium-01` | `late_fire_prefire_near_ttc_margin` | `1.75` | `3.2742114811096417` | `0.7742114811096417` | `4.5137256446355645` | `3.0137256446355645` | `[]` |

## Boundary

two-row descriptive late-fire prefire margin audit only; no actor-causality, repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population, HD-Score-invariance, commercial-value, or retuning claim
