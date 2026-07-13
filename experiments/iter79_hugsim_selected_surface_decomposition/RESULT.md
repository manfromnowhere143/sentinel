# Iteration 79 - HUGSIM selected-object surface decomposition: HUGSIM_SELECTED_ACTIVE_SUPPORT_SUBTHRESHOLD_COMPLETE

Status: `HUGSIM_SELECTED_ACTIVE_SUPPORT_SUBTHRESHOLD_COMPLETE` (offline selected-vs-support
surface audit over the three iteration-78 fixed events).

This iteration launched no GPU work, read no live box state, created no HUGSIM episodes, changed
no thresholds, and did not retune Sentinel. It used only committed iteration-59 proof/report
artifacts and the committed iteration-75, iteration-77, and iteration-78 reports.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer: [`analyze_selected_surface_decomposition.py`](analyze_selected_surface_decomposition.py)
- Tests: [`../../tests/test_iter79_selected_surface_decomposition.py`](../../tests/test_iter79_selected_surface_decomposition.py)
- Analyzer command: [`proof-selected/analyze_selected_surface_decomposition.command.txt`](proof-selected/analyze_selected_surface_decomposition.command.txt)
- JSON report: [`proof-selected/selected_report.json`](proof-selected/selected_report.json)
- Markdown report: [`proof-selected/selected.md`](proof-selected/selected.md)

## Result

The analyzer cross-checked:

- iteration-59 verdict: `ACTOR_MATCH_AUDIT_COMPLETE`;
- iteration-75 verdict: `HUGSIM_CROSS_CHANNEL_OBJECT_SWITCH_COMPLETE`;
- iteration-77 verdict: `HUGSIM_EVENT_SET_FOREGROUND_SUPPORT_MIXED_COMPLETE`;
- iteration-78 verdict: `HUGSIM_SUPPORT_OBJECT_RANKING_MIXED_COMPLETE`;
- exactly the three fixed iteration-78 selected-vs-support comparison events.

Summary:

- target events: `3`;
- evaluated events: `3`;
- row labels:
  - `selected_active_support_subthreshold`: `1`;
  - `selected_borderline_support_subthreshold`: `2`;
- selected active events: `1`;
- selected borderline events: `2`;
- selected subthreshold events: `0`;
- verdict: `HUGSIM_SELECTED_ACTIVE_SUPPORT_SUBTHRESHOLD_COMPLETE`.

| audit id | event | selected object | selected state | selected min cpa | selected ttc | support object | support state | support min cpa |
|---|---|---:|---|---:|---:|---:|---|---:|
| `both_distinct_extreme` | `pre` | `5` | `borderline` | `2.0355 m` | `None` | `9` | `subthreshold` | `21.6343 m` |
| `ttc_medium_a` | `pre` | `6` | `borderline` | `9.2404 m` | `3.2742 s` | `10` | `subthreshold` | `17.2764 m` |
| `ttc_medium_a` | `active` | `24` | `active` | `1.2791 m` | `None` | `10` | `subthreshold` | `13.5578 m` |

## Interpretation

Iteration 78 showed that foreground-supported full-set objects are nonselected and subthreshold.
Iteration 79 shows the paired side: the selected objects are not arbitrary far objects. In the
same rows, the selected objects are either borderline under the registered bands or active under
the logged CPA/TTC surface, while the foreground-supported objects remain subthreshold.

This sharpens the mechanism lead. The fixed rows now separate foreground support from released
hazard-surface selection: the selected hazard-surface object lacks foreground bridge support,
while the foreground-supported object does not look hazardous to the logged surface. That is a
selection/surface/provenance split, not a repair claim.

## Claim boundary

No actor-causality, repair, threshold-value, transfer improvement, safety, deployment readiness,
robustness, benchmark ranking, HD-Score-invariance, population-rate, retuning value, or commercial
value claim. This result only classifies three fixed selected-vs-support event-object comparisons
by frozen CPA/TTC surface state.
