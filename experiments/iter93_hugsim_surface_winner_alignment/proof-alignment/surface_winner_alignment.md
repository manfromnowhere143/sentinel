# Iteration 93 - HUGSIM surface-winner alignment audit

Verdict: `HUGSIM_SURFACE_WINNER_ALIGNMENT_MIXED_COMPLETE`

## Summary

- `target_rows`: `3`
- `evaluated_rows`: `3`
- `row_label_counts`: `{'surface_follows_path_active_no_bridge': 1, 'surface_follows_path_nonactive': 1, 'surface_follows_provenance_nonactive': 1}`
- `surface_matches_path_events`: `2`
- `surface_matches_provenance_events`: `1`
- `path_matches_provenance_events`: `0`

## Events

| audit id | event | surface best | surface state | surface bridge | matches path | matches provenance | label | problems |
|---|---|---:|---|---|---|---|---|---|
| `both_distinct_extreme` | `pre` | `9` | `borderline` | `match` | `False` | `True` | `surface_follows_provenance_nonactive` | `[]` |
| `ttc_medium_a` | `pre` | `19` | `subthreshold` | `ambiguous` | `True` | `False` | `surface_follows_path_nonactive` | `[]` |
| `ttc_medium_a` | `active` | `24` | `active` | `no_support` | `True` | `False` | `surface_follows_path_active_no_bridge` | `[]` |

## Boundary

three-row descriptive selector-alignment audit only; no actor-causality, repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population, HD-Score-invariance, commercial-value, real-world behavior, or retuning claim
