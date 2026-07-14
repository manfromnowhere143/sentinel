# Iteration 110 - HUGSIM support-preserving candidate design: HUGSIM_SUPPORT_PRESERVING_CANDIDATE_DESIGN_CORE_COMPLETE

Status: `HUGSIM_SUPPORT_PRESERVING_CANDIDATE_DESIGN_CORE_COMPLETE` (offline
support-preserving candidate-core design).

This iteration used only committed iteration-52, iteration-54, iteration-59, iteration-104, and
iteration-109 reports. It launched no GPU work, generated no launch manifest, changed no
thresholds, changed no planner/action-control code, changed no HUGSIM metrics, and did not retune
Sentinel.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Analyzer:
  [`analyze_support_preserving_candidate_design.py`](analyze_support_preserving_candidate_design.py)
- Tests:
  [`../../tests/test_iter110_support_preserving_candidate_design.py`](../../tests/test_iter110_support_preserving_candidate_design.py)
- Analyzer command:
  [`proof-design/analyze_support_preserving_candidate_design.command.txt`](proof-design/analyze_support_preserving_candidate_design.command.txt)
- JSON report:
  [`proof-design/support_preserving_candidate_design_report.json`](proof-design/support_preserving_candidate_design_report.json)
- Markdown report:
  [`proof-design/support_preserving_candidate_design.md`](proof-design/support_preserving_candidate_design.md)

## Result

The analyzer completed with no infrastructure problems:

- timing-eligible iteration-54 rows: `35`;
- support-preserving core rows: `8`;
- exact TTC classifiable anchors: `3`;
- TTC classifiable scenario analogues: `5`;
- core channel counts: `{'ttc_only': 8}`;
- core timing counts: `{'short_lead_fire': 5, 'long_lead_fire': 3}`;
- fallback pressure rows: `27`;
- fallback split: `8` TTC residual-risk probes and `19` CPA residual-risk fallback rows;
- fresh primary rows after excluding every prior-support scenario: `3`;
- fresh primary channel counts: `{'cpa_only': 3}`;
- full `13`-slot support-preserving schedule available: `False`.

Support-preserving core:

| role | scenario | run | dataset | tier | timing | lead s | evidence |
|---|---|---:|---|---|---|---:|---|
| `exact_ttc_classifiable_anchor` | `scene-0411-hard-00` | 2 | `iter49_hard_extreme` | `hard` | `short_lead_fire` | `0.25` | `iter109:classifiable_success` |
| `exact_ttc_classifiable_anchor` | `scene-0411-extreme-00` | 1 | `iter49_hard_extreme` | `extreme` | `long_lead_fire` | `4.5` | `iter109:classifiable_success` |
| `exact_ttc_classifiable_anchor` | `scene-0038-hard-00` | 1 | `iter49_hard_extreme` | `hard` | `long_lead_fire` | `1.5` | `iter104:classifiable_foreground` |
| `ttc_classifiable_scenario_analogue` | `scene-0038-extreme-00` | 1 | `iter49_hard_extreme` | `extreme` | `short_lead_fire` | `1.0` | `iter59:classifiable_foreground` |
| `ttc_classifiable_scenario_analogue` | `scene-0038-extreme-00` | 2 | `iter49_hard_extreme` | `extreme` | `short_lead_fire` | `0.75` | `iter59:classifiable_foreground` |
| `ttc_classifiable_scenario_analogue` | `scene-0383-extreme-00` | 2 | `iter49_hard_extreme` | `extreme` | `short_lead_fire` | `0.75` | `iter59:classifiable_foreground` |
| `ttc_classifiable_scenario_analogue` | `scene-0411-hard-00` | 1 | `iter49_hard_extreme` | `hard` | `short_lead_fire` | `0.25` | `iter109:classifiable_success` |
| `ttc_classifiable_scenario_analogue` | `scene-0411-extreme-00` | 2 | `iter49_hard_extreme` | `extreme` | `long_lead_fire` | `3.0` | `iter109:classifiable_success` |

Fresh primary rows were not support-preserving under the frozen rule:

| scenario | run | channel | timing | lead s |
|---|---:|---|---|---:|
| `scene-0064-medium-00` | 2 | `cpa_only` | `short_lead_fire` | `0.0` |
| `scene-0167-hard-00` | 2 | `cpa_only` | `long_lead_fire` | `2.0` |
| `scene-0166-hard-00` | 2 | `cpa_only` | `long_lead_fire` | `1.25` |

## Interpretation

Iteration 110 converts the iteration-109 residual insight into a deterministic design boundary.
There is enough committed evidence for a focused support-preserving core: `8` TTC rows clear the
frozen four-row core floor, including `3` exact classifiable anchors and `5` scenario-level
analogues.

There is not enough evidence for a clean `13`-slot support-preserving schedule. Filling the batch
to `13` would require rows that the frozen rule deliberately separates as residual risk: either
TTC rows with prior non-classifiable evidence or CPA rows, the channel that produced `0/8`
classifiable rows in iteration 109.

The next honest successor, if this line proceeds toward execution, is a launch-manifest preflight
for the `8`-row support-preserving core only. That preflight would still be offline and would not
authorize GPU execution.

## Claim boundary

Offline support-preserving candidate-core design only; no actor-causality, actor-match support
upgrade, repair, threshold-value, transfer, safety, deployment, robustness, benchmark,
population-rate, HD-Score-invariance, real-world behavior, first-responder behavior,
acquisition-value, retuning, production, commercial, launch-manifest, launch authorization, or
GPU-approval claim.
