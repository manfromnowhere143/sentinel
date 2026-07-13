# Iteration 71 - HUGSIM surface-silent margin audit

Verdict: `HUGSIM_SURFACE_SILENT_MARGIN_COMPLETE`

## Summary

- `target_rows`: `2`
- `evaluated_rows`: `2`
- `row_label_counts`: `{'surface_silent_far_margin': 2}`
- `near_margin_rows`: `0`
- `far_margin_rows`: `2`
- `no_object_rows`: `0`

## Rows

| audit id | scenario | label | min valid TTC | TTC margin | min CPA | CPA margin | problems |
|---|---|---|---:|---:|---:|---:|---|
| `mixed_extreme` | `scene-0062-extreme-00` | `surface_silent_far_margin` | `None` | `None` | `4.106245066269483` | `2.6062450662694827` | `[]` |
| `nofire_hard_control` | `scene-0041-hard-00` | `surface_silent_far_margin` | `5.956045036518294` | `3.4560450365182938` | `7.977878342783893` | `6.477878342783893` | `[]` |

## Boundary

two-row descriptive surface-silent margin audit only; no actor-causality, repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population, HD-Score-invariance, commercial-value, or retuning claim
