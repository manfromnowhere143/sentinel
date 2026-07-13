# Iteration 94 - HUGSIM active-row surface margin arbitration: HUGSIM_ACTIVE_ROW_SURFACE_MARGIN_ARBITRATION_COMPLETE

Status: `HUGSIM_ACTIVE_ROW_SURFACE_MARGIN_ARBITRATION_COMPLETE` (offline active-row margin
arbitration over the fixed `ttc_medium_a` active replay row).

This iteration launched no GPU work, read no live box state, created no HUGSIM episodes, changed
no thresholds, read no raw decision logs, and did not retune Sentinel. It used only the committed
iteration-91, iteration-92, and iteration-93 reports.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer:
  [`analyze_active_row_surface_margin_arbitration.py`](analyze_active_row_surface_margin_arbitration.py)
- Tests:
  [`../../tests/test_iter94_active_row_surface_margin_arbitration.py`](../../tests/test_iter94_active_row_surface_margin_arbitration.py)
- Analyzer command:
  [`proof-margin/analyze_active_row_surface_margin_arbitration.command.txt`](proof-margin/analyze_active_row_surface_margin_arbitration.command.txt)
- JSON report:
  [`proof-margin/active_row_surface_margin_arbitration_report.json`](proof-margin/active_row_surface_margin_arbitration_report.json)
- Markdown report:
  [`proof-margin/active_row_surface_margin_arbitration.md`](proof-margin/active_row_surface_margin_arbitration.md)

## Result

The analyzer cross-checked:

- iteration-91 verdict: `HUGSIM_ACTIVE_GAP_PATH_PROVENANCE_DECOMPOSITION_COMPLETE`;
- iteration-92 verdict: `HUGSIM_PATH_PROXIMITY_ARBITRATION_SPLIT_COMPLETE`;
- iteration-93 verdict: `HUGSIM_SURFACE_WINNER_ALIGNMENT_MIXED_COMPLETE`;
- the fixed `ttc_medium_a` / `scene-0071-medium-01` / active row appears exactly once in all
  three source reports;
- iteration-91 row label: `path_active_provenance_far_with_bridge_nonactive`;
- iteration-92 row label: `path_best_active_no_bridge`;
- iteration-93 row label: `surface_follows_path_active_no_bridge`;
- iteration-93 surface follows path and does not follow provenance;
- the iteration-91 active candidate, iteration-92 path-best, and iteration-93 surface-best all
  identify object `24`.

Summary:

- target rows: `1`;
- evaluated rows: `1`;
- row label: `active_row_cpa_margin_overrides_provenance`;
- active candidate count: `1`;
- bridge-supported candidate count: `3`;
- bridge active or borderline count: `0`;
- bridge finite-TTC count: `0`;
- bridge non-positive active-CPA-margin count: `0`;
- active object: `24`;
- active CPA margin: `-0.49901426957705985 m`;
- minimum bridge-supported active CPA margin: `+10.643435514611875 m` on object `10`;
- active object has lower CPA than every bridge-supported object: `true`;
- active object has better CPA rank than every bridge-supported object: `true`.

| candidate set | object | state | bridge band | min CPA | CPA rank | TTC | active CPA margin |
|---|---:|---|---|---:|---:|---|---:|
| active surface/path | `24` | `active` | `no_support` | `1.0009857304229401` | `1` | `null` | `-0.49901426957705985` |
| bridge-supported | `6` | `subthreshold` | `ambiguous` | `19.42671009900369` | `5` | `null` | `17.92671009900369` |
| bridge-supported | `13` | `subthreshold` | `ambiguous` | `19.49972504369191` | `6` | `null` | `17.99972504369191` |
| bridge-supported | `10` | `subthreshold` | `ambiguous` | `12.143435514611875` | `3` | `null` | `10.643435514611875` |

## Interpretation

Iteration 94 explains the active `ttc_medium_a` surface-winner branch from committed reports only.
For this row, the released surface follows object `24` because it is the single active candidate
and it is the CPA/path winner. The provenance-near objects are not near misses under the released
surface in this row: all three bridge-supported candidates are subthreshold, have no finite TTC,
and remain CPA-far by at least `+10.6434 m` of active CPA margin.

This narrows the local mechanism: the active row is not an unresolved tie between active surface
and bridge-supported provenance objects. It is a path/CPA margin arbitration where the only
active object lacks provenance bridge support, while provenance-supported objects remain outside
the active surface.

## Claim boundary

One-row descriptive active-row margin arbitration only; no actor-causality, repair,
threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate,
HD-Score-invariance, commercial-value, real-world behavior, first-responder behavior, or retuning
claim.
