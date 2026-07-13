# Iteration 84 - HUGSIM selected/support path-arbitration decomposition: HUGSIM_SELECTED_SURFACE_SUPPORT_BRIDGE_SPLIT_COMPLETE

Status: `HUGSIM_SELECTED_SURFACE_SUPPORT_BRIDGE_SPLIT_COMPLETE` (offline selected/support
arbitration decomposition over the three fixed iteration-79 event rows).

This iteration launched no GPU work, read no live box state, created no HUGSIM episodes, changed
no thresholds, and did not retune Sentinel. It used only committed iteration-59 proof/report
artifacts and the committed iteration-79, iteration-80, and iteration-83 reports.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer: [`analyze_selected_support_arbitration.py`](analyze_selected_support_arbitration.py)
- Tests: [`../../tests/test_iter84_selected_support_arbitration.py`](../../tests/test_iter84_selected_support_arbitration.py)
- Analyzer command: [`proof-arbitration/analyze_selected_support_arbitration.command.txt`](proof-arbitration/analyze_selected_support_arbitration.command.txt)
- JSON report: [`proof-arbitration/arbitration_report.json`](proof-arbitration/arbitration_report.json)
- Markdown report: [`proof-arbitration/arbitration.md`](proof-arbitration/arbitration.md)

## Result

The analyzer cross-checked:

- iteration-59 verdict: `ACTOR_MATCH_AUDIT_COMPLETE`;
- iteration-79 verdict: `HUGSIM_SELECTED_ACTIVE_SUPPORT_SUBTHRESHOLD_COMPLETE`;
- iteration-80 verdict: `HUGSIM_SELECTED_ALL_PROVENANCE_NO_SUPPORT_COMPLETE`;
- iteration-83 verdict: `HUGSIM_BRIDGE_SUPPORTED_SURFACE_MISS_MIXED_COMPLETE`;
- exactly the three fixed selected/support event rows.

Summary:

- target events: `3`;
- evaluated events: `3`;
- row labels:
  - `selected_surface_support_bridge_split`: `3`;
- support-better-bridge events: `3`;
- selected bridge-supported events: `0`;
- support bridge-supported events: `3`;
- hazard advantages:
  - `selected_lower_cpa`: `3`;
  - `selected_better_cpa_rank`: `3`;
  - `selected_finite_ttc_support_missing`: `1`.

| audit id | event | selected object | selected state | selected bridge | support object | support state | support bridge | selected CPA | support CPA | selected TTC |
|---|---|---:|---|---|---:|---|---|---:|---:|---:|
| `both_distinct_extreme` | `pre` | `5` | `borderline` | `no_support` | `9` | `subthreshold` | `ambiguous` | `2.0355 m` | `21.6343 m` | `None` |
| `ttc_medium_a` | `pre` | `6` | `borderline` | `no_support` | `10` | `subthreshold` | `match` | `9.2404 m` | `17.2764 m` | `3.2742 s` |
| `ttc_medium_a` | `active` | `24` | `active` | `no_support` | `10` | `subthreshold` | `match` | `1.2791 m` | `13.5578 m` | `None` |

## Interpretation

Iteration 84 closes the immediate selected-vs-support arbitration question for these three fixed
rows. The released monitor surface is consistently choosing the object with stronger logged path
geometry: the selected object has lower CPA and better CPA rank in all three rows, and one row
also has finite TTC while the support object has no finite TTC. At the same time, the selected
object has no provenance bridge support in all three rows, while the support object has better
foreground/provenance bridge support in all three rows.

The fixed rows therefore exhibit a clean split: released hazard-surface selection follows the
logged path geometry, while logged collision provenance points to a different surface-ineligible
support object. This is stronger than a generic "wrong object" claim and narrower than a repair:
it says the failure mechanism in these rows is a selected-surface/provenance-bridge arbitration
split under the frozen CPA/TTC surface.

## Claim boundary

Three-row descriptive selected/support arbitration decomposition only; no actor-causality, repair,
threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate,
HD-Score-invariance, commercial-value, real-world behavior, first-responder behavior, or retuning
claim.
