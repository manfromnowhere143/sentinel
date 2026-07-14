# Iteration 96 - HUGSIM branch taxonomy outcome bridge

Verdict: `HUGSIM_BRANCH_TAXONOMY_LATE_FIRE_OUTCOME_BRIDGE_COMPLETE`

## Summary

- `target_rows`: `2`
- `evaluated_rows`: `2`
- `row_label_counts`: `{'late_fire_with_path_cpa_branch': 1, 'late_fire_with_provenance_ttc_branch': 1}`
- `late_fire_rows`: `2`
- `no_pre_foreground_fire_rows`: `2`
- `provenance_ttc_branch_rows`: `1`
- `path_cpa_branch_rows`: `1`
- `active_cpa_branch_rows`: `1`

## Events

| audit id | first foreground | first fire | delta | channel | branches | label | problems |
|---|---:|---:|---:|---|---|---|---|
| `both_distinct_extreme` | `5.25` | `7.0` | `1.75` | `ttc_only` | `['nonactive_surface_provenance_ttc_borderline_over_path_cpa']` | `late_fire_with_provenance_ttc_branch` | `[]` |
| `ttc_medium_a` | `3.25` | `5.0` | `1.75` | `cpa_only` | `['nonactive_surface_path_cpa_over_provenance_bridge', 'active_row_cpa_margin_overrides_provenance']` | `late_fire_with_path_cpa_branch` | `[]` |

## Boundary

two-row descriptive branch-taxonomy/outcome bridge only; no actor-causality, repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate, HD-Score-invariance, commercial-value, real-world behavior, first-responder behavior, or retuning claim
