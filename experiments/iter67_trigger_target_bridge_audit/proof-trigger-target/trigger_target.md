# Iteration 67 - trigger-target bridge audit

Verdict: `TRIGGER_TARGET_SAME_AND_SPLIT_COMPLETE`

## Summary

- `target_rows`: `2`
- `evaluated_rows`: `2`
- `row_label_counts`: `{'same_object_target_trigger_match': 1, 'split_target_match_trigger_match': 1}`
- `same_object_rows`: `1`
- `split_object_rows`: `1`
- `target_match_rows`: `2`
- `trigger_match_rows`: `2`

## Rows

- `ttc_extreme_short` / `scene-0038-extreme-00`: label `same_object_target_trigger_match`, target `2` best `1.6718236908808954` (match), trigger `2` best `1.6718236908808954` (match), first-fire trigger best `6.927225576937264` (no_support), problems `[]`
- `cpa_medium_b` / `scene-0166-medium-00`: label `split_target_match_trigger_match`, target `6` best `0.4325280723170322` (match), trigger `1` best `2.833167998901139` (match), first-fire trigger best `19.69826047075051` (no_support), problems `[]`

## Boundary

two-row trigger/target bridge audit only; no transfer, safety, deployment, benchmark, actor-causality, repair, population, HD-Score-invariance, or retuning claim
