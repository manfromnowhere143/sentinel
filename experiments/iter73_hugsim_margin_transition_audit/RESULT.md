# Iteration 73 - HUGSIM structural margin transition audit: HUGSIM_MARGIN_TRANSITION_SPLIT_COMPLETE

Status: `HUGSIM_MARGIN_TRANSITION_SPLIT_COMPLETE` (offline margin-transition audit over the four
foreground-present structural HUGSIM rows).

This iteration launched no GPU work, read no live box state, created no HUGSIM episodes, changed
no thresholds, and did not retune Sentinel. It used only committed iteration-59 proof/report
artifacts and the committed iteration-70, iteration-71, and iteration-72 reports.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer: [`analyze_margin_transition.py`](analyze_margin_transition.py)
- Tests: [`../../tests/test_iter73_margin_transition.py`](../../tests/test_iter73_margin_transition.py)
- Analyzer command: [`proof-transition/analyze_margin_transition.command.txt`](proof-transition/analyze_margin_transition.command.txt)
- JSON report: [`proof-transition/transition_report.json`](proof-transition/transition_report.json)
- Markdown report: [`proof-transition/transition.md`](proof-transition/transition.md)

## Result

The analyzer cross-checked:

- iteration-59 verdict: `ACTOR_MATCH_AUDIT_COMPLETE`;
- iteration-70 verdict: `HUGSIM_STRUCTURAL_TIMING_TAXONOMY_COMPLETE`;
- iteration-71 verdict: `HUGSIM_SURFACE_SILENT_MARGIN_COMPLETE`;
- iteration-72 verdict: `HUGSIM_LATE_FIRE_PREFIRE_MARGIN_COMPLETE`;
- exactly the four fixed foreground-present structural rows.

Summary:

- target rows: `4`;
- evaluated rows: `4`;
- row labels:
  - `silent_far_never_active`: `2`;
  - `late_prefire_near_postcontact_active`: `2`;
- verdict: `HUGSIM_MARGIN_TRANSITION_SPLIT_COMPLETE`.

| audit id | structural branch | label | first near offset | first active offset | first active channel |
|---|---|---|---:|---:|---|
| `mixed_extreme` | surface-silent | `silent_far_never_active` | `+0.25 s` | none | none |
| `nofire_hard_control` | surface-silent | `silent_far_never_active` | `+3.50 s` | none | none |
| `both_distinct_extreme` | late-fire | `late_prefire_near_postcontact_active` | `-0.25 s` | `+1.75 s` | TTC |
| `ttc_medium_a` | late-fire | `late_prefire_near_postcontact_active` | `-0.75 s` | `+1.75 s` | CPA |

## Interpretation

Iteration 73 resolves the structural branch contrast into a timeline split.

The two surface-silent rows remain non-active across the full committed decision log: no active
CPA/TTC crossing appears anywhere. They can become near after foreground contact, but never cross
the active frozen surface.

The two late-fire rows show the opposite pattern: both are near a frozen trigger surface before
foreground contact, then first cross an active surface only after contact. In both rows, the first
active crossing occurs `1.75 s` after the first foreground timestamp, matching the delayed first
fire from iteration 70. The near-margin side before contact and the active channel after contact
need not be the same channel.

This supports a structural timing mechanism: far/never-active rows versus near-precontact /
postcontact-active rows. It does not authorize threshold changes or repairs.

## Claim boundary

No actor-causality, repair, threshold-value, transfer improvement, safety, deployment readiness,
robustness, benchmark ranking, HD-Score-invariance, population-rate, retuning value, or commercial
value claim. This result only classifies the four fixed foreground-present structural rows by
their descriptive margin-transition timelines.
