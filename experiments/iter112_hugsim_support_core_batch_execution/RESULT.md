# Iteration 112 - HUGSIM support-core batch execution: HUGSIM_SUPPORT_CORE_BATCH_EXECUTION_COMPLETE

Status: `HUGSIM_SUPPORT_CORE_BATCH_EXECUTION_COMPLETE` (slot-level execution proof for the
iteration-111 support-core manifest).

This iteration executed exactly the `8` ON slots frozen in the iteration-111 launch manifest under
the byte-bound HUGSIM provenance patch and released-union monitor patch. It used no OFF arm,
changed no Sentinel thresholds, changed no planner/action-control code, changed no HUGSIM metric
formulas, and did not retune Sentinel.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Launcher:
  [`run_support_core_batch_execution.sh`](run_support_core_batch_execution.sh)
- Analyzer:
  [`analyze_support_core_batch_execution.py`](analyze_support_core_batch_execution.py)
- Tests:
  [`../../tests/test_iter112_support_core_batch_execution.py`](../../tests/test_iter112_support_core_batch_execution.py)
- Box launch command:
  [`proof-execution/box_launch.command.txt`](proof-execution/box_launch.command.txt)
- Analyzer command:
  [`proof-execution/analyze_support_core_batch_execution.command.txt`](proof-execution/analyze_support_core_batch_execution.command.txt)
- Proof archive SHA256:
  [`proof-execution/proof_archive.sha256`](proof-execution/proof_archive.sha256)
- Receipts:
  [`proof-execution/receipts.json`](proof-execution/receipts.json)
- Frozen manifest SHA:
  [`proof-execution/frozen_manifest.sha256`](proof-execution/frozen_manifest.sha256)
- Frozen scenario SHAs:
  [`proof-execution/frozen_scenarios_iter112.sha256`](proof-execution/frozen_scenarios_iter112.sha256)
- GPU run log:
  [`proof-execution/i112-support-core-batch-run.log`](proof-execution/i112-support-core-batch-run.log)
- Heavy artifact manifest:
  [`proof-execution/heavy_manifest_iter112.txt`](proof-execution/heavy_manifest_iter112.txt)
- JSON report:
  [`proof-execution/support_core_batch_execution_report.json`](proof-execution/support_core_batch_execution_report.json)
- Markdown report:
  [`proof-execution/support_core_batch_execution.md`](proof-execution/support_core_batch_execution.md)

The light proof archive copied from the GPU is SHA-bound as
`9432f36e1a8d21532a1e3f2ebf0d7ac1bc8f465705e0f8ad17e65737e1e70295`.

## Result

The batch completed with no analyzer-reported infrastructure problems:

- manifest slot count: `8`;
- completed slot count: `8`;
- proof-complete slot count: `8`;
- evals exposing top-level `collision_provenance`: `8`;
- total collision-provenance rows: `44`;
- HD-Score-present slots: `8`;
- collected slot ids match the manifest: `true`;
- unique scenario count: `5`;
- duplicate scenario groups preserved by `slot_id`: `3`;
- duplicate slots: `6`.

Slot measurements:

| slot | scenario | run | role | complete | provenance rows | hdscore |
|---:|---|---:|---|---|---:|---:|
| 1 | `scene-0411-hard-00` | 2 | `exact_ttc_classifiable_anchor` | `true` | 7 | `0.08122778174910576` |
| 2 | `scene-0411-extreme-00` | 1 | `exact_ttc_classifiable_anchor` | `true` | 5 | `0.08385317850803686` |
| 3 | `scene-0038-hard-00` | 1 | `exact_ttc_classifiable_anchor` | `true` | 4 | `0.13052950648858583` |
| 4 | `scene-0038-extreme-00` | 1 | `ttc_classifiable_scenario_analogue` | `true` | 8 | `0.044995073128065464` |
| 5 | `scene-0038-extreme-00` | 2 | `ttc_classifiable_scenario_analogue` | `true` | 7 | `0.08383815147100172` |
| 6 | `scene-0383-extreme-00` | 2 | `ttc_classifiable_scenario_analogue` | `true` | 5 | `0.35583905370273633` |
| 7 | `scene-0411-hard-00` | 1 | `ttc_classifiable_scenario_analogue` | `true` | 3 | `0.11152001784320285` |
| 8 | `scene-0411-extreme-00` | 2 | `ttc_classifiable_scenario_analogue` | `true` | 5 | `0.11964026296891593` |

## Interpretation

Iteration 112 turns the iteration-111 support-core manifest into committed execution proof. The
slot-keyed launcher preserved all three duplicate scenario groups as distinct slot directories, and
every successful slot carries the required `eval.json`, `output.txt`, `episode_meta.json`, and
`sentinel_iter48_decisions.jsonl` artifacts.

This result does not classify the collision actors and does not say whether the rerun rows remain
foreground-classifiable under the frozen iteration-59 actor-match rules. The next honest step is a
separately pre-registered actor-match support audit over this committed proof.

## Claim boundary

HUGSIM support-core batch execution proof only; no actor-causality, actor-match interpretation,
repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate,
HD-Score-invariance, real-world behavior, first-responder behavior, acquisition-value, retuning,
production, or commercial claim.
