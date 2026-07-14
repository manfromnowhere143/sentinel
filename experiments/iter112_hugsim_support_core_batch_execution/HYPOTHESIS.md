# Iteration 112 - HUGSIM support-core batch execution

Frozen before any iteration-112 launcher, analyzer, GPU command, simulator launch, proof artifact,
result, handoff update, or claim. This is the separately registered execution step for the
iteration-111 support-core slot-level manifest. It is not an actor-match interpretation, not a
repair, not a threshold change, and not a safety result.

## Context

Iteration 110 found that the committed HUGSIM pool supports an `8`-row TTC-only
support-preserving core, but not a clean `13`-slot support-preserving schedule. Iteration 111
converted that core into a byte-bound future-run manifest with `8` execution slots, `5` unique
scenarios, `3` duplicate scenario groups, and `8/8` scenario-SHA-bound slots.

This iteration asks only whether the registered support-core manifest can be executed under the
same byte-bound HUGSIM provenance instrumentation and released-union monitor patch used in
iterations 59, 103, and 107, while preserving slot identity. It does not interpret the resulting
collision actors.

## Frozen manifest

- Manifest path:
  `experiments/iter111_hugsim_support_core_launch_manifest/proof-launch-manifest/support_core_launch_manifest.json`
- Manifest SHA256:
  `a33888b174684b65758e74c949b05b695fda40ef3ddf0c7d9ee439a6ee818e99`
- Manifest report SHA256:
  `d3e3723621e16cc3ba61d47b38273effae586bebaa9e8a83e74300f0bab0b603`
- Manifest verdict required:
  `HUGSIM_SUPPORT_CORE_LAUNCH_MANIFEST_COMPLETE`

## Frozen schedule

Exactly `8` ON slots, in this order:

| slot | slot id | scenario | run | scenario SHA256 | design label |
|---:|---|---|---:|---|---|
| 1 | `i111_s01_iter49_hard_extreme_exact_ttc_classifiable_anchor_short_lead_fire_ttc_only_scene_0411_hard_00_r2` | `scene-0411-hard-00` | 2 | `9f38bbdcdc49fe6ac5274a967b9a209417d621f67060357b97deacb887cf67a9` | `exact_ttc_classifiable_anchor` |
| 2 | `i111_s02_iter49_hard_extreme_exact_ttc_classifiable_anchor_long_lead_fire_ttc_only_scene_0411_extreme_00_r1` | `scene-0411-extreme-00` | 1 | `cd9c86bd4dbad2e6ff74f275f9fe43ad60aa0d9bf314971473ae2ddb01b703fb` | `exact_ttc_classifiable_anchor` |
| 3 | `i111_s03_iter49_hard_extreme_exact_ttc_classifiable_anchor_long_lead_fire_ttc_only_scene_0038_hard_00_r1` | `scene-0038-hard-00` | 1 | `5e1dafedccdde485834d5809dee2fcd3cc0b5c31f7315e454d6b4bd8b04b146d` | `exact_ttc_classifiable_anchor` |
| 4 | `i111_s04_iter49_hard_extreme_ttc_classifiable_scenario_analogue_short_lead_fire_ttc_only_scene_0038_extreme_00_r1` | `scene-0038-extreme-00` | 1 | `ee3dafac4a7c8505829192906d4b39ad48cfed95d0e0fbebda64d86b99708776` | `ttc_classifiable_scenario_analogue` |
| 5 | `i111_s05_iter49_hard_extreme_ttc_classifiable_scenario_analogue_short_lead_fire_ttc_only_scene_0038_extreme_00_r2` | `scene-0038-extreme-00` | 2 | `ee3dafac4a7c8505829192906d4b39ad48cfed95d0e0fbebda64d86b99708776` | `ttc_classifiable_scenario_analogue` |
| 6 | `i111_s06_iter49_hard_extreme_ttc_classifiable_scenario_analogue_short_lead_fire_ttc_only_scene_0383_extreme_00_r2` | `scene-0383-extreme-00` | 2 | `f91d42db520f1e4d716fdbd3544fb701d4550062b2f9f933c86f3eb09c958ecf` | `ttc_classifiable_scenario_analogue` |
| 7 | `i111_s07_iter49_hard_extreme_ttc_classifiable_scenario_analogue_short_lead_fire_ttc_only_scene_0411_hard_00_r1` | `scene-0411-hard-00` | 1 | `9f38bbdcdc49fe6ac5274a967b9a209417d621f67060357b97deacb887cf67a9` | `ttc_classifiable_scenario_analogue` |
| 8 | `i111_s08_iter49_hard_extreme_ttc_classifiable_scenario_analogue_long_lead_fire_ttc_only_scene_0411_extreme_00_r2` | `scene-0411-extreme-00` | 2 | `cd9c86bd4dbad2e6ff74f275f9fe43ad60aa0d9bf314971473ae2ddb01b703fb` | `ttc_classifiable_scenario_analogue` |

No OFF arm is authorized. No extra scenario, replacement, deduplication, or schedule reorder is
authorized. Standard retry-once for infrastructure failure is authorized per slot.

## Frozen environment and patches

Hard launch gates:

- HUGSIM source HEAD must equal `62c690d39fd90020e68a196bd8bcc1c4d4191f2e`.
- UniAD_SIM source HEAD must equal `5fb279e39912a5ac7f58e00d56b065cadcd0a749`.
- checkpoint SHA must equal
  `0ad0c2f5dc9788a41c313305779ea49346aeb742d1f6bb5ad25c46f9beffc990`.
- shim SHA must equal `5bf69a1187478c52d49792d5871bd5732c6dd431ecd1f44b5e391f7adb80682c`.
- Docker image id must include `f73ef3884063`.
- HUGSIM provenance patch SHA must equal
  `49eee7611e4b881d2bb6233e8767913019c6a097c6883762414005d5b2284ecd`.
- Released-union monitor patch SHA must equal
  `6b39fd79d00c7bdb937c6d240fbc4648661b235f1a3024912d62874937146c5c`.
- Episode timeout: `1200` seconds.
- Disk guard: at least `20` GiB free under `/datasets/nuscenes-full`.
- Single-tenant rule: refuse to start if any Docker container is already running.
- Destination directories, skip checks, done markers, run logs, and collection paths must include
  `slot_id`.

The HUGSIM source tree may receive only the byte-bound provenance patch. The UniAD_SIM tree may
receive only the byte-bound released-union monitor patch. No Sentinel thresholds, HUGSIM metric
constants, scenario selection, planner code, action-control code, or HD-Score formulas may change.

## Frozen bars

- `HUGSIM_SUPPORT_CORE_BATCH_EXECUTION_INFRA_NULL`: any hard launch gate fails; the manifest SHA
  check fails; any slot is skipped or collected by scenario instead of `slot_id`; any scheduled
  slot fails both attempts; proof collection is incomplete; any successful slot lacks
  `eval.json`, `output.txt`, `episode_meta.json`, or `sentinel_iter48_decisions.jsonl`; the
  released-union patch marker is missing from a successful slot; the top-level
  `collision_provenance` key is absent from any successful slot's `eval.json`; the launcher does
  not emit the final done marker; or the heavy-artifact manifest is missing.
- `HUGSIM_SUPPORT_CORE_BATCH_EXECUTION_COMPLETE`: all hard gates pass, exactly `8/8` registered
  slot ids complete successfully, exactly `8/8` successful slots have complete proof artifacts,
  exactly `8/8` successful `eval.json` files expose the top-level `collision_provenance` key,
  the collected slot ids exactly equal the manifest slot ids in order, and the three duplicate
  scenario groups remain represented as distinct slot directories.

The result may report descriptive counts such as completed slots, failed attempts, HD-Score
presence, collision-provenance row counts, and disk use. It may not classify actor matches or
claim a repair.

## Required proof artifacts

- launcher and analyzer source plus unit tests;
- box launch command receipt;
- `proof-execution/receipts.json`;
- `proof-execution/frozen_manifest.sha256`;
- `proof-execution/frozen_scenarios_iter112.sha256`;
- `proof-execution/i112-support-core-batch-run.log`;
- per-slot `eval.json`, `output.txt`, `episode_meta.json`, and
  `sentinel_iter48_decisions.jsonl`;
- `proof-execution/support_core_batch_execution_report.json`;
- `proof-execution/support_core_batch_execution.md`;
- `proof-execution/analyze_support_core_batch_execution.command.txt`;
- `proof-execution/heavy_manifest_iter112.txt` if heavy on-box artifacts are not copied.

## Protocol

1. Commit this `HYPOTHESIS.md` alone.
2. Add launcher/analyzer/tests; run targeted lint/tests and `python3 scripts/validate_docs.py`.
3. Copy the launcher, manifest, and byte-bound patch artifacts to the GPU box.
4. Launch exactly the registered `8`-slot ON batch, detached, only if the box is idle.
5. Monitor the log until the first slot starts and patch markers print.
6. On done marker: collect proof, commit proof first, run analyzer once, publish `RESULT.md`,
   update docs/handoff, run `ruff check .`, `pytest -q`, and `python3 scripts/validate_docs.py`,
   then push.

## Forbidden claims

No actor-causality, actor-match interpretation, repair, threshold-value, transfer, safety,
deployment, robustness, benchmark, population-rate, HD-Score-invariance, real-world behavior,
first-responder behavior, acquisition-value, retuning, production, or commercial claim. A complete
batch only proves that the registered slot-level instrumented HUGSIM run executed and produced
the required provenance artifacts.
