# Iteration 58 - HUGSIM provenance instrumented canary: PROVENANCE_CANARY_COMPLETE

Status: `PROVENANCE_CANARY_COMPLETE` (two-episode HUGSIM instrumentation canary).

This iteration ran exactly the pre-registered `scene-0013-hard-00` OFF r1 then ON r1 schedule on
the frozen HUGSIM stack. It did not run an expanded transfer benchmark, did not retune Sentinel,
did not inspect actor-match outcomes before registration, and did not claim safety, deployment,
benchmark, HD-Score invariance, or actor attribution.

## Frozen proof

- Pre-registration: [`HYPOTHESIS.md`](HYPOTHESIS.md)
- Launcher: [`run_provenance_canary.sh`](run_provenance_canary.sh)
- Analyzer: [`analyze_provenance_canary.py`](analyze_provenance_canary.py)
- Tests: [`../../tests/test_iter58_provenance_canary.py`](../../tests/test_iter58_provenance_canary.py)
- Raw proof: [`proof-canary/`](proof-canary/)
- Analyzer command: [`proof-canary/analyze_provenance_canary.command.txt`](proof-canary/analyze_provenance_canary.command.txt)
- JSON report: [`proof-canary/provenance_canary_report.json`](proof-canary/provenance_canary_report.json)
- Markdown report: [`proof-canary/provenance_canary.md`](proof-canary/provenance_canary.md)

## Result

The analyzer returned:

- `completed_rows`: `2`;
- `collision_rows`: `2`;
- `provenance_rows`: `2`;
- `on_decision_log_present`: `true`;
- verdict: `PROVENANCE_CANARY_COMPLETE`.

Both scheduled episodes completed on the first attempt:

| episode | `nc_min` | provenance count | detail rows scalar-only | problems |
|---|---:|---:|---|---|
| `scene-0013-hard-00__off_r1` | `0.0` | `11` | `true` | `[]` |
| `scene-0013-hard-00__on_r1` | `0.0` | `13` | `true` | `[]` |

The top-level scalar metric keys stayed present in both `eval.json` files:
`nc`, `dac`, `ttc`, `c`, `pdms`, `rc`, and `hdscore`. The `details` rows remained scalar
metric rows only. The new provenance was emitted as a top-level `collision_provenance` list,
not inside scalar details rows.

The ON episode also carried the required Sentinel decision log:
[`proof-canary/episodes/scene-0013-hard-00__on_r1/sentinel_iter48_decisions.jsonl`](proof-canary/episodes/scene-0013-hard-00__on_r1/sentinel_iter48_decisions.jsonl).

## Receipts

The run receipts bind the instrumented canary to the frozen stack:

- HUGSIM source SHA: `62c690d39fd90020e68a196bd8bcc1c4d4191f2e`;
- UniAD_SIM source SHA: `5fb279e39912a5ac7f58e00d56b065cadcd0a749`;
- HUGSIM provenance patch SHA256:
  `49eee7611e4b881d2bb6233e8767913019c6a097c6883762414005d5b2284ecd`;
- released-union monitor patch SHA256:
  `6b39fd79d00c7bdb937c6d240fbc4648661b235f1a3024912d62874937146c5c`;
- scenario: `scene-0013-hard-00`;
- scenario SHA256: `6947a5381c09485f20d5fed55eef2406d868ce047bdd44864aad81902f54e48e`.

Heavy simulator artifacts were not copied into git. Their hashes and on-box paths are recorded in
[`proof-canary/heavy_manifest_iter58.txt`](proof-canary/heavy_manifest_iter58.txt).

## Interpretation

Iteration 57 proved the byte-identical patch was statically additive by source diff inspection.
Iteration 58 proves the same patch also executes in real HUGSIM episodes and emits a top-level
collision provenance sidecar under the registered canary envelope.

This retires the instrumentation-execution blocker for a later actor-match experiment. It does not
answer actor match by itself: the schedule contains only one scenario and two episodes, and the
iteration did not compare monitor hazard identity against collision actor identity across the
committed transfer failures.

## Claim boundary

This is a two-episode instrumentation canary only. It makes no transfer, benchmark, safety,
robustness, deployment, real-world, HD-Score-improvement, HD-Score-invariance, actor-match,
collision-cause, monitor-performance, production, acquisition-value, or retuning claim.
