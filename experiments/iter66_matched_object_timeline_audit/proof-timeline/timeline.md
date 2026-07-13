# Iteration 66 - matched-object hazard timeline audit

Verdict: `MATCHED_OBJECT_TIMELINE_MIXED_COMPLETE`

## Summary

- `target_rows`: `2`
- `evaluated_rows`: `2`
- `row_label_counts`: `{'target_object_ever_active_hazard': 1, 'target_object_visible_never_active': 1}`
- `total_pre_contact_frames`: `35`
- `total_present_frames`: `20`
- `total_hazard_frames`: `1`
- `total_borderline_frames`: `2`

## Rows

- `ttc_extreme_short` / `scene-0038-extreme-00` / object `2`: label `target_object_ever_active_hazard`, present `7`/`10`, hazard `1`, borderline `2`, min_cpa `12.216375478884643`, min_ttc `2.189319783987488`, first_fire `ttc_only` at `1.5`, problems `[]`
- `cpa_medium_b` / `scene-0166-medium-00` / object `6`: label `target_object_visible_never_active`, present `13`/`25`, hazard `0`, borderline `0`, min_cpa `7.9669377527970955`, min_ttc `None`, first_fire `cpa_only` at `0.25`, problems `[]`

## Boundary

two-row target-object temporal surface audit only; no transfer, safety, deployment, benchmark, actor-causality, repair, population, HD-Score-invariance, or retuning claim
