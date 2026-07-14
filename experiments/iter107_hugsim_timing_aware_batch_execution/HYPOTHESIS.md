# Iteration 107 - HUGSIM timing-aware provenance batch execution

Frozen before any iteration-107 launcher, analyzer, GPU command, simulator launch, proof artifact,
result, handoff update, or claim. This is the separately registered execution step for the
iteration-106 timing-aware slot-level manifest. It is not an actor-match interpretation, not a
repair, not a threshold change, and not a safety result.

## Context

Iteration 104 showed that the first provenance batch executed correctly but had weak actor-match
support: only `1/13` slots was foreground-classifiable. Iteration 105 redesigned the candidate
schedule around rows where the released union fired at or before first ON collision time.
Iteration 106 converted that schedule into a launch-ready offline manifest with `13` execution
slots, `11` unique scenarios, `2` duplicate scenario groups, and `13/13` scenario-SHA-bound slots.

This iteration asks only whether the registered timing-aware batch can be executed under the same
byte-bound HUGSIM provenance instrumentation and released-union monitor patch used in iteration
59 and iteration 103, while preserving slot identity. It does not interpret the resulting
collision actors.

## Frozen manifest

- Manifest path:
  `experiments/iter106_hugsim_timing_aware_launch_manifest/proof-launch-manifest/timing_aware_launch_manifest.json`
- Manifest SHA256:
  `19d336364ab46f9e2e6bc881ffe4c7bad354471a851195b8609797d42e735f5a`
- Manifest report SHA256:
  `0d8965da55a0d46366bd464203a00e672b2ed45e02ea0909835a9a152c14a69a`
- Manifest verdict required:
  `HUGSIM_TIMING_AWARE_LAUNCH_MANIFEST_COMPLETE`

## Frozen schedule

Exactly 13 ON slots, in this order:

| slot | slot id | scenario | run | scenario SHA256 |
|---:|---|---|---:|---|
| 1 | `i106_s01_iter48_easy_medium_long_lead_fire_ttc_only_scene_0138_medium_01_r1` | `scene-0138-medium-01` | 1 | `69e97a6c983982365b4336e95d2b48570729ab92984ebaa63b5e644118505f9a` |
| 2 | `i106_s02_iter49_hard_extreme_long_lead_fire_cpa_only_scene_0064_hard_00_r2` | `scene-0064-hard-00` | 2 | `2acfe05ed22c4c287daf74dabbbb6ef61d130bd9351088fb1be40b9270d6516e` |
| 3 | `i106_s03_iter48_easy_medium_long_lead_fire_cpa_only_scene_0166_easy_00_r2` | `scene-0166-easy-00` | 2 | `c83e3968a727d199c91dfda0987431fc943e47ca238d2a47f91ef7fc903bfb39` |
| 4 | `i106_s04_iter48_easy_medium_long_lead_fire_ttc_only_scene_0138_medium_01_r2` | `scene-0138-medium-01` | 2 | `69e97a6c983982365b4336e95d2b48570729ab92984ebaa63b5e644118505f9a` |
| 5 | `i106_s05_iter48_easy_medium_long_lead_fire_cpa_only_scene_0064_easy_00_r2` | `scene-0064-easy-00` | 2 | `b7665e1495ffe4fa045af495a44defe247e5497cb8d79330e5f054de86898392` |
| 6 | `i106_s06_iter48_easy_medium_long_lead_fire_cpa_only_scene_0166_medium_01_r2` | `scene-0166-medium-01` | 2 | `fa7d9c8912cf4ea62aa9c2498de516f048742cb93e903b59f0f7d6580138d30b` |
| 7 | `i106_s07_iter49_hard_extreme_long_lead_fire_cpa_only_scene_0064_hard_00_r1` | `scene-0064-hard-00` | 1 | `2acfe05ed22c4c287daf74dabbbb6ef61d130bd9351088fb1be40b9270d6516e` |
| 8 | `i106_s08_iter49_hard_extreme_long_lead_fire_ttc_only_scene_0411_extreme_00_r1` | `scene-0411-extreme-00` | 1 | `cd9c86bd4dbad2e6ff74f275f9fe43ad60aa0d9bf314971473ae2ddb01b703fb` |
| 9 | `i106_s09_iter48_easy_medium_long_lead_fire_ttc_only_scene_0071_easy_00_r2` | `scene-0071-easy-00` | 2 | `f04f159365d966c3bacf326375eb67463cf2614b85b9343eff2adec84d640750` |
| 10 | `i106_s10_iter49_hard_extreme_short_lead_fire_ttc_only_scene_0411_hard_00_r2` | `scene-0411-hard-00` | 2 | `9f38bbdcdc49fe6ac5274a967b9a209417d621f67060357b97deacb887cf67a9` |
| 11 | `i106_s11_iter49_hard_extreme_long_lead_fire_cpa_only_scene_0138_hard_00_r1` | `scene-0138-hard-00` | 1 | `8d0e3ec0d0068ae51047c0f3d2d63995d3a9dfeb60dc4071d7ec017d869fed2e` |
| 12 | `i106_s12_iter49_hard_extreme_long_lead_fire_cpa_only_scene_0071_extreme_00_r1` | `scene-0071-extreme-00` | 1 | `97b55b931c7ac5bf5991b1b0ba46907468dc4c6c8a3108df5b2dddbcf43ab0ed` |
| 13 | `i106_s13_iter48_easy_medium_long_lead_fire_cpa_only_scene_0064_medium_01_r1` | `scene-0064-medium-01` | 1 | `e8a5c2d53b016257f7c1e0758137395c72ff7d36de368af8937ff7d2249efd98` |

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

- `HUGSIM_TIMING_AWARE_BATCH_EXECUTION_INFRA_NULL`: any hard launch gate fails; the manifest SHA
  check fails; any slot is skipped or collected by scenario instead of `slot_id`; any scheduled
  slot fails both attempts; proof collection is incomplete; any successful slot lacks
  `eval.json`, `output.txt`, `episode_meta.json`, or `sentinel_iter48_decisions.jsonl`; the
  released-union patch marker is missing from a successful slot; the top-level
  `collision_provenance` key is absent from any successful slot's `eval.json`; the launcher does
  not emit the final done marker; or the heavy-artifact manifest is missing.
- `HUGSIM_TIMING_AWARE_BATCH_EXECUTION_COMPLETE`: all hard gates pass, exactly `13/13` registered
  slot ids complete successfully, exactly `13/13` successful slots have complete proof artifacts,
  exactly `13/13` successful `eval.json` files expose the top-level `collision_provenance` key,
  the collected slot ids exactly equal the manifest slot ids in order, and the two duplicate
  scenario groups remain represented as distinct slot directories.

The result may report descriptive counts such as completed slots, failed attempts, HD-Score
presence, collision-provenance row counts, and disk use. It may not classify actor matches or
claim a repair.

## Required proof artifacts

- launcher and analyzer source plus unit tests;
- box launch command receipt;
- `proof-execution/receipts.json`;
- `proof-execution/frozen_manifest.sha256`;
- `proof-execution/frozen_scenarios_iter107.sha256`;
- `proof-execution/i107-timing-aware-batch-run.log`;
- per-slot `eval.json`, `output.txt`, `episode_meta.json`, and
  `sentinel_iter48_decisions.jsonl`;
- `proof-execution/timing_aware_batch_execution_report.json`;
- `proof-execution/timing_aware_batch_execution.md`;
- `proof-execution/analyze_timing_aware_batch_execution.command.txt`;
- `proof-execution/heavy_manifest_iter107.txt` if heavy on-box artifacts are not copied.

## Protocol

1. Commit this `HYPOTHESIS.md` alone.
2. Add launcher/analyzer/tests; run targeted lint/tests and `python3 scripts/validate_docs.py`.
3. Copy the launcher, manifest, and byte-bound patch artifacts to the GPU box.
4. Launch exactly the registered 13-slot ON batch, detached, only if the box is idle.
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
