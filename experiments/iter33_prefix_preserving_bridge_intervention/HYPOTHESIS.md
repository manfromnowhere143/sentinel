# Iteration 33 - prefix-preserving bridge intervention pre-registration

Frozen before any iteration-33 tooling, analyzer, prefix manifest, GPU command, gcloud command,
model replay, calibration replay, heldout replay, iteration-12 scoring, selector evaluation, or
closed-loop work.

Iteration 31 built a valid fit-only bridge-centroid direction but stopped at S0 because sparse
alpha-zero canary replay did not reproduce the committed iteration-29 baseline. Iteration 32 then
showed the cause was replay form: a no-op prefix-preserving replay of the exact same canary
targets restored iteration-29 model and GT parity exactly. Iteration 33 is the fresh causal test
authorized by that baseline-recovery result.

## Research question

Using the committed iteration-31 bridge-centroid direction and the iteration-32 prefix-preserving
replay form, does a single global intervention on UniAD's
`sdc_traj_query_last || sdc_track_query` bridge tensor causally increase downstream
command-candidate diversity on heldout `eligible_lowdiv` full-trainval frames while preserving
heldout `benign_control` frames?

Acceptable positive claim if every bar passes:

> Under the frozen prefix-preserving bridge-centroid intervention, changing
> `sdc_traj_query_last || sdc_track_query` before the planning head changes downstream candidate
> geometry on heldout full-trainval `eligible_lowdiv` target rows while passing registered benign
> controls.

Forbidden claims, even on a pass:

- no claim that the bridge tensor is the only cause of low diversity;
- no claim that the intervention recovers a human-legible or executable plan B;
- no iteration-12 dangerous-frame, NeuroNCAP, selector-compatibility, closed-loop, deployment, or
  safety claim;
- no strict-collapse language; iteration 29 failed strict-collapse support;
- no transfer claim to VAD, other UniAD checkpoints, other planners, or other datasets;
- no claim that iteration 31 passed; iteration 31 remains an S0 infrastructure null.

## Frozen input artifacts

Iteration 33 may read only these committed artifacts before its own proof artifacts are written:

- `experiments/iter29_trainval_risk_support_atlas/proof-full-extract/sentinel_e29_stage1.jsonl.gz.part-*`;
- `experiments/iter29_trainval_risk_support_atlas/proof-full-extract/sentinel_e29_stage1_gt.jsonl.gz`;
- `experiments/iter29_trainval_risk_support_atlas/proof-full-extract/s0_integrity_report.json`;
- `experiments/iter29_trainval_risk_support_atlas/proof-full-extract/label_atlas_report.json`;
- `experiments/iter29_trainval_risk_support_atlas/proof-full-extract/sha256s.txt`;
- `experiments/iter29_trainval_risk_support_atlas/HYPOTHESIS.md`;
- `experiments/iter29_trainval_risk_support_atlas/RESULT.md`;
- `experiments/iter30_full_trainval_lowdiv_localization/HYPOTHESIS.md`;
- `experiments/iter30_full_trainval_lowdiv_localization/RESULT.md`;
- `experiments/iter30_full_trainval_lowdiv_localization/proof-localization/localization_report.json`;
- `experiments/iter31_full_trainval_bridge_intervention/HYPOTHESIS.md`;
- `experiments/iter31_full_trainval_bridge_intervention/RESULT.md`;
- `experiments/iter31_full_trainval_bridge_intervention/proof-direction/direction.json`;
- `experiments/iter31_full_trainval_bridge_intervention/proof-direction/replay_manifest_canary.json`;
- `experiments/iter31_full_trainval_bridge_intervention/proof-direction/replay_manifest_calibration.json`;
- `experiments/iter31_full_trainval_bridge_intervention/proof-direction/replay_manifest_heldout.json`;
- `experiments/iter32_prefix_replay_baseline_recovery/HYPOTHESIS.md`;
- `experiments/iter32_prefix_replay_baseline_recovery/RESULT.md`;
- `experiments/iter32_prefix_replay_baseline_recovery/proof-prefix/baseline_recovery_report.json`;
- `experiments/iter32_prefix_replay_baseline_recovery/proof-prefix/prefix_manifest.json`.

Iteration-12 frames remain evaluation-only and must not be read, scored, sampled, or used for
debugging. No selector scoring or closed-loop run is authorized.

## Frozen labels and rows

Use the iteration-29 split assignments and primary labels exactly:

- `danger_4p5`: executed-plan closest gap over the immediate first-three-step horizon `< 4.5 m`;
- `safe_6p0`: executed-plan closest gap over the immediate first-three-step horizon `>= 6.0 m`;
- `low_diversity_1p5`: three command-conditioned candidate plans have final-endpoint max pairwise
  spread `<= 1.5 m`;
- `high_diversity_2p0`: final-endpoint max pairwise spread `>= 2.0 m`;
- `eligible_lowdiv`: `danger_4p5` and `low_diversity_1p5`;
- `benign_control`: `safe_6p0` and `high_diversity_2p0`.

Only `eligible_lowdiv` and `benign_control` target rows enter calibration and heldout pass/fail
metrics. Context-only prefix rows restore runner/input state and are audit rows only.

Expected target counts:

| split | eligible_lowdiv targets | benign_control targets | total targets |
|---|---:|---:|---:|
| canary | `6` | `6` | `12` |
| calibration | `108` | `2344` | `2452` |
| heldout | `158` | `2245` | `2403` |

Expected prefix-expanded replay counts derived from the frozen iteration-31 manifests:

| split | scenes | prefix replay rows | target rows | context-only rows |
|---|---:|---:|---:|---:|
| canary | `3` | `44` | `12` | `32` |
| calibration | `121` | `4293` | `2452` | `1841` |
| heldout | `122` | `4283` | `2403` | `1880` |

If any count differs, publish an infrastructure null before GPU replay.

## Frozen direction

Use the committed iteration-31 fit-only bridge-centroid direction exactly:

- path: `experiments/iter31_full_trainval_bridge_intervention/proof-direction/direction.json`;
- feature count: `1792`;
- fit rows: `5211`;
- dropped dimensions: `0`;
- direction SHA: `3ae7cb14ae4b31451bda3a0eebf9ace23a38483489839445b6f8333cc2f8d794`.

The iteration-33 tooling must verify the direction artifact and write a proof copy or receipt
before GPU replay. No logistic-regression coefficient, heldout score, heldout label, metadata
feature, ego-plan feature, candidate-geometry feature, iteration-12 row, or iteration-33 replay
output may alter the direction.

## Frozen replay and intervention form

For every run, replay each scene from sample index `0` through the largest target index for that
scene, in scene/sample order. Every row must be logged and marked `target_row=true` or
`target_row=false`.

Context-only prefix rows:

- must be served before target rows to restore runner/input state;
- must always use alpha `0.00`;
- must not receive the bridge intervention;
- must not enter calibration or heldout pass/fail metrics.

Target rows:

- receive the run's global alpha;
- are the only rows used for target parity, calibration, and heldout metrics.

Hook site:

- immediately after `outs_motion["sdc_traj_query"]` and `outs_motion["sdc_track_query"]` are
  available;
- immediately before every `self.model.planning_head.forward(...)` call used for the executed
  command and the three command-conditioned candidate sweeps.

Patch form on target rows:

- let `x_raw` be `flatten(sdc_traj_query[-1]) || flatten(sdc_track_query)` in the same order as
  the direction artifact;
- for global alpha `a`, compute `x_intervened = x_raw + a * d_raw`;
- write the first `1536` values back to `sdc_traj_query[-1]` with shape `[1, 6, 256]`;
- write the final `256` values back to `sdc_track_query` with shape `[1, 256]`;
- all other model weights, tensors, planner code paths, detector thresholds, and scenario inputs
  remain unchanged.

Frozen alpha grid:

```text
alpha in {0.00, 0.25, 0.50, 0.75, 1.00}
```

Alpha is global. No per-scene, per-frame, per-class, or per-row alpha is allowed. Alpha `0.00` is
the sham/baseline cell and is not selectable as the final intervention.

## S0 - offline manifest, direction, and canary integrity

Before any calibration grid:

- iteration-29 extraction and GT hashes must match the committed proof table;
- iteration-29 S0 and label-atlas reports must still pass exactly as published;
- iteration-30 result status must be `LOCALIZATION_PASS_SUCCESSOR_PREREG_AUTHORIZED`;
- iteration-31 direction SHA and row counts must match this pre-registration;
- iteration-32 result status must be `BASELINE_RECOVERY_PASS_S1_PREFIX_REPLAY`;
- prefix manifests must match the frozen canary/calibration/heldout count table above;
- the server patch must log:
  - exact source-tree commit or patch hash;
  - direction SHA256;
  - split and alpha;
  - `target_row`;
  - whether intervention was applied;
  - original and intervened bridge-vector SHA256 for target rows;
  - original and intervened command-candidate trajectories for target rows;
  - original and intervened executed trajectory for target rows.

Canary:

- use the exact frozen canary prefix manifest: `44` prefix replay rows, `12` target rows;
- run twice at `alpha=0.00` and twice at `alpha=0.50`;
- each run must log exactly `44` non-reset rows and `12` target rows;
- alpha `0.00` target canonical hash must match the iteration-32 model target hash
  `2495f9a1dc4d7f7544673cd4dc25c1283977087a0018b37e76184a2b3c0b611e`;
- alpha `0.00` GT target canonical hash must match the iteration-32 GT target hash
  `5064a3177c7918712fa56533b897e50a7d731f516d17a9ca6241ef67296050c7`;
- alpha `0.00` target trajectories, candidates, object tracks, forecasts, and bridge tensors must
  match iteration-29 originals within max absolute tolerance `1e-5`;
- alpha `0.50` target canonical hashes must match across repeats;
- alpha `0.50` target rows must record `intervention_applied=true` and changed bridge-vector
  SHA256s for all `12` target rows;
- duplicate, missing, or unexpected target keys must be `0`.

If any S0 bar fails, publish an infrastructure null and stop before calibration-grid replay.

## S1 - calibration alpha selection

Run exactly one calibration prefix replay for every alpha in the frozen grid. Each alpha run must
serve exactly `4293` prefix replay rows and log exactly `2452` target rows. Metrics are computed
only on target rows:

- `108` calibration `eligible_lowdiv` target rows;
- `2344` calibration `benign_control` target rows.

For each alpha, compute:

- endpoint spread for the three command candidates;
- best candidate closest gap: max closest gap across the three command candidates;
- executed-plan closest gap;
- executed-plan final-endpoint displacement from alpha `0.00`;
- whether a benign target row crosses the frozen `danger_4p5` threshold after intervention;
- whether a benign target row collapses from `high_diversity_2p0` to `low_diversity_1p5`;
- gross validity: every logged target trajectory coordinate finite, max absolute coordinate
  `<= 100 m`, and max per-step displacement `<= 20 m`.

A nonzero alpha is calibration-eligible only if all bars pass:

- error target rows `0`;
- gross-validity failures `0`;
- on calibration `eligible_lowdiv`, median endpoint-spread delta `> 0.25 m`;
- on calibration `eligible_lowdiv`, at least `50%` of rows have endpoint-spread delta `> 0.25 m`;
- on calibration `eligible_lowdiv`, median best-candidate-gap delta `>= 0.00 m`;
- on calibration `benign_control`, median executed final-endpoint displacement `<= 0.50 m`;
- on calibration `benign_control`, 95th percentile executed final-endpoint displacement
  `<= 2.00 m`;
- on calibration `benign_control`, no more than `5%` cross into `danger_4p5`;
- on calibration `benign_control`, no more than `5%` collapse into `low_diversity_1p5`;
- on calibration `benign_control`, median endpoint-spread delta `>= -0.25 m`.

Select the eligible nonzero alpha with the largest calibration median endpoint-spread delta on
`eligible_lowdiv`. Ties choose the smallest alpha. If no nonzero alpha is eligible, publish a
calibration null and stop before heldout replay.

All grid-cell metrics, including failed cells, must be committed.

## S2 - heldout causal geometry bars

Run the selected alpha exactly once on the heldout prefix manifest. The run must serve exactly
`4283` prefix replay rows and log exactly `2403` target rows. Metrics are computed only on target
rows:

- `158` heldout `eligible_lowdiv` target rows;
- `2245` heldout `benign_control` target rows.

Heldout `eligible_lowdiv` bars:

- error target rows `0`;
- gross-validity failures `0`;
- median endpoint-spread delta `>= 0.50 m`;
- at least `60%` of rows have endpoint-spread delta `>= 0.25 m`;
- median best-candidate-gap delta `>= 0.10 m`;
- no more than `25%` of rows have best-candidate-gap delta `< -0.25 m`.

If any heldout `eligible_lowdiv` bar fails, publish a diagnostic-but-not-causal null and stop.

## S3 - heldout benign-control bars

Heldout `benign_control` bars:

- error target rows `0`;
- gross-validity failures `0`;
- median executed final-endpoint displacement `<= 0.50 m`;
- 95th percentile executed final-endpoint displacement `<= 2.00 m`;
- no more than `5%` cross into `danger_4p5`;
- no more than `5%` collapse into `low_diversity_1p5`;
- median endpoint-spread delta `>= -0.25 m`.

If any S3 bar fails, publish a causal-but-unsafe-or-nonspecific null and stop.

## Named falsifiers

- **Input integrity failure.** Iter29, iter30, iter31, or iter32 prerequisite artifacts are
  missing, invalid, or do not match committed hashes/counts.
- **Prefix manifest drift.** Any target key, prefix count, scene count, or context-only count
  differs from the frozen tables.
- **Direction drift.** The committed iteration-31 direction SHA or feature layout does not match
  this pre-registration.
- **Patch nondeterminism.** Canary repeated hashes differ, or alpha `0.00` fails to reproduce
  iteration-29/iteration-32 target outputs.
- **Context contamination.** Any context-only prefix row receives a nonzero-alpha intervention or
  enters pass/fail metrics.
- **No usable alpha.** No nonzero calibration alpha passes the frozen grid bars.
- **Diagnostic but not causal.** Heldout `eligible_lowdiv` candidate geometry does not move by the
  frozen S2 bars.
- **Causal but risk-worsening.** Candidate spread increases while best-candidate gap worsens beyond
  the frozen S2 limit.
- **Benign harm.** Heldout benign controls move, become dangerous, or collapse beyond S3 bars.
- **Nonspecific corruption.** The patch creates nonfinite or gross-invalid target trajectories.
- **Leakage.** Any iteration-12 frame, selector outcome, heldout tuning, per-frame alpha,
  unregistered feature, or post-hoc grid expansion is used.
- **Overclaim attempt.** RESULT language treats this as closed-loop safety, plan-B recovery, or a
  global mechanism proof.

## Required proof artifacts

If run, the RESULT must commit:

- exact command lines;
- prefix manifest builder source and all split manifests;
- direction receipt or proof copy with SHA256;
- server patch, feeder, analyzer, run scripts, and tests;
- canary logs, GT sidecars, target canonical hashes, and alpha-zero parity report;
- calibration grid per-row and per-cell metrics for every alpha, including failed cells;
- selected-alpha decision record with tie handling;
- heldout per-row metrics and aggregate S2/S3 report;
- row counts by split and class, including context-only rows and ambiguous rows;
- local verification output for `ruff check .`, `pytest -q`, and
  `python3 scripts/validate_docs.py`;
- claim-boundary paragraph before interpretation.

Any gzip proof artifact over `90 MB` must be split into `.part-*` files before commit.

## Protocol

1. Commit this `HYPOTHESIS.md` before writing iteration-33 tooling or running any intervention.
2. Commit the prefix manifest builder, server patch, feeder, analyzer, run scripts, and tests
   before any GPU replay.
3. Run S0 offline checks and canary first. Stop on any S0 failure.
4. Run the calibration grid once. Stop if no alpha is eligible.
5. Run heldout once with the selected alpha. Do not rerun with changed bars, labels, alphas, or
   patch form.
6. Publish `RESULT.md` at full weight whether the result passes or fails.
7. A pass authorizes only a separate Stage-2 pre-registration for iteration-12 or selector
   evaluation. It does not authorize iteration-12 scoring, selector evaluation, closed-loop work,
   deployment language, or a safety claim.
