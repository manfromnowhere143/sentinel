# Iteration 103 - HUGSIM provenance batch execution: HUGSIM_PROVENANCE_BATCH_EXECUTION_COMPLETE

Status: `HUGSIM_PROVENANCE_BATCH_EXECUTION_COMPLETE` (slot-level HUGSIM provenance execution
proof for the iteration-102 manifest).

This iteration executed the registered 13-slot ON batch on the GPU box under the byte-bound HUGSIM
collision-provenance patch and released-union monitor patch. It changed no thresholds, HUGSIM
metric constants, planner code, action-control code, scenario selection, or HD-Score formulas.
It does not classify actor matches and does not claim a repair.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Launcher: [`run_provenance_batch_execution.sh`](run_provenance_batch_execution.sh)
- Analyzer:
  [`analyze_provenance_batch_execution.py`](analyze_provenance_batch_execution.py)
- Tests:
  [`../../tests/test_iter103_provenance_batch_execution.py`](../../tests/test_iter103_provenance_batch_execution.py)
- Box launch command:
  [`proof-execution/box_launch.command.txt`](proof-execution/box_launch.command.txt)
- Analyzer command:
  [`proof-execution/analyze_provenance_batch_execution.command.txt`](proof-execution/analyze_provenance_batch_execution.command.txt)
- JSON report:
  [`proof-execution/provenance_batch_execution_report.json`](proof-execution/provenance_batch_execution_report.json)
- Markdown report:
  [`proof-execution/provenance_batch_execution.md`](proof-execution/provenance_batch_execution.md)
- Run log:
  [`proof-execution/i103-provenance-batch-run.log`](proof-execution/i103-provenance-batch-run.log)
- Receipts and manifests:
  [`proof-execution/receipts.json`](proof-execution/receipts.json),
  [`proof-execution/frozen_manifest.sha256`](proof-execution/frozen_manifest.sha256),
  [`proof-execution/frozen_scenarios_iter103.sha256`](proof-execution/frozen_scenarios_iter103.sha256),
  [`proof-execution/heavy_manifest_iter103.txt`](proof-execution/heavy_manifest_iter103.txt)

## Result

The launcher completed all 13 registered slots on first attempt:

- completed slots: `13/13`;
- retries: `0`;
- collected slot ids match the iteration-102 manifest order: `true`;
- unique scenarios: `9`;
- duplicate scenario groups preserved: `4`;
- duplicate slots preserved: `8`;
- slots with complete proof artifacts: `13/13`;
- slots with `collision_provenance` key in `eval.json`: `13/13`;
- total collision-provenance rows: `217`;
- slots with finite HD-Score: `13/13`.

Per-slot descriptive execution summary:

| slot | scenario | run | HD-Score | steps | provenance rows |
|---:|---|---:|---:|---:|---:|
| 1 | `scene-0013-easy-00` | 1 | `0.16773162939297126` | 16 | 0 |
| 2 | `scene-0013-easy-00` | 2 | `0.16773162939297126` | 16 | 0 |
| 3 | `scene-0038-medium-01` | 1 | `0.5282331934384059` | 126 | 1 |
| 4 | `scene-0062-medium-00` | 2 | `0.4146361408854252` | 101 | 12 |
| 5 | `scene-0051-easy-00` | 1 | `0.3511572226656027` | 179 | 80 |
| 6 | `scene-0051-easy-00` | 2 | `0.4292237442922374` | 219 | 75 |
| 7 | `scene-0041-extreme-00` | 2 | `0.0902911675917811` | 25 | 7 |
| 8 | `scene-0062-hard-00` | 1 | `0.274339562295472` | 61 | 1 |
| 9 | `scene-0013-extreme-00` | 1 | `0.008209087681931132` | 12 | 11 |
| 10 | `scene-0013-extreme-00` | 2 | `0.00813513193704887` | 12 | 11 |
| 11 | `scene-0038-hard-00` | 1 | `0.14451788620586578` | 44 | 3 |
| 12 | `scene-0038-hard-00` | 2 | `0.1528465784696083` | 43 | 2 |
| 13 | `scene-0138-extreme-00` | 1 | `0.1135355017986909` | 30 | 14 |

## Interpretation

Iteration 103 retires the execution blocker for the 13-slot provenance batch. The manifest was
not collapsed by scenario: duplicate scenario groups stayed represented as distinct slot
directories, including both `scene-0013-easy-00` slots, both `scene-0051-easy-00` slots, both
`scene-0013-extreme-00` slots, and both `scene-0038-hard-00` slots.

The batch also confirms that the byte-bound provenance patch still emits the top-level
`collision_provenance` key in every completed eval. Two no-fire slots have zero provenance rows;
that is compatible with this execution proof because the bar required key presence, not an
actor-match-support classification.

The next scientific step is a separate pre-registered analyzer over this proof that asks which
slots are classifiable for monitor-hazard versus HUGSIM collision actor comparison. Iteration 103
itself does not answer that question.

## Claim boundary

HUGSIM provenance batch execution proof only; no actor-causality, actor-match interpretation,
repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate,
HD-Score-invariance, real-world behavior, first-responder behavior, acquisition-value, or retuning
claim.
