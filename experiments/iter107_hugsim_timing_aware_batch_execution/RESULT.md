# Iteration 107 - HUGSIM timing-aware batch execution: HUGSIM_TIMING_AWARE_BATCH_EXECUTION_COMPLETE

Status: `HUGSIM_TIMING_AWARE_BATCH_EXECUTION_COMPLETE` (slot-level HUGSIM provenance execution
proof for the iteration-106 timing-aware manifest).

This iteration executed the registered 13-slot ON batch on the GPU box under the byte-bound HUGSIM
collision-provenance patch and released-union monitor patch. It changed no thresholds, HUGSIM
metric constants, planner code, action-control code, scenario selection, or HD-Score formulas.
It does not classify actor matches and does not claim a repair.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Launcher: [`run_timing_aware_batch_execution.sh`](run_timing_aware_batch_execution.sh)
- Analyzer:
  [`analyze_timing_aware_batch_execution.py`](analyze_timing_aware_batch_execution.py)
- Tests:
  [`../../tests/test_iter107_timing_aware_batch_execution.py`](../../tests/test_iter107_timing_aware_batch_execution.py)
- Analyzer command:
  [`proof-execution/analyze_timing_aware_batch_execution.command.txt`](proof-execution/analyze_timing_aware_batch_execution.command.txt)
- JSON report:
  [`proof-execution/timing_aware_batch_execution_report.json`](proof-execution/timing_aware_batch_execution_report.json)
- Markdown report:
  [`proof-execution/timing_aware_batch_execution.md`](proof-execution/timing_aware_batch_execution.md)
- Run log:
  [`proof-execution/i107-timing-aware-batch-run.log`](proof-execution/i107-timing-aware-batch-run.log)
- Receipts and manifests:
  [`proof-execution/receipts.json`](proof-execution/receipts.json),
  [`proof-execution/frozen_manifest.sha256`](proof-execution/frozen_manifest.sha256),
  [`proof-execution/frozen_scenarios_iter107.sha256`](proof-execution/frozen_scenarios_iter107.sha256),
  [`proof-execution/slot_schedule_iter107.tsv`](proof-execution/slot_schedule_iter107.tsv),
  [`proof-execution/heavy_manifest_iter107.txt`](proof-execution/heavy_manifest_iter107.txt),
  [`proof-execution/proof_archive.sha256`](proof-execution/proof_archive.sha256)

## Result

The launcher completed all 13 registered slots on first attempt:

- completed slots: `13/13`;
- retries: `0`;
- collected slot ids match the iteration-106 manifest order: `true`;
- unique scenarios: `11`;
- duplicate scenario groups preserved: `2`;
- duplicate slots preserved: `4`;
- slots with complete proof artifacts: `13/13`;
- slots with `collision_provenance` key in `eval.json`: `13/13`;
- total collision-provenance rows: `252`;
- slots with finite HD-Score: `13/13`.

Per-slot descriptive execution summary:

| slot | scenario | run | HD-Score | steps | provenance rows |
|---:|---|---:|---:|---:|---:|
| 1 | `scene-0138-medium-01` | 1 | `0.7692097454143353` | 126 | 12 |
| 2 | `scene-0064-hard-00` | 2 | `0.3029107939472085` | 90 | 39 |
| 3 | `scene-0166-easy-00` | 2 | `0.9280500521376424` | 137 | 0 |
| 4 | `scene-0138-medium-01` | 2 | `0.44087154483601426` | 67 | 3 |
| 5 | `scene-0064-easy-00` | 2 | `0.7084148727984348` | 146 | 33 |
| 6 | `scene-0166-medium-01` | 2 | `0.43247164838459995` | 103 | 32 |
| 7 | `scene-0064-hard-00` | 1 | `0.5481931334625358` | 153 | 48 |
| 8 | `scene-0411-extreme-00` | 1 | `0.08435831813760336` | 27 | 5 |
| 9 | `scene-0071-easy-00` | 2 | `0.6021008068381027` | 142 | 24 |
| 10 | `scene-0411-hard-00` | 2 | `0.07093223850965198` | 27 | 6 |
| 11 | `scene-0138-hard-00` | 1 | `0.11067041298220909` | 37 | 10 |
| 12 | `scene-0071-extreme-00` | 1 | `0.08458208801654708` | 37 | 8 |
| 13 | `scene-0064-medium-01` | 1 | `0.655051975127951` | 146 | 32 |

## Interpretation

Iteration 107 retires the execution blocker for the timing-aware provenance batch. The
iteration-106 manifest was not collapsed by scenario: both duplicate scenario groups stayed
represented as distinct slot directories (`scene-0138-medium-01` runs 1 and 2, and
`scene-0064-hard-00` runs 2 and 1).

The batch also confirms that the byte-bound provenance patch still emits the top-level
`collision_provenance` key in every completed eval, with `252` total provenance rows across the
13 slots. Slot 3 has zero provenance rows while still carrying the required top-level key; that is
compatible with this execution proof because the bar required key presence, not actor-match
support classification.

The next scientific step is a separate pre-registered analyzer over this proof that asks whether
the timing-aware redesign improved foreground actor-match support relative to the iteration-104
`1/13` classifiable-support null. Iteration 107 itself does not answer that question.

## Claim boundary

HUGSIM timing-aware batch execution proof only; no actor-causality, actor-match interpretation,
repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate,
HD-Score-invariance, real-world behavior, first-responder behavior, acquisition-value, retuning,
production, or commercial claim.
