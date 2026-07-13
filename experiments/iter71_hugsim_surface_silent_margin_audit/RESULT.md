# Iteration 71 - HUGSIM surface-silent margin audit: HUGSIM_SURFACE_SILENT_MARGIN_COMPLETE

Status: `HUGSIM_SURFACE_SILENT_MARGIN_COMPLETE` (offline margin audit over the two
iteration-70 foreground-present surface-silent rows).

This iteration launched no GPU work, read no live box state, created no HUGSIM episodes, changed
no thresholds, and did not retune Sentinel. It used only committed iteration-59 proof/report
artifacts and the committed iteration-70 structural timing report.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer: [`analyze_surface_silent_margin.py`](analyze_surface_silent_margin.py)
- Tests: [`../../tests/test_iter71_surface_silent_margin.py`](../../tests/test_iter71_surface_silent_margin.py)
- Analyzer command: [`proof-margin/analyze_surface_silent_margin.command.txt`](proof-margin/analyze_surface_silent_margin.command.txt)
- JSON report: [`proof-margin/margin_report.json`](proof-margin/margin_report.json)
- Markdown report: [`proof-margin/margin.md`](proof-margin/margin.md)

## Result

The analyzer cross-checked:

- iteration-59 verdict: `ACTOR_MATCH_AUDIT_COMPLETE`;
- iteration-70 verdict: `HUGSIM_STRUCTURAL_TIMING_TAXONOMY_COMPLETE`;
- exactly the two fixed `foreground_present_surface_silent` rows;
- no row-level problems from iteration 70.

Summary:

- target rows: `2`;
- evaluated rows: `2`;
- row labels:
  - `surface_silent_far_margin`: `2`;
- near-margin rows: `0`;
- no-object rows: `0`;
- verdict: `HUGSIM_SURFACE_SILENT_MARGIN_COMPLETE`.

| audit id | scenario | label | min valid TTC | TTC margin | min CPA | CPA margin |
|---|---|---|---:|---:|---:|---:|
| `mixed_extreme` | `scene-0062-extreme-00` | `surface_silent_far_margin` | none | none | `4.1062 m` | `+2.6062 m` |
| `nofire_hard_control` | `scene-0041-hard-00` | `surface_silent_far_margin` | `5.9560 s` | `+3.4560 s` | `7.9779 m` | `+6.4779 m` |

## Interpretation

The two foreground-present surface-silent rows were not near misses against the frozen released
CPA/TTC trigger surfaces under the registered descriptive bands.

`mixed_extreme` had object rows before foreground contact but no valid finite TTC, and the closest
CPA remained `2.6062 m` outside the frozen `1.5 m` CPA margin. `nofire_hard_control` had object
rows, but its closest valid TTC remained `3.4560 s` above the frozen TTC threshold and its closest
CPA remained `6.4779 m` outside the frozen CPA margin.

This means the surface-silent branch is not explained by a small threshold miss in these two
rows. It remains a mechanism fact, not a repair authorization.

## Claim boundary

No actor-causality, repair, threshold-value, transfer improvement, safety, deployment readiness,
robustness, benchmark ranking, HD-Score-invariance, population-rate, retuning value, or commercial
value claim. This result only classifies the two fixed surface-silent rows by descriptive margins
to the frozen released-union trigger surfaces.
