# Iteration 65 - matched pre-contact temporal alignment audit

Verdict: `TEMPORAL_ALIGNMENT_SUBTHRESHOLD_COMPLETE`

## Summary

- `target_rows`: `2`
- `evaluated_rows`: `2`
- `row_label_counts`: `{'matched_object_subthreshold': 2}`
- `matched_object_ids`: `[2, 6]`
- `matched_objects_equal_first_fire_objects`: `1`

## Rows

- `ttc_extreme_short` / `scene-0038-extreme-00`: label `matched_object_subthreshold`, matched object `2`, decision `0.25`, min_cpa `12.724000037517374`, ttc `3.576347739341626`, cpa_cross `False`, ttc_cross `False`, first_fire `ttc_only` object `2`, problems `[]`
- `cpa_medium_b` / `scene-0166-medium-00`: label `matched_object_subthreshold`, matched object `6`, decision `2.25`, min_cpa `9.31789901398808`, ttc `None`, cpa_cross `False`, ttc_cross `False`, first_fire `cpa_only` object `1`, problems `[]`

## Boundary

two-row temporal/provenance alignment audit only; no transfer, safety, deployment, benchmark, actor-causality, repair, population, HD-Score-invariance, or retuning claim
