# Iteration 94 - HUGSIM active-row surface margin arbitration

Verdict: `HUGSIM_ACTIVE_ROW_SURFACE_MARGIN_ARBITRATION_COMPLETE`

## Summary

- `target_rows`: `1`
- `evaluated_rows`: `1`
- `row_label_counts`: `{'active_row_cpa_margin_overrides_provenance': 1}`
- `active_candidate_count`: `1`
- `bridge_supported_count`: `3`
- `bridge_active_or_borderline_count`: `0`
- `bridge_finite_ttc_count`: `0`
- `bridge_nonpositive_active_cpa_margin_count`: `0`
- `active_object_id`: `24`
- `active_cpa_margin_m`: `-0.49901426957705985`
- `min_bridge_active_cpa_margin_m`: `10.643435514611875`
- `min_bridge_active_cpa_margin_object_id`: `10`
- `active_lower_cpa_than_all_bridge`: `True`
- `active_better_cpa_rank_than_all_bridge`: `True`

## Event

| audit id | event | active object | active margin | bridge count | min bridge margin | bridge finite TTC | label | problems |
|---|---|---:|---:|---:|---:|---:|---|---|
| `ttc_medium_a` | `active` | `24` | `-0.49901426957705985` | `3` | `10.643435514611875` | `0` | `active_row_cpa_margin_overrides_provenance` | `[]` |

## Boundary

one-row descriptive active-row margin arbitration only; no actor-causality, repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate, HD-Score-invariance, commercial-value, real-world behavior, first-responder behavior, or retuning claim
