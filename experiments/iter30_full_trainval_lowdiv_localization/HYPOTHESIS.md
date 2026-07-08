# Iteration 30 - full-trainval low-diversity localization pre-registration

Frozen before any iter30 analyzer, probe fitting, PCA fitting, threshold selection, label
recomputation, activation-direction writing, intervention replay, iteration-12 contact, selector
scoring, closed-loop evaluation, GPU run, or gcloud command.

Iteration 29 passed the full-trainval risk-support atlas on the official staged nuScenes trainval
root. It established enough fresh post-firewall `eligible_lowdiv` hazard frames and
`benign_control` frames for a successor, while the optional strict-collapse note failed. Iteration
30 is that successor's first diagnostic gate. It is not a causal-intervention experiment.

## Research question

Using only the committed iteration-29 extraction and GT artifacts, does UniAD's frozen
motion/planning-bridge representation carry a stable, low-capacity signal for the pre-registered
`eligible_lowdiv` hazard label that generalizes to heldout fresh scenes and exceeds non-internal
controls?

Acceptable positive claim if every bar passes:

> On the committed full-trainval fresh-scene split, the concatenated `sdc_traj_query_last` and
> `sdc_track_query` representation carries linearly decodable information about the frozen
> `eligible_lowdiv` label beyond metadata and ego-plan-kinematic controls.

Forbidden claims from this iteration, even on a pass:

- no claim that the probe is an explanation;
- no claim that the representation is the cause of low diversity;
- no activation direction, activation patch, intervention alpha, or candidate-repair claim;
- no iteration-12, NeuroNCAP, selector-compatibility, closed-loop, or safety-improvement claim;
- no strict-collapse language; iteration 29 failed the strict-collapse support note;
- no claim that the result transfers to VAD, other UniAD checkpoints, or other planners.

## Frozen input artifacts

Iteration 30 may use only committed iteration-29 artifacts:

- `experiments/iter29_trainval_risk_support_atlas/proof-full-extract/sentinel_e29_stage1.jsonl.gz.part-*`;
- `experiments/iter29_trainval_risk_support_atlas/proof-full-extract/sentinel_e29_stage1_gt.jsonl.gz`;
- `experiments/iter29_trainval_risk_support_atlas/proof-full-extract/s0_integrity_report.json`;
- `experiments/iter29_trainval_risk_support_atlas/proof-full-extract/label_atlas_report.json`;
- `experiments/iter29_trainval_risk_support_atlas/proof-full-extract/sha256s.txt`;
- `experiments/iter29_trainval_risk_support_atlas/HYPOTHESIS.md`;
- `experiments/iter29_trainval_risk_support_atlas/RESULT.md`.

No new extraction is authorized. No GPU, Docker, NeuroNCAP, gcloud, browser download, dataset
copy, or remote box command is authorized. If any required committed artifact is missing or its
hash does not match iteration 29's proof, publish an infrastructure-null and stop.

## Frozen labels

Labels are exactly iteration 29 labels and must be recomputed by the iter30 analyzer from the
committed rows using the same definitions:

- `danger_4p5`: closest predicted gap over the immediate first-three-step horizon `< 4.5 m`;
- `safe_6p0`: closest predicted gap over the immediate first-three-step horizon `>= 6.0 m`;
- `low_diversity_1p5`: three command-conditioned candidate plans have final-endpoint max pairwise
  spread `<= 1.5 m`;
- `high_diversity_2p0`: final-endpoint max pairwise spread `>= 2.0 m`;
- `eligible_lowdiv`: `danger_4p5` and `low_diversity_1p5`;
- `benign_control`: `safe_6p0` and `high_diversity_2p0`.

The primary binary task is `eligible_lowdiv` versus `benign_control`. Ambiguous rows that are
neither primary positive nor primary control are excluded from the probe task but still counted in
the proof summary. Use all eligible positives and all eligible controls; do not downsample,
reweight rows outside the fixed model class, move scenes, relax labels, or tune thresholds after
heldout scoring.

## S0 - input and count integrity

Before any probe fitting, the analyzer must validate:

- the split extraction parts reconstruct into a gzip stream that validates;
- the unsplit extraction gzip SHA256 matches iteration 29's proof table;
- GT gzip SHA256 matches iteration 29's proof table;
- S0 report says `all_s0_integrity_pass: true`;
- label-atlas report says `support_pass: true`;
- label-atlas report says `strict_optional_support_pass: false`;
- recomputed primary counts match iteration 29 exactly:
  - `eligible_lowdiv`: fit `127`, calibration `108`, heldout `158`;
  - `benign_control`: fit `5084`, calibration `2344`, heldout `2245`;
- heldout `eligible_lowdiv` frames come from at least `5` scenes and no single heldout scene
  contributes more than `25%` of heldout `eligible_lowdiv` rows.

If any S0 bar fails, publish an infrastructure/data-null and stop before probe fitting.

## Frozen feature sets

Primary internal representation:

- flatten `sdc_traj_query_last`;
- concatenate flattened `sdc_track_query`;
- no planner-output geometry, object counts, scene names, raw timestamps, or labels are appended.

Preprocessing for every probe:

- standardize each feature using fit-split mean and standard deviation only;
- drop fit-constant dimensions only; record the dropped count;
- fit PCA on the fit split only;
- `n_components = min(32, rank, n_fit_rows - 1, n_features_after_constant_drop)`;
- no PCA whitening;
- fixed random seed `30` anywhere an operation needs a seed.

Model for every probe:

- one L2-regularized logistic regression with balanced class weights;
- `C = 1.0`;
- `max_iter = 10000`;
- threshold chosen only on calibration to maximize balanced accuracy;
- ties choose the highest threshold among tied balanced-accuracy values;
- heldout is evaluated once.

Negative controls:

- **metadata control:** manifest scene ordinal within its split, sample index normalized by scene
  length, and timestamp offset from the first sample in that scene;
- **ego-plan-kinematic control:** first-step and three-step displacement magnitude, final endpoint,
  and approximate yaw change derived from the executed plan only;
- **shuffled-label internal control:** same internal features and split, with fit labels shuffled
  by seed `30`; calibration and heldout labels are not shuffled.

Positive-control report, not a pass/fail negative control:

- **candidate-geometry control:** closest gap, endpoint spread, candidate endpoint count, and object
  count. This may predict the label because the label is defined from candidate geometry; it cannot
  rescue or fail the internal-representation claim.

## S1 - low-capacity localization bars

S1 is evaluated on heldout rows only, after calibration threshold selection.

Primary internal probe must satisfy all bars:

- heldout AUROC `>= 0.80`;
- heldout average precision `>= 0.20`;
- heldout balanced accuracy `>= 0.70`;
- heldout recall on `eligible_lowdiv` at the frozen calibration threshold `>= 0.60`;
- heldout specificity on `benign_control` at the frozen calibration threshold `>= 0.70`.

Negative-control separation must satisfy all bars:

- primary heldout AUROC exceeds metadata-control AUROC by at least `0.10`;
- primary heldout AUROC exceeds ego-plan-kinematic-control AUROC by at least `0.10`;
- shuffled-label internal-control AUROC is between `0.40` and `0.60`;
- shuffled-label internal-control balanced accuracy is between `0.40` and `0.60`.

If any S1 bar fails, publish a diagnostic null and stop. Do not write an activation direction, do
not run an intervention, do not touch iteration-12, and do not write a closed-loop
pre-registration from a failed S1.

## S2 - scene-cluster robustness bars

S2 is evaluated only if S1 passes. Use heldout scenes as clusters. Run exactly `1000`
scene-cluster bootstrap resamples with replacement using seed `30`. In each resample, include all
primary-task rows from sampled scenes. Skip a resample only if it contains a single class; report
the skipped count.

Robustness bars:

- at least `900` valid bootstrap resamples;
- 5th percentile of heldout AUROC across valid resamples `>= 0.70`;
- 5th percentile of heldout balanced accuracy across valid resamples `>= 0.62`;
- median heldout AUROC across valid resamples `>= 0.80`.

If S2 fails, publish a robustness null and stop. A positive point estimate without scene-cluster
robustness is not enough to authorize causal work.

## Named falsifiers

- **Input integrity failure.** Iter29 artifacts are missing, invalid, or do not match the committed
  hashes/counts.
- **Label mismatch.** Recomputed labels do not exactly match iteration 29's published primary
  counts.
- **No localized signal.** The primary internal probe fails any S1 performance bar.
- **Metadata explains the signal.** Metadata control comes within `0.10` AUROC of the primary
  probe.
- **Ego-plan kinematics explain the signal.** Ego-plan-kinematic control comes within `0.10` AUROC
  of the primary probe.
- **Shuffle sanity failure.** Shuffled-label internal control is outside the frozen null band.
- **Scene-cluster fragility.** S2 robustness bars fail.
- **Protocol breach.** Any threshold movement, split movement, row downsampling, heldout tuning,
  unregistered feature addition, iteration-12 inspection, intervention attempt, GPU launch, or
  closed-loop run voids the result.
- **Overclaim attempt.** RESULT language that treats probe success as mechanism proof, causal proof,
  intervention evidence, selector compatibility, or closed-loop safety must be corrected before
  publication.

## Required proof artifacts

With the RESULT:

- exact command line;
- artifact hash validation table;
- reconstructed-gzip validation result without committing another unsplit copy;
- row counts by split and class, including ambiguous rows;
- PCA dimensionality, dropped-dimension count, and fit-only preprocessing hashes;
- calibration threshold and tie count;
- heldout metrics for primary, negative controls, shuffled-label control, and candidate-geometry
  positive control;
- scene-cluster bootstrap summary with skipped-resample count and quantiles;
- coefficient/checkpoint artifact or coefficient hash for every fitted probe;
- claim-boundary paragraph before interpretation.

## Protocol

1. Commit this hypothesis before writing or running the iter30 analyzer.
2. Commit the analyzer and any tests before running it on the iteration-29 proof artifacts.
3. Run the analyzer once. Do not rerun with changed thresholds, feature sets, or labels.
4. Publish `RESULT.md` at full weight whether S0, S1, or S2 fails or passes.
5. A pass authorizes only a separate causal-intervention pre-registration. It does not authorize
   activation patching, iteration-12 scoring, selector evaluation, or closed-loop work.
