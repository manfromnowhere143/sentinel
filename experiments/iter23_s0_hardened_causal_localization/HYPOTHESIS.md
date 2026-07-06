# Iteration 23 - S0-hardened causal localization pre-registration

Frozen before any iter23 availability manifest, extraction patch, canary run, full extraction,
probe fitting, activation direction, intervention replay, GPU run, iteration-12 contact, or
closed-loop evaluation.

Iteration 22 asked the right mechanistic question but failed before the question could be tested:
the extraction and GT sidecar used incompatible timestamp precision, and the frozen heldout split
had zero GT rows. Iteration 23 is therefore not a broader hypothesis. It is the same narrow
Stage 1 causal-localization line with a hardened S0 gate that must prove the artifacts are valid
before any probe or intervention exists.

## Research question

At UniAD's motion/planning bridge, after proving extraction/GT integrity and heldout data support
under a frozen non-evaluation split, does the representation carry a low-capacity signal for
command-candidate collapse, and can one pre-declared activation direction increase downstream
candidate diversity on heldout scenes without damaging benign controls?

Acceptable positive claim if every bar passes:

> Under one frozen non-evaluation split and one frozen UniAD hook site, a pre-declared
> motion/planning-bridge activation direction changes offline candidate geometry on heldout
> scenes while preserving benign controls.

Forbidden claims from this iteration, even on a pass:

- no claim about iteration-12 dangerous frames;
- no claim that a deployable plan B has been recovered;
- no selector-compatibility claim;
- no closed-loop safety claim;
- no claim that a probe is an explanation;
- no claim that this mechanism generalizes to VAD, other UniAD checkpoints, or other planners.

## Frozen data and split discipline

Iteration 23 must create its own availability and split manifest after this hypothesis is
committed and before any model extraction.

- Source: nuScenes train-split scene metadata plus local file-existence checks for the staged
  image/keyframe files only.
- Exclusions: every NeuroNCAP official/evaluation scene and every iteration-12 evaluation scene
  identity must be excluded. Scene identity may be used only for exclusion. Iteration-12 labels,
  gaps, escapes, scores, per-frame evidence, and candidate proof artifacts are prohibited.
- Prohibited inputs: uncommitted iter19/iter21/iter22 scene lists, GPU shell history,
  remembered scene names, extraction logs, and result labels are not sources of truth.
- Token hygiene: manifests must not commit nuScenes scene/sample tokens. Use scene names,
  sample indices, timestamps, counts, and hashes only.
- Availability manifest: commit the generator script, exact command, exclusion report,
  `availability_manifest.json`, and SHA256 digest before any GPU launch. Each eligible scene
  must have at least 24 locally readable keyframes with all six cameras present.
- Eligibility bar before extraction: at least 36 eligible scenes after exclusions, with planned
  heldout coverage of at least 200 locally readable keyframes. If either condition fails, publish
  an availability-null and stop before model extraction.
- Split rule: sort eligible scenes by SHA256 of `iter23:<scene_name>`, ascending. Assign the
  first 60% to `fit`, the next 20% to `calibration`, and the final 20% to `heldout`, rounding
  down for `fit` and assigning any remainder to `heldout`. No scene may move between splits
  after the manifest is committed.
- Frame order: within each scene, use nuScenes sample order. Every extraction row must include
  the split, scene name, zero-based sample index within that scene, and the original nuScenes
  sample timestamp in microseconds.

The iteration-12 corpus remains completely outside Stage 1. No exact join, no dangerous-frame
inspection, no selector scoring, and no closed-loop run may touch iteration-12 unless a later
Stage 2 pre-registration exists.

## Frozen representation

The primary hook site and representation match the registered iter22 target:

- hook site: immediately before `planning_head.forward(...)` in UniAD `inference/runner.py`;
- tensors: `outs_motion['sdc_traj_query']` and `outs_motion['sdc_track_query']`;
- representation vector: flatten the last decoder layer of `sdc_traj_query`, then concatenate
  flattened `sdc_track_query`.

Ego speed, yaw rate, acceleration, command, scene name, sample index, timestamp, object count,
candidate trajectories, planner logits, BEV tensors, and late outputs are not part of the
primary representation. They may be logged only for labels, integrity, or named negative
controls.

No substitute tensor is allowed after seeing extraction results. If this hook cannot produce
stable tensor shapes, publish an infrastructure null.

## Join key and canary discipline

The S0 gate is split into a canary phase and a full-extraction phase.

### Canary phase

Before the canary run, commit:

- extraction patch;
- feeder script;
- canary run script;
- full extraction run script;
- baseline analyzer;
- canonical JSONL hashing script or documented canonicalization routine.

The canary scene set is frozen by manifest order: the first scene in each split. Extract at most
five keyframes per canary scene. Run the canary twice from a clean model process.

Canary pass bars:

- exactly one GT row and one extraction row per served keyframe;
- 100% one-to-one join on `(scene, sample_index, timestamp_us)`;
- zero `missing_gt`, duplicate-key, missing-tensor, or tensor-shape error rows;
- identical canonical SHA256 for the two canary extraction outputs and the two GT sidecars;
- all primary tensor shapes stable within and across canary runs.

If any canary bar fails, publish an infrastructure null and stop before full extraction.

### Full extraction phase

Only after canary pass may the full manifest be extracted once.

Full S0 integrity pass bars:

- extraction row count equals GT row count for non-reset rows;
- 100% one-to-one join on `(scene, sample_index, timestamp_us)`;
- zero error rows of any type;
- row counts by split and scene match the committed availability manifest, allowing only
  pre-declared image-read skips that are listed in the proof table;
- primary tensor shapes and dtypes are stable for every scored row;
- no extraction row contains an intervention alpha other than `0.0`;
- gzip artifacts validate locally and, if larger than 90 MB, are split into `.part-*` files before
  commit.

If full extraction integrity fails, publish a data-null and stop before probe fitting.

## Labels and minimum counts

All labels are computed only from the iter23 non-evaluation extraction after S0 integrity passes.

- `danger_positive`: executed UniAD plan closest predicted gap `< 3.5 m` over the immediate
  horizon.
- `safe_control`: executed plan closest predicted gap `>= 5.0 m`.
- `collapse_positive`: three command-conditioned candidate plans have final-endpoint max pairwise
  spread `<= 0.5 m`.
- `high_diversity_control`: three command-conditioned candidate plans have final-endpoint max
  pairwise spread `>= 2.0 m`.
- Ambiguous frames between thresholds are excluded from binary scoring.
- `eligible_intervention_frame`: both `danger_positive` and `collapse_positive`.
- `benign_control_frame`: both `safe_control` and `high_diversity_control`.

Minimum count floors, evaluated after full extraction and before any probe fitting:

| split | required counts |
|---|---|
| fit | `collapse_positive >= 30`, `high_diversity_control >= 30` |
| calibration | `collapse_positive >= 15`, `high_diversity_control >= 15`, `eligible_intervention_frame >= 10`, `benign_control_frame >= 10` |
| heldout | `collapse_positive >= 30`, `high_diversity_control >= 30`, `danger_positive >= 30`, `safe_control >= 30`, `eligible_intervention_frame >= 20`, `benign_control_frame >= 20` |

If any count floor fails, publish a data-null with all counts and stop. Do not move scenes, relax
thresholds, or relabel frames.

## Probe protocol

Probe fitting is authorized only after S0 integrity and count floors pass.

- Preprocessing: standardize primary tensor components using the `fit` split only.
- Dimensionality reduction: PCA fitted on the `fit` split only with
  `n_components = min(16, rank, n_fit_rows, n_features)`.
- Model: one L2-regularized logistic regression with balanced class weights, fixed seed 23,
  `C = 1.0`, `max_iter = 10000`.
- Primary label: `collapse_positive` versus `high_diversity_control`.
- Threshold: choose the probability threshold on calibration that maximizes balanced accuracy.
  Freeze it before heldout scoring.
- Negative controls: same protocol for ego-kinematics-only, scene/sample-index metadata,
  shuffled-label internal tensor, and late-output candidate-geometry features.

S1 pass bars on heldout:

- primary internal-tensor AUC `>= 0.80`;
- primary balanced accuracy `>= 0.70`;
- primary AUC exceeds each negative control by at least `0.10`;
- shuffled-label control AUC must be between `0.40` and `0.60`.

If S1 fails, publish a diagnostic null and stop before activation-direction writing.

## Frozen activation intervention

The intervention exists only if S1 passes.

- Direction: on the fit split, compute mean primary tensor vector for
  `high_diversity_control` minus mean primary tensor vector for `collapse_positive`, then
  normalize to unit L2 norm.
- Patch site: immediately before `planning_head.forward(...)`, add the reshaped direction to
  `outs_motion['sdc_traj_query']` last decoder layer and `outs_motion['sdc_track_query']` in
  their original tensor slots.
- Grid: `alpha in {0.25, 0.5, 1.0, 2.0}`. `alpha = 0.0` is a sham-control row that must be
  reported but is not selectable.
- Calibration selection: choose the smallest nonzero alpha that increases median command-candidate
  endpoint spread by at least `0.50 m` on calibration eligible frames while meeting the benign
  limits below on calibration benign frames.
- Heldout evaluation: run the single selected alpha once on heldout frames. Heldout results may
  not alter the tensor, direction, alpha, labels, or bars.

S2 pass bars on heldout eligible frames:

- endpoint spread increases on at least `60%` of eligible heldout frames;
- median endpoint-spread increase `>= 0.75 m`;
- sham alpha median endpoint-spread change `< 0.10 m`.

S3 pass bars on heldout benign controls:

- median executed-plan endpoint displacement `<= 0.780 m`;
- 95th percentile executed-plan endpoint displacement `<= 1.5 m`;
- no more than `5%` of benign controls cross from `safe_control` to `danger_positive`;
- no more than `5%` of benign controls lose high-diversity status solely due to the intervention.

If S2 or S3 fails, publish the null and stop. A pass authorizes only a separate Stage 2
pre-registration. It does not authorize iteration-12 scoring, selector compatibility, or
closed-loop work.

## Named falsifiers

- **Availability unsupported.** Fewer than 36 eligible non-evaluation scenes or fewer than 200
  planned heldout keyframes exist under the frozen availability rules.
- **Join key invalid.** Canary or full extraction fails the `(scene, sample_index, timestamp_us)`
  one-to-one join.
- **Extraction nondeterminism.** Canary canonical SHA256 digests differ, tensor shapes drift, or
  error rows appear.
- **Inadequate data support.** Count floors fail after valid extraction.
- **No stable localized signal.** S1 fails.
- **Metadata or kinematics explains the signal.** Any negative control is within `0.10` AUC of
  the primary internal-tensor probe.
- **Diagnostic but not causal.** S1 passes but S2 fails.
- **Causal but nonspecific corruption.** S2 passes but S3 fails.
- **Protocol breach.** Any use of iteration-12 outcomes, uncommitted scene lists, hidden tensor
  search, hidden alpha search, heldout retuning, or post-data split movement voids the result.
- **Overclaim attempt.** Any RESULT language that treats probe success as mechanism proof or
  spread increase as deployable plan-B recovery must be corrected before publication.

## Required proof artifacts

Before any GPU launch:

- this `HYPOTHESIS.md`;
- availability/split manifest generator, manifest, exclusion report, command record, and SHA256;
- extraction patch, feeder, canary/full extraction run scripts, analyzer, and canonical hashing
  routine.

With the RESULT:

- raw canary logs, full extraction logs, and JSONL/gzip artifacts;
- canonical SHA256 table for both canary runs;
- split/scene/frame availability table and actual row-count table;
- join-integrity report with error-type counts even if zero;
- tensor shape/dtype summaries;
- if S0 passes, label counts by split before any probe;
- if S1 runs, probe config, coefficients or hashes, threshold, heldout metrics, and all negative
  controls;
- if S2/S3 run, full calibration grid including failed alphas and sham alpha, selected-alpha
  rule application, and per-frame heldout intervention decisions;
- exact command lines for every artifact;
- claim-boundary paragraph in `RESULT.md`.

## Protocol

1. Commit this hypothesis.
2. Create and commit the availability/split manifest generator and manifest. If availability
   fails, publish an availability-null and stop.
3. Create and commit canary/full extraction code and analyzer before GPU launch.
4. Run the canary twice. If canary fails, publish an infrastructure null and stop.
5. Run full non-evaluation extraction once. If S0 integrity or count floors fail, publish a
   data-null and stop.
6. Only after S0 passes, fit probes and evaluate S1.
7. Only after S1 passes, write the activation direction and run the calibration/heldout
   intervention protocol.
8. Publish pass or null at full weight.
9. Only after a full S0-S3 pass, write a separate Stage 2 pre-registration for any iteration-12
   or closed-loop question.
