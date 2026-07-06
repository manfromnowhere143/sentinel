# Iteration 22 - causal planner interpretability, Stage 1 pre-registration

Frozen before any split manifest, extraction, probe fitting, activation intervention, GPU run,
gate run, or closed-loop evaluation for this iteration.

This is a Stage 1 causal-localization experiment on non-evaluation nuScenes train scenes. It is
not a plan-B recovery experiment, not a selector-compatibility experiment, and not a closed-loop
pre-registration. Iteration-12 evaluation frames remain untouched until a separate Stage 2
pre-registration exists.

## Research question

The campaign has shown that frozen end-to-end planners lose feasible alternatives under threat:
UniAD command candidates had **0/37** escapes in iteration 12, the planning-query diversity head
had **0/37** feasible escapes in iteration 19, and the BEV-conditioned head again had **0/37**
feasible escapes in iteration 21.

Iteration 22 Stage 1 asks one narrower question:

> At UniAD's motion/planning bridge, does a frozen internal representation carry a stable
> low-capacity signal for command-candidate collapse, and can a single pre-declared activation
> direction causally increase downstream candidate diversity on non-evaluation heldout scenes
> without harming benign controls?

Acceptable positive claim if all bars pass: one frozen intervention on one UniAD internal
representation changes offline candidate geometry on heldout non-evaluation scenes while
preserving benign controls.

Forbidden claims from Stage 1, even on a pass:

- no claim that UniAD has recovered a deployable plan B;
- no claim that the released-union selector can choose the changed candidate;
- no claim about iteration-12 dangerous frames;
- no closed-loop safety claim;
- no claim that a probe is an explanation.

## Frozen data and split discipline

Stage 1 must create its own split manifest before any extraction.

- Source: nuScenes train-split scene metadata only.
- Exclusions: every NeuroNCAP official/evaluation scene and every iteration-12 evaluation scene
  identity must be excluded. The generator may use scene/run identity solely for exclusion. It
  may not read or use iteration-12 candidate gaps, danger labels, escape labels, per-frame
  scores, or any proof artifact content beyond scene identity.
- Prohibited inputs: uncommitted iter19/iter21 train scene lists, GPU shell history, old
  `/tmp/train_scenes.txt` files, remembered scene names, or extraction logs are not sources of
  truth.
- Manifest: commit `split_manifest.json`, the generator script, the exact generator command,
  exclusion-report text, and a SHA256 digest before extraction.
- Assignment: sort eligible scene names lexicographically, take the first 90 eligible scenes,
  and assign scenes 1-60 to `fit`, 61-75 to `calibration`, and 76-90 to `heldout`. If fewer than
  90 eligible scenes remain after exclusions, publish a data-null and stop before extraction.
- No split movement: after the manifest is committed, no scene may move between splits and no
  scene may be added to rescue positive counts.

The iteration-12 corpus, including its 311 committed frames and 37 dangerous frames, is
evaluation-only and completely outside Stage 1 scoring. A Stage 1 operator must not run an exact
join against iteration 12, inspect the 37 dangerous frames, or tune any tensor/intervention from
iteration-12 outcomes. Any such contact voids Stage 1.

## Frozen representation

Stage 1 tests exactly one writable UniAD internal surface:

- hook site: the actual NeuroNCAP serving call site immediately before
  `planning_head.forward(...)` in `inference/runner.py`, the same call site used by the
  iteration-19 extraction patch;
- tensors: `outs_motion['sdc_traj_query']` and `outs_motion['sdc_track_query']`;
- representation vector: flatten the last decoder layer of `sdc_traj_query` exactly as
  iteration 19 did, concatenate flattened `sdc_track_query`, then append ego speed, yaw rate,
  acceleration, and the one-hot command only for negative-control reporting. The causal
  activation direction itself is computed on the tensor components, not on ego kinematics or
  command bits.

No BEV tensor, late output, planner logits, candidate trajectory, object count, run index, scene
name, or metadata feature may be used as the primary representation in Stage 1. Such quantities
may appear only as explicit negative controls or descriptive artifacts.

If the committed extraction patch cannot recover these tensors with stable shapes, Stage 1
publishes an infrastructure null. Do not substitute a nearby tensor after seeing data.

## Labels and rulers

All labels are computed only from the Stage 1 non-evaluation extraction.

- `danger_positive`: the executed UniAD plan has closest predicted gap `< 3.5 m` to any
  predicted actor future over the immediate horizon, reusing the iteration-12 closest-gap ruler.
- `safe_control`: the executed plan's closest predicted gap is `>= 5.0 m`.
- `collapse_positive`: the three UniAD command-conditioned candidate plans have final-endpoint
  max pairwise spread `<= 0.5 m`.
- `high_diversity_control`: the three command-conditioned candidate plans have final-endpoint
  max pairwise spread `>= 2.0 m`.
- Ambiguous frames between the positive/control thresholds are excluded from that label's
  binary scoring before any model fitting.
- `eligible_intervention_frame`: a heldout or calibration frame that is both
  `danger_positive` and `collapse_positive`.
- `benign_control_frame`: a heldout or calibration frame that is both `safe_control` and
  `high_diversity_control`.

Minimum heldout counts are gates, not suggestions:

- at least 30 `collapse_positive` and 30 `high_diversity_control` frames for localization;
- at least 30 `danger_positive` and 30 `safe_control` frames for descriptive danger reporting;
- at least 20 `eligible_intervention_frame` frames for intervention scoring;
- at least 20 `benign_control_frame` frames for benign intervention controls.

If any minimum count is missing, publish a data-null with the counts and stop. Do not relax a
threshold or move scenes.

## Probe and intervention protocol

### Low-capacity probe

- Preprocessing: standardize tensor components using the `fit` split only. If dimensionality
  reduction is needed, use PCA fitted on the `fit` split only with `n_components = min(16,
  rank)`. The PCA component count is fixed by this rule, not tuned.
- Model: one L2-regularized logistic regression with balanced class weights, `C = 1.0`,
  `max_iter = 10000`, and a fixed random seed of 22.
- Primary label: `collapse_positive` versus `high_diversity_control`.
- Threshold: choose the probability threshold on the `calibration` split that maximizes balanced
  accuracy for the primary label. Freeze that threshold before heldout scoring.
- Negative controls: run the same probe protocol for an ego-kinematics-only vector, a
  shuffled-label control with the same split, and a scene/run metadata control if scene/run
  metadata is present in the artifact. Controls are reported at full weight.

Probe success alone is only a diagnostic result. The RESULT may say that the frozen
representation carries linearly decodable information about candidate collapse under this
split. It may not say the probe found the mechanism.

### Frozen activation intervention

The intervention uses the same motion/planning bridge tensors and no learned generator.

- Direction: compute the tensor-space mean vector of `high_diversity_control` frames minus the
  tensor-space mean vector of `collapse_positive` frames on the `fit` split. Normalize it to unit
  L2 norm. This is the pre-declared anti-collapse direction.
- Patch site: immediately before `planning_head.forward(...)`, add the reshaped direction to
  `outs_motion['sdc_traj_query']` last decoder layer and `outs_motion['sdc_track_query']` in
  their original tensor slots. Ego kinematics and command bits are never patched.
- Grid: `alpha in {0.25, 0.5, 1.0, 2.0}`. `alpha = 0.0` is a sham-control row reported in the
  proof table but is not selectable.
- Calibration selection: evaluate every nonzero alpha on calibration
  `eligible_intervention_frame` and `benign_control_frame` frames. Choose the smallest alpha
  that increases median command-candidate endpoint spread by at least `0.50 m` on calibration
  eligible frames while also satisfying the benign-control limits below on calibration benign
  frames. If no alpha satisfies both, Stage 1 fails the intervention gate; do not invent a new
  direction or grid.
- Heldout evaluation: run the single calibration-selected alpha once on heldout frames. Heldout
  results are not used for any further tuning.

The pre-declared causal direction is increased command-candidate endpoint spread. Increased
spread is not counted as plan-B recovery and is not counted as useful if benign controls are
damaged.

## Offline bars

All bars must pass for a Stage 1 pass.

- **S0 - split, extraction, and determinism integrity.** The committed manifest exists before
  extraction; exclusions are logged; no extraction row contains an error marker; tensor shapes
  are stable for every scored row; row counts by scene/split are reported; a two-scene
  deterministic subset rerun has matching canonical JSONL SHA256 digests; and all heldout
  minimum positive/control counts above are met.
- **S1 - low-capacity collapse localization.** On heldout non-evaluation scenes, the primary
  logistic probe reaches AUC `>= 0.80` and balanced accuracy `>= 0.70` for
  `collapse_positive` versus `high_diversity_control`, and beats each negative control by at
  least `0.10` AUC. Danger-label probe metrics are reported descriptively and do not rescue a
  failed collapse probe.
- **S2 - frozen causal movement.** On heldout `eligible_intervention_frame` frames, the
  selected alpha increases command-candidate endpoint spread on at least `60%` of eligible
  frames, and the median spread increase is `>= 0.75 m`.
- **S3 - benign control.** On heldout `benign_control_frame` frames, median executed-plan
  endpoint displacement is `<= 0.780 m`, 95th percentile executed-plan endpoint displacement is
  `<= 1.5 m`, and no more than `5%` of benign controls cross from `safe_control` to
  `danger_positive` after intervention.

Gate rule: if S0, S1, S2, or S3 fails, publish a Stage 1 null and stop. A pass authorizes only a
separate Stage 2 pre-registration. It does not authorize iteration-12 scoring, selector
compatibility, or closed-loop evaluation.

## Named falsifiers

- **No stable localized signal.** S1 fails or heldout positive/control counts are insufficient.
- **Metadata or kinematics explains the signal.** Any negative control is within `0.10` AUC of
  the internal-representation probe on heldout.
- **Diagnostic but not causal.** S1 passes but S2 fails.
- **Causal but nonspecific corruption.** S2 passes but S3 fails.
- **Inadequate data support.** S0 count floors cannot be met under the frozen split.
- **Extraction nondeterminism.** Tensor rows, shapes, or canonical subset hashes fail S0.
- **Protocol breach.** Any use of iteration-12 outcomes, uncommitted prior scene lists, hidden
  tensor search, hidden alpha search, or heldout retuning voids Stage 1.
- **Overclaim attempt.** RESULT language that treats probe success as mechanism proof or spread
  increase as deployable plan-B recovery is a reporting failure and must be corrected before
  publication.

## Proof artifacts required

Before any extraction:

- this `HYPOTHESIS.md`;
- split-manifest generator script, manifest, exclusion report, generator command, and SHA256;
- extraction/intervention patch and run scripts with exact hook-site comments.

With the Stage 1 RESULT:

- raw extraction logs and JSONL/gzip artifacts, split into git-sized parts if needed;
- tensor shape/dtype/row-count summaries for every split;
- deterministic subset rerun proof and canonical digests;
- probe config, fitted coefficients or hashes, calibration threshold, heldout metrics, and all
  negative-control outputs;
- full calibration grid table including failed alphas and the sham alpha;
- per-frame heldout intervention decisions, spread changes, benign displacement, and danger
  threshold crossings;
- command lines for every artifact;
- a `RESULT.md` that publishes pass or null at full weight and includes an explicit
  claim-boundary paragraph before interpretation.

## Protocol

1. Commit this hypothesis.
2. Create and commit the Stage 1 split manifest and generator before extraction.
3. Create and commit extraction/intervention patch code and run scripts before GPU launch.
4. Extract only the committed non-evaluation Stage 1 scenes.
5. Fit probes on `fit`, select threshold and alpha on `calibration`, and evaluate `heldout`
   once.
6. Commit proof artifacts and publish `RESULT.md`, pass or null.
7. Only after a Stage 1 pass, write a separate Stage 2 hypothesis that freezes the single
   tensor direction and alpha before any iteration-12 or closed-loop work.
