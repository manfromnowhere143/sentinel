# Iteration 88 - HUGSIM bridge/surface margin residual decomposition: HUGSIM_BRIDGE_SURFACE_MARGIN_RESIDUAL_SPLIT_COMPLETE

Status: `HUGSIM_BRIDGE_SURFACE_MARGIN_RESIDUAL_SPLIT_COMPLETE` (offline bridge/surface margin
residual decomposition over the three fixed iteration-87 replay rows).

This iteration launched no GPU work, read no live box state, created no HUGSIM episodes, read no
raw decision logs, changed no thresholds, and did not retune Sentinel. It used only the committed
iteration-85 and iteration-87 reports.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer: [`analyze_bridge_surface_margin_residual.py`](analyze_bridge_surface_margin_residual.py)
- Tests: [`../../tests/test_iter88_bridge_surface_margin_residual.py`](../../tests/test_iter88_bridge_surface_margin_residual.py)
- Analyzer command: [`proof-residual/analyze_bridge_surface_margin_residual.command.txt`](proof-residual/analyze_bridge_surface_margin_residual.command.txt)
- JSON report: [`proof-residual/bridge_surface_margin_residual_report.json`](proof-residual/bridge_surface_margin_residual_report.json)
- Markdown report: [`proof-residual/bridge_surface_margin_residual.md`](proof-residual/bridge_surface_margin_residual.md)

## Result

The analyzer cross-checked:

- iteration-85 verdict: `HUGSIM_PATH_HORIZON_BRIDGE_TIMING_SPLIT_COMPLETE`;
- iteration-87 verdict: `HUGSIM_INTERVAL_BRIDGE_TIME_SURFACE_REPLAY_MIXED_COMPLETE`;
- exactly the three fixed support-object rows and replay alignments.

Summary:

- target rows: `3`;
- evaluated rows: `3`;
- row labels:
  - `bridge_surface_ttc_borderline_cpa_far`: `1`;
  - `bridge_surface_no_finite_ttc_cpa_far`: `2`;
- support bridge bands:
  - `ambiguous`: `1`;
  - `match`: `2`;
- replay states:
  - `borderline`: `1`;
  - `subthreshold`: `2`.

| audit id | event | support object | bridge band | bridge distance | replay state | active CPA margin | replay TTC | active TTC margin | label |
|---|---|---:|---|---:|---|---:|---:|---:|---|
| `both_distinct_extreme` | `pre` | `9` | `ambiguous` | `3.6899 m` | `borderline` | `+20.0208 m` | `4.7761 s` | `+2.2761 s` | `bridge_surface_ttc_borderline_cpa_far` |
| `ttc_medium_a` | `pre` | `10` | `match` | `1.1245 m` | `subthreshold` | `+9.6354 m` | `None` | `None` | `bridge_surface_no_finite_ttc_cpa_far` |
| `ttc_medium_a` | `active` | `10` | `match` | `1.2931 m` | `subthreshold` | `+10.6434 m` | `None` | `None` | `bridge_surface_no_finite_ttc_cpa_far` |

## Interpretation

Iteration 88 closes the immediate margin-residual question after iteration 87. The support side is
not a uniform near-threshold miss. Object `9` has ambiguous provenance bridge support and reaches
only TTC-borderline, while remaining very CPA-far from active (`+20.0208 m`). Object `10` has
stronger provenance bridge matches, but at both replay rows it has no finite TTC and remains
CPA-far from active (`+9.6354 m` and `+10.6434 m`).

The fixed rows therefore split into one TTC-borderline/CPA-far residual and two
no-finite-TTC/CPA-far residuals. This sharpens the selected/support mechanism story: provenance
can identify support objects, but the released surface does not convert those support objects into
active hazards because their path/closing geometry remains outside the frozen surface.

## Claim boundary

Three-row descriptive bridge/surface margin residual decomposition only; no actor-causality,
repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate,
HD-Score-invariance, commercial-value, real-world behavior, first-responder behavior, or retuning
claim.
