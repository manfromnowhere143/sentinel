# Iteration 103 - HUGSIM provenance batch execution

Frozen before any iteration-103 launcher, analyzer, GPU command, simulator launch, proof artifact,
result, or claim. This is the separately registered execution step for the iteration-102
slot-level manifest. It is not an actor-match interpretation, not a repair, not a threshold
change, and not a safety result.

## Context

Iteration 100 proved that existing committed reports cannot expand the fixed five-row structural
bridge map because the collision side lacks actor/provenance support. Iteration 101 froze a
13-row candidate schedule. Iteration 102 converted that schedule into a launch-ready manifest
with `13` execution slots, `9` unique scenarios, `4` duplicate scenario groups, and a hard rule
that `slot_id` is the primary execution key.

This iteration asks only whether the registered 13-slot batch can be executed under the same
byte-bound HUGSIM provenance instrumentation and released-union monitor patch used in iteration
59, while preserving slot identity. It does not interpret the resulting collision actors.

## Frozen manifest

- Manifest path:
  `experiments/iter102_hugsim_provenance_batch_launch_manifest/proof-launch-manifest/provenance_batch_launch_manifest.json`
- Manifest SHA256:
  `ddbc9960fe0b50b95842bd2c8b2e26b5e7ed00abba65f8f97b5ed6515c428870`
- Manifest report SHA256:
  `081244471a47bb52ae785ac90935206a9b4609df77dc96bc9f4ada0cea3ebb05`
- Manifest verdict required:
  `HUGSIM_PROVENANCE_BATCH_LAUNCH_MANIFEST_COMPLETE`

## Frozen schedule

Exactly 13 ON slots, in this order:

| slot | slot id | scenario | run | scenario SHA256 |
|---:|---|---|---:|---|
| 1 | `i102_s01_iter48_easy_medium_no_fire_scene_0013_easy_00_r1` | `scene-0013-easy-00` | 1 | `22d30c2a3dadf59451ff3704b50c412fb6fa74d261ee96dd4e6bf17c9a064735` |
| 2 | `i102_s02_iter48_easy_medium_no_fire_scene_0013_easy_00_r2` | `scene-0013-easy-00` | 2 | `22d30c2a3dadf59451ff3704b50c412fb6fa74d261ee96dd4e6bf17c9a064735` |
| 3 | `i102_s03_iter48_easy_medium_unique_cpa_object_scene_0038_medium_01_r1` | `scene-0038-medium-01` | 1 | `cbc56796e802e964bca700662f34c77fb2500ee8ee32225820276521d4a230e2` |
| 4 | `i102_s04_iter48_easy_medium_unique_cpa_object_scene_0062_medium_00_r2` | `scene-0062-medium-00` | 2 | `8ab4eaa941cf292710701f1a8e0d791ee81fede1874c985d0bf126951018e2ae` |
| 5 | `i102_s05_iter48_easy_medium_unique_ttc_object_scene_0051_easy_00_r1` | `scene-0051-easy-00` | 1 | `48ed82b0b0700803e77940fbfd401b34fe2f40d5d5d1f7deaa2e23053c3990f1` |
| 6 | `i102_s06_iter48_easy_medium_unique_ttc_object_scene_0051_easy_00_r2` | `scene-0051-easy-00` | 2 | `48ed82b0b0700803e77940fbfd401b34fe2f40d5d5d1f7deaa2e23053c3990f1` |
| 7 | `i102_s07_iter49_hard_extreme_no_fire_scene_0041_extreme_00_r2` | `scene-0041-extreme-00` | 2 | `7d186ac9491de1cc3aab58a3a636ab0eb00088179f68d8a563214aaada3aa8af` |
| 8 | `i102_s08_iter49_hard_extreme_no_fire_scene_0062_hard_00_r1` | `scene-0062-hard-00` | 1 | `a318c5a49a43fc50e66b6b1b73bd53df165cca3c49e409e7b22f65276361e90e` |
| 9 | `i102_s09_iter49_hard_extreme_unique_cpa_object_scene_0013_extreme_00_r1` | `scene-0013-extreme-00` | 1 | `7b4b374bda9c9520114c9fdcb8ce8f3f91686dc9c0caacc261838ae4fe2a3442` |
| 10 | `i102_s10_iter49_hard_extreme_unique_cpa_object_scene_0013_extreme_00_r2` | `scene-0013-extreme-00` | 2 | `7b4b374bda9c9520114c9fdcb8ce8f3f91686dc9c0caacc261838ae4fe2a3442` |
| 11 | `i102_s11_iter49_hard_extreme_unique_ttc_object_scene_0038_hard_00_r1` | `scene-0038-hard-00` | 1 | `5e1dafedccdde485834d5809dee2fcd3cc0b5c31f7315e454d6b4bd8b04b146d` |
| 12 | `i102_s12_iter49_hard_extreme_unique_ttc_object_scene_0038_hard_00_r2` | `scene-0038-hard-00` | 2 | `5e1dafedccdde485834d5809dee2fcd3cc0b5c31f7315e454d6b4bd8b04b146d` |
| 13 | `i102_s13_iter49_hard_extreme_both_distinct_objects_scene_0138_extreme_00_r1` | `scene-0138-extreme-00` | 1 | `d4e83c49e3240c8091294a5b545920f0c6f3b0e3498cb49c8b132e824c7cf1d9` |

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

- `HUGSIM_PROVENANCE_BATCH_EXECUTION_INFRA_NULL`: any hard launch gate fails; the manifest SHA
  check fails; any slot is skipped or collected by scenario instead of `slot_id`; any scheduled
  slot fails both attempts; proof collection is incomplete; any successful slot lacks
  `eval.json`, `output.txt`, `episode_meta.json`, or `sentinel_iter48_decisions.jsonl`; the
  released-union patch marker is missing from a successful slot; the top-level
  `collision_provenance` key is absent from any successful slot's `eval.json`; the launcher does
  not emit the final done marker; or the heavy-artifact manifest is missing.
- `HUGSIM_PROVENANCE_BATCH_EXECUTION_COMPLETE`: all hard gates pass, exactly `13/13` registered
  slot ids complete successfully, exactly `13/13` successful slots have complete proof artifacts,
  exactly `13/13` successful `eval.json` files expose the top-level `collision_provenance` key,
  the collected slot ids exactly equal the manifest slot ids in order, and the duplicate scenario
  groups remain represented as distinct slot directories.

The result may report descriptive counts such as completed slots, failed attempts, HD-Score
presence, collision-provenance row counts, and disk use. It may not classify actor matches or
claim a repair.

## Required proof artifacts

- launcher and analyzer source plus unit tests;
- box launch command receipt;
- `proof-execution/receipts.json`;
- `proof-execution/frozen_manifest.sha256`;
- `proof-execution/frozen_scenarios_iter103.sha256`;
- `proof-execution/i103-provenance-batch-run.log`;
- per-slot `eval.json`, `output.txt`, `episode_meta.json`, and
  `sentinel_iter48_decisions.jsonl`;
- `proof-execution/provenance_batch_execution_report.json`;
- `proof-execution/provenance_batch_execution.md`;
- `proof-execution/analyze_provenance_batch_execution.command.txt`;
- `proof-execution/heavy_manifest_iter103.txt` if heavy on-box artifacts are not copied.

## Protocol

1. Commit this `HYPOTHESIS.md` alone.
2. Add launcher/analyzer/tests; run `ruff check .`, targeted tests, and
   `python3 scripts/validate_docs.py`.
3. Copy the launcher, manifest, and byte-bound patch artifacts to the GPU box.
4. Launch exactly the registered 13-slot ON batch, detached, only if the box is idle.
5. Monitor the log until the first slot starts and patch markers print.
6. On done marker: collect proof, commit proof first, run analyzer once, publish `RESULT.md`,
   update docs/handoff, run `ruff check .`, `pytest -q`, and `python3 scripts/validate_docs.py`,
   then push.

## Forbidden claims

No actor-causality, actor-match interpretation, repair, threshold-value, transfer, safety,
deployment, robustness, benchmark, population-rate, HD-Score-invariance, real-world behavior,
first-responder behavior, acquisition-value, or retuning claim. A complete batch only proves that
the registered slot-level instrumented HUGSIM run executed and produced the required provenance
artifacts.
