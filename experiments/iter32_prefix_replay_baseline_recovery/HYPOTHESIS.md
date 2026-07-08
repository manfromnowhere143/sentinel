# Iteration 32 - prefix replay baseline-recovery pre-registration

Frozen before any iteration-32 tooling, analyzer, prefix manifest, GPU command, gcloud command,
model replay, calibration replay, heldout replay, iteration-12 scoring, selector evaluation, or
closed-loop work.

Iteration 31 stopped at S0 because the alpha `0.00` canary was deterministic but did not reproduce
the committed iteration-29 trajectories/candidates. A narrow source inspection identifies a
plausible infrastructure cause: iteration 31 replayed only sparse target rows, while iteration 29
had advanced each scene through preceding keyframes before logging the same target rows. The runner
state and feeder-emulated CAN bus can therefore differ even when no bridge intervention is applied.

## Research question

Can a prefix-preserving no-op replay of the exact iteration-31 canary target rows reproduce the
committed iteration-29 baseline trajectories, command candidates, and bridge tensors?

The only acceptable positive claim is:

> Replaying each canary scene from sample index `0` through the last target index, while logging
> only the frozen target rows, restores iteration-29 baseline parity for the registered canary
> targets.

Forbidden claims, even on a pass:

- no claim that the bridge-centroid intervention works;
- no claim that any nonzero alpha is safe or useful;
- no calibration, heldout, iteration-12, selector, or closed-loop claim;
- no claim about closed-loop safety, plan-B recovery, or deployment performance;
- no resurrection of iteration 31's failed pre-registration.

## Frozen inputs

Iteration 32 may read only committed artifacts and source files:

- `experiments/iter29_trainval_risk_support_atlas/proof-full-extract/sentinel_e29_stage1.jsonl.gz.part-*`;
- `experiments/iter29_trainval_risk_support_atlas/proof-full-extract/sentinel_e29_stage1_gt.jsonl.gz`;
- `experiments/iter29_trainval_risk_support_atlas/proof-full-extract/s0_integrity_report.json`;
- `experiments/iter29_trainval_risk_support_atlas/proof-full-extract/label_atlas_report.json`;
- `experiments/iter29_trainval_risk_support_atlas/proof-full-extract/sha256s.txt`;
- `experiments/iter29_trainval_risk_support_atlas/server_patch_stage1.py`;
- `experiments/iter29_trainval_risk_support_atlas/feeder_stage1.py`;
- `experiments/iter31_full_trainval_bridge_intervention/proof-direction/replay_manifest_canary.json`;
- `experiments/iter31_full_trainval_bridge_intervention/proof-canary/canary_report.json`;
- `experiments/iter31_full_trainval_bridge_intervention/RESULT.md`.

No iteration-12 frame, selector outcome, closed-loop log, heldout tuning signal, or new label may
enter this experiment.

## Frozen target and prefix rows

Targets are exactly the committed iteration-31 canary rows. The prefix replay must serve every
keyframe from sample index `0` through the largest target index for each scene. Prefix rows exist
only to restore model and input state; pass/fail metrics are computed only on target rows.

| scene | target sample indices | target rows | prefix replay rows | target label family |
|---|---:|---:|---:|---|
| `scene-0252` | `1,2,3,4,5,6` | `6` | `7` | `benign_control` |
| `scene-0258` | `1,3,6,7,8` | `5` | `9` | `eligible_lowdiv` |
| `scene-0261` | `27` | `1` | `28` | `eligible_lowdiv` |
| **total** |  | **`12`** | **`44`** |  |

The prefix manifest must contain exactly `44` replay rows, exactly `12` target rows, and exactly
`32` context-only rows. If any count differs, publish an infrastructure null before GPU replay.

## Frozen replay form

The model patch must be behavior-preserving:

- restore `inference/runner.py` and `inference/server.py` before patching;
- use the same checkpoint/config pair as iteration 29 and 31:
  `projects/configs/stage2_e2e/inference_e2e.py` and `ckpts/uniad_base_e2e.pth`;
- log `traj`, the three command-conditioned `cands`, `objs`, `futs`, scores, and the bridge tensor
  `flatten(sdc_traj_query_last) || flatten(sdc_track_query)` in the same feature order used by
  iterations 29-31;
- apply no bridge direction, no alpha, no tensor mutation, and no extra pre-forward planning-head
  call before the normal executed planning call;
- mark every row as either `target_row=true` or `target_row=false`.

Context-only prefix rows may be logged for audit, but they must not enter target parity metrics.

## S0 - offline manifest and tooling integrity

Before any GPU replay:

- build `proof-prefix/prefix_manifest.json` from the committed iter31 canary manifest only;
- record exact source command lines and SHA256s;
- verify `target_rows=12`, `prefix_replay_rows=44`, and `context_only_rows=32`;
- verify every target key exists exactly once in the committed iteration-29 extraction and GT
  artifacts;
- unit-test split-gzip iter29 reference loading and target filtering.

If any S0 offline bar fails, publish an infrastructure null and stop before GPU replay.

## S1 - no-op prefix replay canary

Run exactly two no-op prefix replays on the GPU. Each run must serve the same `44` prefix manifest
rows in scene/sample order and produce a target-filterable JSONL proof log plus GT sidecar.

Pass bars:

- both runs complete with no error rows;
- each run logs exactly `44` non-reset replay rows and exactly `12` target rows;
- target keys are identical to the frozen target table;
- target canonical JSONL hashes match across the two repeats;
- for all `12` target rows, command and runner timestamp match iteration 29;
- for all `12` target rows, GT `command`, `speed`, `yaw_rate`, `accel`, and `gt_future` match the
  committed iteration-29 GT within max absolute tolerance `1e-9` for scalar/coordinate values;
- for all `12` target rows, `traj`, `cands`, `objs`, `futs`, and bridge tensor values match the
  committed iteration-29 extraction within max absolute coordinate/tensor tolerance `1e-5`;
- duplicate target keys `0`;
- missing iteration-29 references `0`.

If any S1 bar fails, publish an infrastructure null and stop.

## Outcome rule

A pass authorizes only a fresh successor pre-registration for a prefix-preserving bridge
intervention. It does not authorize reusing iteration 31, running calibration, running heldout,
touching iteration-12 frames, scoring selectors, or running closed loop.

A failure closes this baseline-recovery line as an infrastructure null. A later successor would
need a different pre-registered reproduction plan.

## Named falsifiers

- **Manifest drift.** The prefix manifest does not contain exactly the frozen target keys or
  `44` total replay rows.
- **Reference missingness.** Any target key is absent or duplicated in committed iteration-29
  extraction or GT artifacts.
- **Replay nondeterminism.** Target canonical hashes differ across the two no-op prefix repeats.
- **Input-state mismatch.** Target GT command/speed/yaw/accel/future values do not reproduce
  iteration 29.
- **No-op patch mutation.** Target trajectories, command candidates, object tracks, forecasts, or
  bridge tensors do not reproduce iteration 29 within tolerance.
- **Leakage.** Any iteration-12 frame, selector outcome, heldout tuning, per-row alpha, or
  post-hoc target expansion is used.
- **Overclaim.** RESULT language treats a pass as an intervention, selector, closed-loop, or
  safety result.

## Required proof artifacts

If run, the RESULT must commit:

- `proof-prefix/prefix_manifest.json`;
- command lines and SHA256s for generated artifacts;
- no-op server patch, feeder, analyzer, and tests;
- both prefix replay logs and GT sidecars;
- `proof-prefix/baseline_recovery_report.json`;
- exact local verification output for `ruff check .`, `pytest -q`, and
  `python3 scripts/validate_docs.py`;
- claim-boundary paragraph before interpretation.

Any gzip proof artifact over `90 MB` must be split into `.part-*` files before commit.
