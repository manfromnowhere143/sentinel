# Iteration 31 - full-trainval bridge intervention pre-registration

Frozen before any iter31 analyzer, direction artifact, server patch, feeder, extraction script,
activation patching, calibration-grid replay, heldout replay, iteration-12 contact, selector
scoring, closed-loop evaluation, GPU run, or gcloud command.

Iteration 30 passed a diagnostic localization gate: the frozen UniAD motion/planning-bridge
representation `sdc_traj_query_last || sdc_track_query` carries linearly decodable
`eligible_lowdiv` information beyond metadata and ego-plan-kinematic controls. Iteration 31 is the
next Stage-1 causal test. It is not an iteration-12, selector, or closed-loop experiment.

## Research question

Using only the committed iteration-29 split/artifacts and the iteration-30 diagnostic result, does
a single pre-declared intervention that shifts UniAD's motion/planning-bridge tensor toward the
fit-split benign-control centroid causally increase downstream command-candidate diversity on
heldout `eligible_lowdiv` frames while preserving heldout `benign_control` frames?

Acceptable positive claim if every bar passes:

> Under the frozen iter31 bridge-centroid intervention, changing
> `sdc_traj_query_last || sdc_track_query` before the planning head changes downstream candidate
> geometry on heldout full-trainval `eligible_lowdiv` frames while passing registered benign
> controls.

Forbidden claims from this iteration, even on a pass:

- no claim that the bridge tensor is the only cause of low diversity;
- no claim that the intervention recovers a human-legible plan B;
- no iteration-12 dangerous-frame, NeuroNCAP, selector-compatibility, closed-loop, or safety claim;
- no strict-collapse language; iteration 29 failed strict-collapse support;
- no transfer claim to VAD, other UniAD checkpoints, other planners, or other datasets.

## Frozen input artifacts

Iter31 may read only these committed artifacts before its own intervention extraction:

- `experiments/iter29_trainval_risk_support_atlas/proof-full-extract/sentinel_e29_stage1.jsonl.gz.part-*`;
- `experiments/iter29_trainval_risk_support_atlas/proof-full-extract/sentinel_e29_stage1_gt.jsonl.gz`;
- `experiments/iter29_trainval_risk_support_atlas/proof-full-extract/s0_integrity_report.json`;
- `experiments/iter29_trainval_risk_support_atlas/proof-full-extract/label_atlas_report.json`;
- `experiments/iter29_trainval_risk_support_atlas/proof-full-extract/sha256s.txt`;
- `experiments/iter29_trainval_risk_support_atlas/HYPOTHESIS.md`;
- `experiments/iter29_trainval_risk_support_atlas/RESULT.md`;
- `experiments/iter30_full_trainval_lowdiv_localization/HYPOTHESIS.md`;
- `experiments/iter30_full_trainval_lowdiv_localization/RESULT.md`;
- `experiments/iter30_full_trainval_lowdiv_localization/proof-localization/localization_report.json`.

Iteration-12 frames remain evaluation-only and must not be read, scored, sampled, or used for
debugging in this iteration. No selector scoring or closed-loop run is authorized.

## Frozen split and labels

Use the iteration-29 split assignments exactly:

- fit split: derive the bridge-centroid direction only;
- calibration split: choose one global intervention alpha from the frozen grid;
- heldout split: evaluate the chosen alpha once.

Labels are exactly the iteration-29/30 primary labels:

- `danger_4p5`: executed-plan closest gap over the immediate first-three-step horizon `< 4.5 m`;
- `safe_6p0`: executed-plan closest gap over the immediate first-three-step horizon `>= 6.0 m`;
- `low_diversity_1p5`: three command-conditioned candidate plans have final-endpoint max pairwise
  spread `<= 1.5 m`;
- `high_diversity_2p0`: final-endpoint max pairwise spread `>= 2.0 m`;
- `eligible_lowdiv`: `danger_4p5` and `low_diversity_1p5`;
- `benign_control`: `safe_6p0` and `high_diversity_2p0`.

Only `eligible_lowdiv` and `benign_control` rows are used for calibration and heldout gates.
Ambiguous rows may be counted in proof summaries but must not influence alpha selection or heldout
pass/fail.

Expected primary counts, which must reproduce before any intervention:

| label | fit | calibration | heldout |
|---|---:|---:|---:|
| `eligible_lowdiv` | `127` | `108` | `158` |
| `benign_control` | `5084` | `2344` | `2245` |

## Frozen direction

The intervention direction is derived once from fit-split primary-task rows:

1. Build each raw bridge vector exactly as iteration 30 did:
   `flatten(sdc_traj_query_last) || flatten(sdc_track_query)`.
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
feature, candidate-geometry feature, or iteration-12 row may enter the direction.

The direction builder must write `proof-direction/direction.json` before any GPU replay. That file
must include the fit row counts, feature count, dropped-dimension count, direction L2 norms in
standardized and raw units, and SHA256 over the ordered raw direction plus fit statistics. If the
direction artifact cannot be reproduced byte-identically from committed inputs, publish an
infrastructure null and stop.

## Frozen intervention

Hook site:

- immediately after `outs_motion["sdc_traj_query"]` and `outs_motion["sdc_track_query"]` are
  available;
- immediately before every `self.model.planning_head.forward(...)` call used for the executed
  command and the three command-conditioned candidate sweeps.

Patch form:

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

## S0 - artifact, direction, and canary integrity

Before any calibration grid:

- iteration-29 extraction and GT hashes must match the committed proof table;
- iteration-29 S0 and label-atlas reports must still pass exactly as published;
- iteration-30 result status must be `LOCALIZATION_PASS_SUCCESSOR_PREREG_AUTHORIZED`;
- primary counts must exactly match the table above;
- `direction.json` must be reproducible from committed inputs;
- the server patch must log:
  - exact source-tree commit or patch hash;
  - direction SHA256;
  - alpha;
  - whether intervention was applied;
  - original and intervened bridge-vector SHA256 for every nonzero-alpha row;
  - original and intervened command-candidate trajectories;
  - original and intervened executed trajectory.

Canary:

- use the first `6` calibration `eligible_lowdiv` rows and first `6` calibration `benign_control`
  rows after sorting by `(scene, sample_index, timestamp_us)`;
- run the canary twice at `alpha=0.00` and twice at `alpha=0.50`;
- canonical JSONL hashes for each alpha must match across the two repeats;
- `alpha=0.00` candidate and executed trajectories must match iteration-29 originals within
  max absolute coordinate error `<= 1e-5`.

If any S0 bar fails, publish an infrastructure null and stop before calibration-grid replay.

## S1 - calibration alpha selection

Run exactly one calibration replay for every alpha in the frozen grid on all calibration
primary-task rows:

- `108` calibration `eligible_lowdiv` rows;
- `2344` calibration `benign_control` rows.

For each alpha, compute:

- endpoint spread for the three command candidates;
- best candidate closest gap: max closest gap across the three command candidates;
- executed-plan closest gap;
- executed-plan final-endpoint displacement from alpha `0.00`;
- whether a benign row crosses the frozen `danger_4p5` threshold after intervention;
- whether a benign row collapses from `high_diversity_2p0` to `low_diversity_1p5`;
- gross validity: every logged trajectory coordinate finite, max absolute coordinate `<= 100 m`,
  and max per-step displacement `<= 20 m`.

A nonzero alpha is calibration-eligible only if all bars pass:

- error rows `0`;
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

Run the selected alpha exactly once on heldout primary-task rows:

- `158` heldout `eligible_lowdiv` rows;
- `2245` heldout `benign_control` rows.

Heldout `eligible_lowdiv` bars:

- error rows `0`;
- gross-validity failures `0`;
- median endpoint-spread delta `>= 0.50 m`;
- at least `60%` of rows have endpoint-spread delta `>= 0.25 m`;
- median best-candidate-gap delta `>= 0.10 m`;
- no more than `25%` of rows have best-candidate-gap delta `< -0.25 m`.

If any heldout `eligible_lowdiv` bar fails, publish a diagnostic-but-not-causal null and stop.

## S3 - heldout benign-control bars

Heldout `benign_control` bars:

- error rows `0`;
- gross-validity failures `0`;
- median executed final-endpoint displacement `<= 0.50 m`;
- 95th percentile executed final-endpoint displacement `<= 2.00 m`;
- no more than `5%` cross into `danger_4p5`;
- no more than `5%` collapse into `low_diversity_1p5`;
- median endpoint-spread delta `>= -0.25 m`.

If any S3 bar fails, publish a causal-but-unsafe-or-nonspecific null and stop.

## Named falsifiers

- **Input integrity failure.** Iter29 or iter30 artifacts are missing, invalid, or do not match the
  committed hashes/counts.
- **Direction instability.** The fit-only centroid direction cannot be reproduced byte-identically
  from committed inputs.
- **Patch nondeterminism.** Canary repeated hashes differ, or alpha `0.00` fails to reproduce
  original iter29 outputs.
- **No usable alpha.** No nonzero calibration alpha passes the frozen grid bars.
- **Diagnostic but not causal.** Heldout `eligible_lowdiv` candidate geometry does not move by the
  frozen S2 bars.
- **Causal but risk-worsening.** Candidate spread increases while best-candidate gap worsens beyond
  the frozen S2 limit.
- **Benign harm.** Heldout benign controls move, become dangerous, or collapse beyond S3 bars.
- **Nonspecific corruption.** The patch creates nonfinite or gross-invalid trajectories.
- **Leakage.** Any iteration-12 frame, selector outcome, heldout tuning, per-frame alpha,
  unregistered feature, or post-hoc grid expansion is used.
- **Overclaim attempt.** RESULT language treats this as closed-loop safety, plan-B recovery, or a
  global mechanism proof.

## Required proof artifacts

If run, the RESULT must commit:

- exact command lines;
- direction builder source and `proof-direction/direction.json`;
- server patch and patch/source hash;
- canary logs and canonical hashes;
- calibration grid per-row and per-cell metrics for all alphas, including failed cells;
- selected-alpha decision record with tie handling;
- heldout per-row metrics and aggregate S2/S3 report;
- row counts by split and class, including ambiguous rows;
- claim-boundary paragraph before interpretation.

Any gzip proof artifact over `90 MB` must be split into `.part-*` files before commit, matching the
campaign artifact rule.

## Protocol

1. Commit this `HYPOTHESIS.md` before writing iter31 tooling or running any intervention.
2. Commit the direction builder, server patch, feeder, analyzer, and tests before any GPU replay.
3. Run S0 canary first. Stop on any S0 failure.
4. Run the calibration grid once. Stop if no alpha is eligible.
5. Run heldout once with the selected alpha. Do not rerun with changed bars, labels, alphas, or
   patch form.
6. Publish `RESULT.md` at full weight whether the result passes or fails.
7. A pass authorizes only a separate Stage-2 pre-registration for iteration-12 or selector
   evaluation. It does not authorize iteration-12 scoring, selector evaluation, closed-loop work,
   or a safety claim.
