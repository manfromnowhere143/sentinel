# Iteration 105 - HUGSIM timing-aware provenance batch design: HUGSIM_TIMING_AWARE_BATCH_DESIGN_COMPLETE

Status: `HUGSIM_TIMING_AWARE_BATCH_DESIGN_COMPLETE` (offline next-run candidate schedule design
after the iteration-104 actor-match support null).

This iteration changed the candidate-selection basis from iteration 101's monitor-provenance
strata to timing-aware support yield. It used only committed reports, launched no GPU work, read
no raw episode directories, changed no thresholds, changed no planner/action-control code, and
did not retune Sentinel.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer:
  [`analyze_timing_aware_provenance_batch_design.py`](analyze_timing_aware_provenance_batch_design.py)
- Tests:
  [`../../tests/test_iter105_timing_aware_provenance_batch_design.py`](../../tests/test_iter105_timing_aware_provenance_batch_design.py)
- Analyzer command:
  [`proof-design/analyze_timing_aware_provenance_batch_design.command.txt`](proof-design/analyze_timing_aware_provenance_batch_design.command.txt)
- JSON report:
  [`proof-design/timing_aware_provenance_batch_design_report.json`](proof-design/timing_aware_provenance_batch_design_report.json)
- Markdown report:
  [`proof-design/timing_aware_provenance_batch_design.md`](proof-design/timing_aware_provenance_batch_design.md)

## Result

The timing-aware design passed the frozen bar:

- primary eligible rows after excluding iteration-59/104 instrumented scenarios: `20`;
- excluded eligible rows from already instrumented scenarios: `15`;
- selected future slots: `13`;
- selected unique scenarios: `11`;
- selected datasets: `iter48_easy_medium: 7`, `iter49_hard_extreme: 6`;
- selected channels: `cpa_only: 8`, `ttc_only: 5`;
- selected tiers: `easy: 3`, `medium: 4`, `hard: 4`, `extreme: 2`;
- selected timing labels: `long_lead_fire: 12`, `short_lead_fire: 1`;
- primary pool timing labels: `long_lead_fire: 16`, `short_lead_fire: 4`.

Selected future schedule:

| slot | scenario | run | dataset | tier | channel | timing | lead s | brake frames |
|---:|---|---:|---|---|---|---|---:|---:|
| 1 | `scene-0138-medium-01` | 1 | `iter48_easy_medium` | `medium` | `ttc_only` | `long_lead_fire` | `27.0` | 71 |
| 2 | `scene-0064-hard-00` | 2 | `iter49_hard_extreme` | `hard` | `cpa_only` | `long_lead_fire` | `5.5` | 29 |
| 3 | `scene-0166-easy-00` | 2 | `iter48_easy_medium` | `easy` | `cpa_only` | `long_lead_fire` | `14.5` | 12 |
| 4 | `scene-0138-medium-01` | 2 | `iter48_easy_medium` | `medium` | `ttc_only` | `long_lead_fire` | `18.0` | 51 |
| 5 | `scene-0064-easy-00` | 2 | `iter48_easy_medium` | `easy` | `cpa_only` | `long_lead_fire` | `9.75` | 12 |
| 6 | `scene-0166-medium-01` | 2 | `iter48_easy_medium` | `medium` | `cpa_only` | `long_lead_fire` | `13.0` | 37 |
| 7 | `scene-0064-hard-00` | 1 | `iter49_hard_extreme` | `hard` | `cpa_only` | `long_lead_fire` | `5.25` | 27 |
| 8 | `scene-0411-extreme-00` | 1 | `iter49_hard_extreme` | `extreme` | `ttc_only` | `long_lead_fire` | `4.5` | 10 |
| 9 | `scene-0071-easy-00` | 2 | `iter48_easy_medium` | `easy` | `ttc_only` | `long_lead_fire` | `5.5` | 18 |
| 10 | `scene-0411-hard-00` | 2 | `iter49_hard_extreme` | `hard` | `ttc_only` | `short_lead_fire` | `0.25` | 7 |
| 11 | `scene-0138-hard-00` | 1 | `iter49_hard_extreme` | `hard` | `cpa_only` | `long_lead_fire` | `4.25` | 19 |
| 12 | `scene-0071-extreme-00` | 1 | `iter49_hard_extreme` | `extreme` | `cpa_only` | `long_lead_fire` | `4.0` | 26 |
| 13 | `scene-0064-medium-01` | 1 | `iter48_easy_medium` | `medium` | `cpa_only` | `long_lead_fire` | `3.0` | 28 |

## Interpretation

Iteration 105 is the corrective step after the iteration-104 support null. The previous
instrumented batch proved the provenance mechanism and slot-level execution, but it was not
targeted enough for actor-match support: most slots were background-only, no-fire, or
post-collision-fire. The new schedule deliberately selects rows where the released union fired at
or before the first ON collision time, while preserving dataset, channel, tier, and timing
diversity.

This is still only a schedule. The next honest move is a separate launch-manifest preflight that
binds these 13 future slots to scenario hashes, frozen stack receipts, and slot ids. Only after
that preflight would a separate launch step be eligible for operator-approved GPU execution.

## Claim boundary

Offline timing-aware candidate-schedule design only; no GPU approval, launch authorization,
actor-causality, actor-match result, repair, threshold-value, transfer, safety, deployment,
robustness, benchmark, population-rate, HD-Score-invariance, real-world behavior, first-responder
behavior, acquisition-value, retuning, production, or commercial claim.
