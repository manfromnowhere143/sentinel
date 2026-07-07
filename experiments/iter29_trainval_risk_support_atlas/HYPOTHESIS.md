# Iteration 29 - full-trainval risk-support atlas pre-registration

Frozen before any iter29 manifest import, extraction patch, canary run, full extraction, label
atlas computation, probe fitting, activation direction, intervention replay, iteration-12 contact,
selector scoring, closed-loop evaluation, or GPU run.

Iteration 28 completed the missing infrastructure prerequisite: the official nuScenes v1.0
trainval metadata and ten sensor-blob archives are staged and extracted under
`/datasets/nuscenes-full`, and the committed availability inventory found `532` fresh
post-firewall train scenes with `21,461` eligible keyframes. Iteration 29 is the first research
gate that may use that root.

Iteration 29 is not a causal-intervention experiment. It is a full-trainval risk-support atlas.
Its job is to answer whether the newly staged, fresh non-evaluation trainval support contains
enough low-diversity hazardous frames and benign controls to justify a later causal-localization
or planner-repair pre-registration.

## Research question

Using only the committed iteration-28 availability manifest and `/datasets/nuscenes-full`, does
the fresh post-firewall trainval pool contain enough pre-registered low-diversity hazard support
and benign controls for a later model-side Sentinel experiment?

Acceptable positive claim if every bar passes:

> The committed full-trainval root contains sufficient fresh low-diversity hazard and benign
> control support to justify a separate causal-localization or planner-repair pre-registration.

Forbidden claims from this iteration, even on a pass:

- no claim about iteration-12 dangerous frames;
- no claim that a probe localizes a mechanism;
- no claim that an activation direction exists;
- no activation intervention, intervention alpha, selector-compatibility, or closed-loop claim;
- no claim that `low_diversity_1p5` is the same phenomenon as strict planner collapse;
- no claim that this support generalizes to VAD, other UniAD checkpoints, or other planners;
- no deployment, safety, or "solved plan B" language.

## Frozen data source and firewall

Iteration 29 may use only:

- data root: `/datasets/nuscenes-full`;
- metadata root: `/datasets/nuscenes-full/v1.0-trainval`;
- committed availability manifest:
  `experiments/iter28_nuscenes_trainval_staging/proof-inventory/selected_availability_manifest.json`;
- committed manifest digest:
  `experiments/iter28_nuscenes_trainval_staging/proof-inventory/selected_availability_manifest.sha256`.

The iter28 manifest already applies the known-data firewall excluding NeuroNCAP / iteration-12
evaluation scenes and known iter22/iter23/iter24 scene names. Iteration 29 must not add scenes,
move scenes between splits, use uncommitted scene lists, use GPU shell history, use remembered
scene names, or inspect iteration-12 outcomes.

Token hygiene is unchanged: committed iter29 manifests and proof summaries must not contain
nuScenes scene/sample tokens. Use scene names, sample indices, timestamps, counts, relative camera
paths, and hashes only.

## S0a manifest-import gate

Before any extraction or GPU launch, commit the manifest-import script and run it once against the
committed iter28 manifest. It must write an iter29 input manifest and SHA256 sidecar under this
experiment directory.

Manifest-import pass bars:

- source manifest SHA256 exactly matches the committed iter28 sidecar;
- data root is exactly `/datasets/nuscenes-full`;
- root ID is exactly `/datasets/nuscenes-full`;
- split names are exactly `fit`, `calibration`, and `heldout`;
- imported split counts match iter28: `266` fit scenes, `133` calibration scenes, `133` heldout
  scenes;
- imported keyframe counts match iter28: `10,726` fit, `5,375` calibration, `5,360` heldout,
  `21,461` total;
- known-data contamination count is `0`;
- mixed-root keyframe count is `0`;
- metadata identifier field count is `0`.

If any S0a bar fails, publish an infrastructure-null and stop before model extraction.

## Frozen extraction surface

Iteration 29 must commit an iter29-namespaced copy of the proven iter24 extraction surface before
any GPU launch:

- hook site: immediately before `planning_head.forward(...)` in UniAD `inference/runner.py`;
- tensors: `outs_motion['sdc_traj_query']` and `outs_motion['sdc_track_query']`;
- logged planner outputs required for labels: executed plan `traj`, command candidates `cands`,
  object states `objs`, and future modes `futs`;
- join key: `(scene, sample_index, timestamp_us)`;
- intervention alpha: extraction rows must contain no intervention or `intervention_alpha = 0.0`;
- no probe features may be fitted and no activation direction may be written.

## S0b canary integrity gate

Before the canary run, commit:

- this `HYPOTHESIS.md`;
- manifest-import script and imported iter29 manifest;
- extraction patch;
- feeder script;
- canary run script;
- full extraction run script;
- S0 analyzer;
- label-atlas analyzer;
- canonical JSONL hashing routine.

The canary scene set is frozen by imported manifest order: the first two scenes in each split.
Extract at most five keyframes per canary scene. Run the canary twice from a clean model process.

Canary pass bars:

- exactly one GT row and one extraction row per served keyframe;
- 100% one-to-one join on `(scene, sample_index, timestamp_us)`;
- zero `missing_gt`, duplicate-key, missing-tensor, invalid-candidate-count, context-error,
  nonzero-intervention, or tensor-shape error rows;
- identical canonical SHA256 for the two canary extraction outputs and the two GT sidecars;
- all primary tensor shapes and dtypes are stable within and across canary runs.

If any canary bar fails, publish an infrastructure-null and stop before full extraction.

## S0c full extraction integrity gate

Only after S0a and S0b pass may the full iter29 manifest be extracted once. The full run covers all
`21,461` imported keyframes unless a pre-declared image-read failure is emitted and recorded by
scene/frame before scoring.

Full S0 pass bars:

- extraction row count equals GT row count for non-reset rows;
- 100% one-to-one join on `(scene, sample_index, timestamp_us)`;
- zero error rows of any type;
- row counts by split and scene match the imported iter29 manifest, allowing only pre-declared
  image-read skips listed in the proof table;
- primary tensor shapes and dtypes are stable for every scored row;
- no extraction row contains an intervention alpha other than `0.0`;
- gzip artifacts validate locally and, if larger than 90 MB, are split into `.part-*` files before
  commit.

If full extraction integrity fails, publish an infrastructure/data-null and stop before label
support claims.

## Frozen label atlas

All labels are computed only from fresh iter29 non-evaluation extraction rows after S0 integrity
passes.

Distance labels use the immediate horizon of the first three executed-plan steps:

- `danger_3p5`: closest predicted gap `< 3.5 m`;
- `danger_4p5`: closest predicted gap `< 4.5 m`;
- `safe_5p0`: closest predicted gap `>= 5.0 m`;
- `safe_6p0`: closest predicted gap `>= 6.0 m`.

Candidate-diversity labels use final-endpoint max pairwise spread across the three
command-conditioned candidate plans:

- `strict_collapse_0p5`: spread `<= 0.5 m`;
- `low_diversity_1p0`: spread `<= 1.0 m`;
- `low_diversity_1p5`: spread `<= 1.5 m`;
- `high_diversity_2p0`: spread `>= 2.0 m`.

Composite support labels:

- `eligible_strict`: `danger_3p5` and `strict_collapse_0p5`;
- `eligible_lowdiv`: `danger_4p5` and `low_diversity_1p5`;
- `benign_control`: `safe_6p0` and `high_diversity_2p0`.

`strict_collapse_0p5` and `eligible_strict` must be reported at full weight, even if zero. A
future experiment may use the low-diversity family only if it names the phenomenon
`low_diversity`, not strict collapse.

## S1 support bars

The primary support gate is `low_diversity_1p5` under `danger_4p5`, not
`strict_collapse_0p5`. Passing S1 authorizes only a later pre-registration. It does not authorize
probe fitting, activation directions, interventions, iteration-12 scoring, selector evaluation, or
closed-loop work.

Minimum counts:

| split | required counts |
|---|---|
| fit | `low_diversity_1p5 >= 240`, `high_diversity_2p0 >= 240`, `danger_4p5 >= 240`, `safe_6p0 >= 240`, `eligible_lowdiv >= 80`, `benign_control >= 160` |
| calibration | `low_diversity_1p5 >= 80`, `high_diversity_2p0 >= 80`, `danger_4p5 >= 80`, `safe_6p0 >= 80`, `eligible_lowdiv >= 25`, `benign_control >= 60` |
| heldout | `low_diversity_1p5 >= 80`, `high_diversity_2p0 >= 80`, `danger_4p5 >= 80`, `safe_6p0 >= 80`, `eligible_lowdiv >= 25`, `benign_control >= 60` |

Distribution bars:

- fit `eligible_lowdiv` frames must come from at least 15 scenes;
- calibration `eligible_lowdiv` frames must come from at least 5 scenes;
- heldout `eligible_lowdiv` frames must come from at least 5 scenes;
- no single scene may contribute more than 25% of heldout `eligible_lowdiv` frames.

If any S1 count or distribution bar fails, publish a support-null and stop. Do not move scenes,
relax thresholds, merge splits, reweight frames, or relabel frames.

## Optional strict-collapse support note

If the stricter labels also satisfy these counts, the result may state that strict-collapse support
exists:

| split | required strict counts |
|---|---|
| fit | `strict_collapse_0p5 >= 120`, `eligible_strict >= 40` |
| calibration | `strict_collapse_0p5 >= 40`, `eligible_strict >= 12` |
| heldout | `strict_collapse_0p5 >= 40`, `eligible_strict >= 12` |

Failure of this optional strict note does not fail S1. It only limits the language of any later
experiment: a successor may not call selected frames "strict collapse" unless these strict counts
pass.

## Named falsifiers

- **Manifest import invalid.** The iter29 input manifest does not exactly match the committed
  iter28 manifest digest, split counts, keyframe counts, root ID, or token-hygiene bars.
- **Known-data contamination.** Any NeuroNCAP, iteration-12, iter22, iter23, or iter24 scene enters
  confirmatory counts.
- **Join key invalid.** Canary or full extraction fails the `(scene, sample_index, timestamp_us)`
  one-to-one join.
- **Extraction nondeterminism.** Canary canonical SHA256 digests differ, tensor shapes drift, or
  error rows appear.
- **Support absent.** S1 minimum counts fail.
- **Support concentrated.** S1 distribution bars fail, showing support is a small scene artifact.
- **Strict collapse absent.** The optional strict-collapse counts fail; this does not kill S1 but
  forbids strict-collapse language in successors.
- **Protocol breach.** Any use of iteration-12 outcomes, hidden scene search, hidden threshold
  search, heldout retuning, post-data split movement, or use of excluded known rows in
  confirmatory counts voids the result.
- **Overclaim attempt.** Any RESULT language that treats support counts as mechanism evidence,
  probe evidence, causal evidence, selector compatibility, or deployable plan-B recovery must be
  corrected before publication.

## Required proof artifacts

Before any GPU launch:

- this `HYPOTHESIS.md`;
- manifest-import script, imported iter29 manifest, command record, validation report, and SHA256;
- extraction patch, feeder, canary/full extraction run scripts, S0 analyzer, label-atlas analyzer,
  and canonical hashing routine.

With the RESULT:

- raw canary logs, full extraction logs, and JSONL/gzip artifacts;
- canonical SHA256 table for canary runs and full extraction artifacts;
- split/scene/frame availability table and actual row-count table;
- firewall exclusion summary inherited from iter28 plus iter29 contamination checks;
- join-integrity report with error-type counts even if zero;
- tensor shape/dtype summaries;
- label counts by split and by scene for every label above;
- count and distribution bar report, including failures;
- exact command lines for every artifact;
- claim-boundary paragraph in `RESULT.md`.

## Protocol

1. Commit this hypothesis.
2. Commit the manifest import and extraction/analysis surface before any GPU launch.
3. Generate and commit the imported iter29 manifest before any canary extraction.
4. Run the two-run canary only if S0a passes.
5. Run full extraction only if the canary passes.
6. Compute the label atlas only if full S0 passes.
7. Publish the result at full weight whether S1 passes or fails.
8. A pass authorizes only a separate successor pre-registration. It does not authorize probe
   fitting, activation intervention, iteration-12 scoring, selector evaluation, or closed-loop
   evaluation.
