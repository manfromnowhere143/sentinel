# Iteration 97 - HUGSIM surface-silent outcome margin bridge

Verdict: `HUGSIM_SURFACE_SILENT_OUTCOME_MARGIN_BRIDGE_COMPLETE`

## Summary

- `target_rows`: `2`
- `evaluated_rows`: `2`
- `row_label_counts`: `{'surface_silent_far_never_active_post_foreground_near': 2}`
- `surface_silent_rows`: `2`
- `zero_fire_rows`: `2`
- `far_margin_rows`: `2`
- `never_active_rows`: `2`
- `post_foreground_near_rows`: `2`
- `pre_foreground_near_rows`: `0`

## Events

| audit id | foreground | CPA margin | TTC margin | near offset | active relation | label | problems |
|---|---:|---:|---|---:|---|---|---|
| `mixed_extreme` | `4.75` | `2.6062450662694827` | `None` | `0.25` | `never` | `surface_silent_far_never_active_post_foreground_near` | `[]` |
| `nofire_hard_control` | `2.5` | `6.477878342783893` | `3.4560450365182938` | `3.5` | `never` | `surface_silent_far_never_active_post_foreground_near` | `[]` |

## Boundary

two-row descriptive surface-silent outcome/margin bridge only; no actor-causality, repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate, HD-Score-invariance, commercial-value, real-world behavior, first-responder behavior, or retuning claim
