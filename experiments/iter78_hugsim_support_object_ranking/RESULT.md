# Iteration 78 - HUGSIM support-object ranking audit: HUGSIM_SUPPORT_OBJECT_RANKING_MIXED_COMPLETE

Status: `HUGSIM_SUPPORT_OBJECT_RANKING_MIXED_COMPLETE` (offline ranking audit over the three
iteration-77 foreground-supported full-object-set events).

This iteration launched no GPU work, read no live box state, created no HUGSIM episodes, changed
no thresholds, and did not retune Sentinel. It used only committed iteration-59 proof/report
artifacts and the committed iteration-70, iteration-72, iteration-73, iteration-74, iteration-75,
iteration-76, and iteration-77 reports.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer: [`analyze_support_object_ranking.py`](analyze_support_object_ranking.py)
- Tests: [`../../tests/test_iter78_support_object_ranking.py`](../../tests/test_iter78_support_object_ranking.py)
- Analyzer command: [`proof-ranking/analyze_support_object_ranking.command.txt`](proof-ranking/analyze_support_object_ranking.command.txt)
- JSON report: [`proof-ranking/ranking_report.json`](proof-ranking/ranking_report.json)
- Markdown report: [`proof-ranking/ranking.md`](proof-ranking/ranking.md)

## Result

The analyzer cross-checked:

- iteration-59 verdict: `ACTOR_MATCH_AUDIT_COMPLETE`;
- iteration-70 verdict: `HUGSIM_STRUCTURAL_TIMING_TAXONOMY_COMPLETE`;
- iteration-72 verdict: `HUGSIM_LATE_FIRE_PREFIRE_MARGIN_COMPLETE`;
- iteration-73 verdict: `HUGSIM_MARGIN_TRANSITION_SPLIT_COMPLETE`;
- iteration-74 verdict: `HUGSIM_LATE_FIRE_CROSS_CHANNEL_DELAY_COMPLETE`;
- iteration-75 verdict: `HUGSIM_CROSS_CHANNEL_OBJECT_SWITCH_COMPLETE`;
- iteration-76 verdict: `HUGSIM_SWITCH_FOREGROUND_BOTH_OR_AMBIGUOUS_COMPLETE`;
- iteration-77 verdict: `HUGSIM_EVENT_SET_FOREGROUND_SUPPORT_MIXED_COMPLETE`;
- exactly the three fixed iteration-77 support events.

Summary:

- target events: `3`;
- evaluated events: `3`;
- row labels:
  - `support_object_nonselected_subthreshold`: `3`;
- nonselected active events: `0`;
- nonselected borderline events: `0`;
- selected events: `0`;
- verdict: `HUGSIM_SUPPORT_OBJECT_RANKING_MIXED_COMPLETE`.

| audit id | event | support object | selected object | label | cpa rank | min cpa | ttc |
|---|---|---:|---:|---|---:|---:|---:|
| `both_distinct_extreme` | `pre` | `9` | `5` | `support_object_nonselected_subthreshold` | `4` | `21.6343 m` | `None` |
| `ttc_medium_a` | `pre` | `10` | `6` | `support_object_nonselected_subthreshold` | `7` | `17.2764 m` | `None` |
| `ttc_medium_a` | `active` | `10` | `24` | `support_object_nonselected_subthreshold` | `2` | `13.5578 m` | `None` |

## Interpretation

Iteration 77 showed that the full event-row object set can contain foreground-supported objects
even when the selected switched hazard objects do not bridge to foreground. Iteration 78 shows
that those foreground-supported objects are not selected by the released monitor surface and do
not cross even the registered borderline CPA/TTC bands at the fixed event rows.

That narrows the mechanism lead. The evidence no longer points to simple absence of foreground
geometry in the monitor stream, and it also does not support an explanation where the
foreground-supported object is already an active or near-active hazard that merely lost final
selection. The fixed support objects are visible, nonselected, and subthreshold under the logged
surface.

## Claim boundary

No actor-causality, repair, threshold-value, transfer improvement, safety, deployment readiness,
robustness, benchmark ranking, HD-Score-invariance, population-rate, retuning value, or commercial
value claim. This result only classifies three fixed foreground-supported event objects by
selection and frozen CPA/TTC ranking state.
