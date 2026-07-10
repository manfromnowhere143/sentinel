# Iteration 37 - track-query site intervention pre-registration

Frozen after iteration 36 was published as `BRIDGE_SITE_PASS_SITE_SPECIFIC_PREREG_AUTHORIZED`, and
before any iteration-37 tooling, direction artifact, server patch, feeder, GPU command, gcloud
command, model replay, calibration replay, heldout replay, iteration-12 scoring, selector
evaluation, or closed-loop work.

Iterations 33-35 closed the tested global bridge-centroid direction and simple baseline-geometry
row conditioning. Iteration 36 changed the target-site question and found that `track_query` is the
strongest pre-declared diagnostic site: AUROC `0.970531`, AP `0.726416`, and scene-bootstrap AUROC
p05 `0.950589`. Iteration 37 is the next causal test authorized by that diagnostic result. It is
not an iteration-12, selector, NeuroNCAP, or closed-loop experiment.

## Research question

Using a fit-only centroid direction on `sdc_track_query` alone, and the prefix-preserving replay
form that restored alpha-zero parity in iteration 32 and passed S0 in iteration 33, does a
track-query-only intervention causally increase downstream command-candidate diversity on heldout
`eligible_lowdiv` full-trainval frames while preserving heldout `benign_control` frames?

Acceptable positive claim if every bar passes:

> Under the frozen prefix-preserving track-query intervention, changing `sdc_track_query` before
> the planning head changes downstream candidate geometry on heldout full-trainval
> `eligible_lowdiv` target rows while passing registered benign controls.

Forbidden claims, even on a pass:

- no claim that the track query is the only cause of low diversity;
- no claim that the intervention recovers a human-legible or executable plan B;
- no iteration-12 dangerous-frame, NeuroNCAP, selector-compatibility, closed-loop, deployment, or
  safety claim;
- no strict-collapse language; iteration 29 failed strict-collapse support;
- no transfer claim to VAD, other UniAD checkpoints, other planners, or other datasets;
- no claim that iterations 33-35 passed; they remain published nulls.

## Frozen input artifacts

Iteration 37 may read only these committed artifacts before its own proof artifacts are written:

- `experiments/iter29_trainval_risk_support_atlas/proof-full-extract/sentinel_e29_stage1.jsonl.gz.part-*`;
- `experiments/iter29_trainval_risk_support_atlas/proof-full-extract/sentinel_e29_stage1_gt.jsonl.gz`;
- `experiments/iter29_trainval_risk_support_atlas/proof-full-extract/s0_integrity_report.json`;
- `experiments/iter29_trainval_risk_support_atlas/proof-full-extract/label_atlas_report.json`;
- `experiments/iter29_trainval_risk_support_atlas/proof-full-extract/sha256s.txt`;
- `experiments/iter29_trainval_risk_support_atlas/RESULT.md`;
- `experiments/iter30_full_trainval_lowdiv_localization/RESULT.md`;
- `experiments/iter32_prefix_replay_baseline_recovery/RESULT.md`;
- `experiments/iter32_prefix_replay_baseline_recovery/proof-prefix/baseline_recovery_report.json`;
- `experiments/iter33_prefix_preserving_bridge_intervention/RESULT.md`;
- `experiments/iter33_prefix_preserving_bridge_intervention/proof-prefix/prefix_manifest_canary.json`;
- `experiments/iter33_prefix_preserving_bridge_intervention/proof-prefix/prefix_manifest_calibration.json`;
- `experiments/iter33_prefix_preserving_bridge_intervention/proof-prefix/prefix_manifest_heldout.json`;
- `experiments/iter33_prefix_preserving_bridge_intervention/proof-canary/canary_report.json`;
- `experiments/iter36_bridge_site_decomposition/RESULT.md`;
- `experiments/iter36_bridge_site_decomposition/proof-audit/bridge_site_decomposition_report.json`.

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

Expected prefix-expanded replay counts are inherited from the committed iteration-33 manifests:

| split | scenes | prefix replay rows | target rows | context-only rows |
|---|---:|---:|---:|---:|
| canary | `3` | `44` | `12` | `32` |
| calibration | `121` | `4293` | `2452` | `1841` |
| heldout | `122` | `4283` | `2403` | `1880` |

If any count differs, publish an infrastructure null before GPU replay.

## Frozen direction

The direction is derived once from fit-split primary-task rows, using only `sdc_track_query`:

1. Build each raw vector as `flatten(sdc_track_query)`.
2. Fit per-feature mean and standard deviation on all fit-split primary-task rows only.
3. Drop only fit-constant dimensions with standard deviation `<= 1e-12`.
4. Standardize fit vectors with the fit-only statistics.
5. Compute standardized class centroids:
   - `mu_pos_std`: mean standardized vector over fit `eligible_lowdiv` rows;
   - `mu_benign_std`: mean standardized vector over fit `benign_control` rows.
6. Define the repair direction in standardized feature space:
   `d_std = mu_benign_std - mu_pos_std`.
7. Convert to raw tensor units for nonconstant dimensions:
   `d_raw = d_std * fit_std`.
8. Fill dropped dimensions with `0.0`.

No logistic-regression coefficient, heldout score, heldout label, metadata feature, ego-plan
feature, candidate-geometry feature, iteration-12 row, or iteration-37 replay output may enter the
direction.

The direction builder must write `proof-direction/track_query_direction.json` before any GPU
replay. That file must include fit row counts, feature count `256`, dropped-dimension count, raw
and standardized L2 norms, and SHA256 over the ordered raw direction plus fit statistics. If the
direction artifact cannot be reproduced byte-identically from committed inputs, publish an
infrastructure null and stop.

## Frozen replay and intervention form

For every run, replay each scene from sample index `0` through the largest target index for that
scene, in scene/sample order. Every row must be logged and marked `target_row=true` or
`target_row=false`.

Context-only prefix rows:

- must be served before target rows to restore runner/input state;
- must always use alpha `0.00`;
- must not receive the intervention;
- must not enter calibration or heldout pass/fail metrics.

Target rows:

- receive the run's global alpha;
- are the only rows used for target parity, calibration, and heldout metrics.

Hook site:

- immediately after `outs_motion["sdc_track_query"]` is available;
- immediately before every `self.model.planning_head.forward(...)` call used for the executed
  command and the three command-conditioned candidate sweeps.

Patch form on target rows:

- let `x_raw` be `flatten(sdc_track_query)`;
- for global alpha `a`, compute `x_intervened = x_raw + a * d_raw`;
- write `x_intervened` back to `sdc_track_query` with shape `[1, 256]`;
- leave `sdc_traj_query` unchanged;
- all other model weights, tensors, planner code paths, detector thresholds, and scenario inputs
  remain unchanged.

Frozen alpha grid:

```text
alpha in {0.00, 0.25, 0.50, 0.75, 1.00}
```

Alpha is global. No per-scene, per-frame, per-class, or per-row alpha is allowed. Alpha `0.00` is
the sham/baseline cell and is not selectable as the final intervention.

## S0 - offline direction, manifest, and canary integrity

Before any calibration grid:

- iteration-29 extraction and GT hashes must match the committed proof table;
- iteration-29 S0 and label-atlas reports must still pass exactly as published;
- iteration-30 result status must be `LOCALIZATION_PASS_SUCCESSOR_PREREG_AUTHORIZED`;
- iteration-32 result status must be `BASELINE_RECOVERY_PASS_S1_PREFIX_REPLAY`;
- iteration-33 canary report must have passed S0 for prefix replay;
- iteration-36 result status must be `BRIDGE_SITE_PASS_SITE_SPECIFIC_PREREG_AUTHORIZED`;
- iteration-36 must list `track_query` as a passing site;
- the track-query direction artifact must be reproducible from committed inputs;
- prefix manifests must match the frozen canary/calibration/heldout count table above;
- the server patch must log:
  - exact source-tree commit or patch hash;
  - direction SHA256;
  - split and alpha;
  - `target_row`;
  - whether intervention was applied;
  - original and intervened track-query SHA256 for target rows;
  - original and intervened bridge SHA256 for target rows;
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
- alpha `0.50` target rows must record `intervention_applied=true` and changed track-query
  SHA256s for all `12` target rows;
- alpha `0.50` target rows must record unchanged `sdc_traj_query_last` SHA256s for all `12`
  target rows;
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

- **Input integrity failure.** Iter29, Iter30, Iter32, Iter33, or Iter36 artifacts are missing,
  invalid, or do not match committed hashes/counts/statuses.
- **Direction instability.** The fit-only track-query centroid direction cannot be reproduced
  byte-identically before replay.
- **Replay instability.** Alpha-zero prefix replay fails the frozen iteration-32 target hashes or
  coordinate tolerance.
- **Wrong-site mutation.** Nonzero-alpha canary changes `sdc_traj_query_last` on target rows.
- **No target response.** Calibration cannot find a nonzero alpha that moves eligible-lowdiv
  candidate spread enough while maintaining best-candidate gap.
- **Benign harm.** Any selected alpha exceeds benign displacement, danger-crossing, or
  low-diversity-collapse bars.
- **Heldout failure.** The selected alpha fails heldout target response or benign-control bars.
- **Leakage.** Any iteration-12 frame, selector outcome, closed-loop log, uncommitted model log,
  post-hoc alpha, or altered site slice is used.
- **Overclaim.** RESULT language treats this as NeuroNCAP, selector, deployment, closed-loop, or
  safety evidence.

## Required proof artifacts

If run, the RESULT must commit:

- exact command lines;
- direction builder, server patch, feeder, run scripts, analyzer source, and tests;
- `proof-direction/track_query_direction.json`;
- S0 canary JSONL logs, GT logs, hashes, and canary report;
- calibration report and all grid-cell metrics if S0 passes;
- heldout report if calibration selects an alpha;
- `proof-*/local_verification.txt`;
- claim-boundary paragraph before interpretation.

## Protocol

1. Commit this `HYPOTHESIS.md` before writing or running iteration-37 tooling.
2. Commit tooling and tests before producing direction or replay artifacts.
3. Build and commit the track-query direction artifact before any GPU replay.
4. Run S0 canary only after the direction artifact is committed and the GPU box is confirmed idle.
5. Commit and publish S0 at full weight if it fails; if S0 passes, only then may calibration be
   considered.
6. A heldout replay, iteration-12 scoring, selector evaluation, closed-loop work, deployment
   language, or safety claim is prohibited unless every prior registered gate authorizes it.
