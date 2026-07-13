# Iteration 72 - HUGSIM late-fire prefire margin audit: HUGSIM_LATE_FIRE_PREFIRE_MARGIN_COMPLETE

Status: `HUGSIM_LATE_FIRE_PREFIRE_MARGIN_COMPLETE` (offline prefire margin audit over the two
iteration-70 foreground-present late-fire rows).

This iteration launched no GPU work, read no live box state, created no HUGSIM episodes, changed
no thresholds, and did not retune Sentinel. It used only committed iteration-59 proof/report
artifacts and the committed iteration-70 structural timing report.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer: [`analyze_late_fire_prefire_margin.py`](analyze_late_fire_prefire_margin.py)
- Tests: [`../../tests/test_iter72_late_fire_prefire_margin.py`](../../tests/test_iter72_late_fire_prefire_margin.py)
- Analyzer command: [`proof-prefire/analyze_late_fire_prefire_margin.command.txt`](proof-prefire/analyze_late_fire_prefire_margin.command.txt)
- JSON report: [`proof-prefire/prefire_report.json`](proof-prefire/prefire_report.json)
- Markdown report: [`proof-prefire/prefire.md`](proof-prefire/prefire.md)

## Result

The analyzer cross-checked:

- iteration-59 verdict: `ACTOR_MATCH_AUDIT_COMPLETE`;
- iteration-70 verdict: `HUGSIM_STRUCTURAL_TIMING_TAXONOMY_COMPLETE`;
- exactly the two fixed `foreground_present_late_fire` rows;
- no row-level problems from iteration 70.

Summary:

- target rows: `2`;
- evaluated rows: `2`;
- row labels:
  - `late_fire_prefire_near_cpa_margin`: `1`;
  - `late_fire_prefire_near_ttc_margin`: `1`;
- near-margin rows: `2`;
- far-margin rows: `0`;
- no-object rows: `0`;
- verdict: `HUGSIM_LATE_FIRE_PREFIRE_MARGIN_COMPLETE`.

| audit id | scenario | label | fire delay | min valid TTC | TTC margin | min CPA | CPA margin |
|---|---|---|---:|---:|---:|---:|---:|
| `both_distinct_extreme` | `scene-0138-extreme-00` | `late_fire_prefire_near_cpa_margin` | `+1.75 s` | none | none | `2.0355 m` | `+0.5355 m` |
| `ttc_medium_a` | `scene-0071-medium-01` | `late_fire_prefire_near_ttc_margin` | `+1.75 s` | `3.2742 s` | `+0.7742 s` | `4.5137 m` | `+3.0137 m` |

## Interpretation

The two foreground-present late-fire rows differ from the surface-silent rows in iteration 71.

Both late-fire rows were near a frozen trigger surface before foreground contact, but neither had
an active crossing before contact. `both_distinct_extreme` was near the CPA surface before contact
(`+0.5355 m` outside the frozen CPA margin), while `ttc_medium_a` was near the TTC surface before
contact (`+0.7742 s` above the frozen TTC threshold). In both rows, the first actual fire still
arrived `1.75 s` after first foreground contact.

This supports a late-threshold-crossing mechanism for these two rows under the registered
descriptive bands. It does not authorize changing thresholds.

## Claim boundary

No actor-causality, repair, threshold-value, transfer improvement, safety, deployment readiness,
robustness, benchmark ranking, HD-Score-invariance, population-rate, retuning value, or commercial
value claim. This result only classifies the two fixed late-fire rows by descriptive prefire
margins to the frozen released-union trigger surfaces.
