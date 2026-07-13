# Iteration 95 - HUGSIM non-active surface branch arbitration

Verdict: `HUGSIM_NONACTIVE_SURFACE_BRANCH_ARBITRATION_SPLIT_COMPLETE`

## Summary

- `target_rows`: `2`
- `evaluated_rows`: `2`
- `row_label_counts`: `{'nonactive_surface_path_cpa_over_provenance_bridge': 1, 'nonactive_surface_provenance_ttc_borderline_over_path_cpa': 1}`
- `surface_matches_path_events`: `1`
- `surface_matches_provenance_events`: `1`
- `provenance_finite_ttc_events`: `1`
- `path_cpa_rank_better_events`: `2`
- `provenance_closer_bridge_events`: `2`

## Events

| audit id | event | surface object | matches path | matches provenance | path CPA rank | provenance TTC | label | problems |
|---|---|---:|---|---|---:|---|---|---|
| `both_distinct_extreme` | `pre` | `9` | `False` | `True` | `1` | `4.776101409133555` | `nonactive_surface_provenance_ttc_borderline_over_path_cpa` | `[]` |
| `ttc_medium_a` | `pre` | `19` | `True` | `False` | `1` | `None` | `nonactive_surface_path_cpa_over_provenance_bridge` | `[]` |

## Boundary

two-row descriptive non-active surface branch arbitration only; no actor-causality, repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate, HD-Score-invariance, commercial-value, real-world behavior, first-responder behavior, or retuning claim
