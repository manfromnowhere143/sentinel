# Iteration 60 - actor-match bridge sensitivity

Verdict: `BRIDGE_AMBIGUOUS_NULL`

## Summary

- `iter59_classifiable_rows`: `3`
- `variant_rows_evaluated`: `3`
- `variants_per_row`: `16`
- `sensitivity_counts`: `{'bridge_ambiguous_possible': 1, 'robust_mismatch': 2}`
- `minimum_distance_m`: `5.664876449943843`

## Classifiable Rows

- `ttc_extreme_short` / `scene-0038-extreme-00`: best `robust_mismatch`, distance `8.652459284308707`, variant `first_fire/yx/-1/-1`, problems `[]`
- `cpa_medium_b` / `scene-0166-medium-00`: best `robust_mismatch`, distance `19.69826047075051`, variant `first_fire/yx/1/-1`, problems `[]`
- `ttc_extreme_b` / `scene-0383-extreme-00`: best `bridge_ambiguous_possible`, distance `5.664876449943843`, variant `first_fire/yx/-1/1`, problems `[]`

## Boundary

offline sensitivity audit over the three iteration-59 classifiable rows only; no transfer, safety, deployment, benchmark, retuning, repair, or population claim
