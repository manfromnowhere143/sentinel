# Iteration 24 - fresh risk-support atlas pre-registration

Frozen before any iter24 manifest generation, extraction patch, canary run, full extraction, label
atlas computation, probe fitting, activation direction, intervention replay, GPU run,
iteration-12 contact, selector scoring, or closed-loop evaluation.

Iterations 22 and 23 asked a narrow causal-localization question at UniAD's motion/planning
bridge. Iteration 22 failed at artifact integrity. Iteration 23 repaired that failure: canary and
full extraction passed S0, with 2,627/2,627 joined non-reset rows, zero error rows, and stable
primary tensor shapes. The next gate then failed because the frozen non-evaluation corpus had no
collapse-positive or eligible-intervention frames.

Iteration 24 is therefore not a causal-intervention experiment. It is a data-support atlas. Its
job is to answer whether a **fresh**, non-evaluation nuScenes train subset contains enough
low-diversity hazardous frames and benign controls to justify a later causal-localization
pre-registration at all.

## Research question

Under a frozen fresh-scene manifest, frozen extraction surface, and frozen label family, does the
non-evaluation train pool contain enough low-diversity hazard support and benign controls for a
future causal-localization experiment?

Acceptable positive claim if every bar passes:

> A fresh non-evaluation nuScenes train subset has sufficient pre-registered low-diversity hazard
> and benign-control support to justify a separate causal-localization pre-registration.

Forbidden claims from this iteration, even on a pass:

- no claim about iteration-12 dangerous frames;
- no claim that a probe localizes a mechanism;
- no claim that an activation direction exists;
- no activation intervention, intervention alpha, selector-compatibility, or closed-loop claim;
- no claim that `low_diversity_1p5` is the same phenomenon as strict planner collapse;
- no claim that this support generalizes to VAD, other UniAD checkpoints, or other planners.

## Known-data firewall

The iteration-23 extraction and label counts are already known. Iteration 24 may use them only as
motivation for this new hypothesis and as excluded known data. They cannot contribute to any
iter24 pass bar.

The iter24 confirmatory universe must exclude:

- every NeuroNCAP official/evaluation scene;
- every iteration-12 evaluation scene identity;
- every scene name in committed iteration-22 manifests or extraction sidecars;
- every scene name in committed iteration-23 manifests or extraction sidecars.

If the resulting fresh scene pool is too small, publish an availability-null and stop. Do not
reuse iter22/iter23 scenes to rescue the gate.

## Frozen data and split discipline

Iteration 24 must create its own availability and split manifest after this hypothesis is
committed and before any model extraction.

- Source: official nuScenes train-split scene metadata plus local file-existence checks for the
  staged image/keyframe files only.
- Exclusions: the known-data firewall above. Scene identity may be used only for exclusion and
  split assignment. Iteration-12 labels, gaps, escapes, scores, per-frame evidence, and candidate
  proof artifacts are prohibited.
- Prohibited inputs: uncommitted iter19/iter21 scene lists, GPU shell history, remembered scene
  names, and post-hoc label counts are not sources of truth.
- Token hygiene: manifests must not commit nuScenes scene/sample tokens. Use scene names, sample
  indices, timestamps, counts, and hashes only.
- Availability manifest: commit the generator script, exact command, exclusion report,
  `availability_manifest.json`, and SHA256 digest before any GPU launch.
- Eligibility: each eligible scene must have at least 24 locally readable keyframes with all six
  cameras present.
- Availability bar before extraction: at least 48 fresh eligible scenes after exclusions, at
  least 1,200 planned keyframes, and at least 300 planned heldout keyframes. If any condition
  fails, publish an availability-null and stop before model extraction.
- Split rule: sort eligible scene names by SHA256 of `iter24:<scene_name>`, ascending. Assign
  the first 50% to `fit`, the next 25% to `calibration`, and the final 25% to `heldout`, rounding
  down for `fit` and assigning any remainder to `heldout`. No scene may move between splits after
  the manifest is committed.
- Frame order: within each scene, use nuScenes sample order. Every extraction row must include
  the split, scene name, zero-based sample index within that scene, and the original nuScenes
  sample timestamp in microseconds.

The iteration-12 corpus remains completely outside iteration 24. No exact join, dangerous-frame
inspection, selector scoring, or closed-loop run may touch iteration-12 unless a later Stage 2
pre-registration exists.

## Frozen extraction surface

Iteration 24 reuses the proven iteration-23 extraction design but must commit an iter24-namespaced
copy before any launch:

- hook site: immediately before `planning_head.forward(...)` in UniAD `inference/runner.py`;
- tensors: `outs_motion['sdc_traj_query']` and `outs_motion['sdc_track_query']`;
- logged planner outputs required for labels: executed plan `traj`, command candidates `cands`,
  object states `objs`, and future modes `futs`;
- join key: `(scene, sample_index, timestamp_us)`;
- intervention alpha: extraction rows must contain no intervention or `intervention_alpha = 0.0`.

No probe features may be fitted and no activation direction may be written in iteration 24.

## S0 integrity gates

Before the canary run, commit:

- availability/split manifest generator;
- extraction patch;
- feeder script;
- canary run script;
- full extraction run script;
- S0 analyzer;
- label-atlas analyzer;
- canonical JSONL hashing script or documented canonicalization routine.

The canary scene set is frozen by manifest order: the first scene in each split. Extract at most
five keyframes per canary scene. Run the canary twice from a clean model process.

Canary pass bars:

- exactly one GT row and one extraction row per served keyframe;
- 100% one-to-one join on `(scene, sample_index, timestamp_us)`;
- zero `missing_gt`, duplicate-key, missing-tensor, invalid-candidate-count, or tensor-shape
  error rows;
- identical canonical SHA256 for the two canary extraction outputs and the two GT sidecars;
- all primary tensor shapes stable within and across canary runs.

If any canary bar fails, publish an infrastructure null and stop before full extraction.

Only after canary pass may the full fresh manifest be extracted once.

Full S0 pass bars:

- extraction row count equals GT row count for non-reset rows;
- 100% one-to-one join on `(scene, sample_index, timestamp_us)`;
- zero error rows of any type;
- row counts by split and scene match the committed availability manifest, allowing only
  pre-declared image-read skips listed in the proof table;
- primary tensor shapes and dtypes are stable for every scored row;
- no extraction row contains an intervention alpha other than `0.0`;
- gzip artifacts validate locally and, if larger than 90 MB, are split into `.part-*` files before
  commit.

If full extraction integrity fails, publish an infrastructure/data-null and stop before label
support claims.

## Frozen label atlas

All labels are computed only from fresh iter24 non-evaluation extraction rows after S0 integrity
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

The primary iter24 support gate is `low_diversity_1p5` under `danger_4p5`, not
`strict_collapse_0p5`. Passing S1 authorizes only a later pre-registration. It does not authorize
probe fitting or interventions.

Minimum counts:

| split | required counts |
|---|---|
| fit | `low_diversity_1p5 >= 60`, `high_diversity_2p0 >= 60`, `danger_4p5 >= 60`, `safe_6p0 >= 60`, `eligible_lowdiv >= 20`, `benign_control >= 40` |
| calibration | `low_diversity_1p5 >= 20`, `high_diversity_2p0 >= 20`, `danger_4p5 >= 20`, `safe_6p0 >= 20`, `eligible_lowdiv >= 8`, `benign_control >= 15` |
| heldout | `low_diversity_1p5 >= 20`, `high_diversity_2p0 >= 20`, `danger_4p5 >= 20`, `safe_6p0 >= 20`, `eligible_lowdiv >= 8`, `benign_control >= 15` |

Distribution bars:

- fit `eligible_lowdiv` frames must come from at least 5 scenes;
- calibration `eligible_lowdiv` frames must come from at least 2 scenes;
- heldout `eligible_lowdiv` frames must come from at least 2 scenes;
- no single scene may contribute more than 40% of heldout `eligible_lowdiv` frames.

If any S1 count or distribution bar fails, publish a support-null and stop. Do not move scenes,
relax thresholds, merge splits, or relabel frames.

## Optional strict-collapse support note

If the stricter labels also satisfy these counts, the result may state that strict-collapse
support exists:

| split | required strict counts |
|---|---|
| fit | `strict_collapse_0p5 >= 30`, `eligible_strict >= 10` |
| calibration | `strict_collapse_0p5 >= 10`, `eligible_strict >= 4` |
| heldout | `strict_collapse_0p5 >= 10`, `eligible_strict >= 4` |

Failure of this optional strict note does not fail S1. It only limits the language of any later
experiment: a successor may not call the selected frames "strict collapse" unless these strict
counts pass.

## Named falsifiers

- **Fresh availability unsupported.** Fewer than 48 fresh eligible scenes, fewer than 1,200
  planned keyframes, or fewer than 300 planned heldout keyframes exist under the frozen
  firewall.
- **Known-data contamination.** Any iter22, iter23, NeuroNCAP, or iteration-12 scene enters the
  confirmatory manifest.
- **Join key invalid.** Canary or full extraction fails the `(scene, sample_index, timestamp_us)`
  one-to-one join.
- **Extraction nondeterminism.** Canary canonical SHA256 digests differ, tensor shapes drift, or
  error rows appear.
- **Support absent.** S1 minimum counts fail.
- **Support concentrated.** S1 distribution bars fail, showing support is a small scene artifact.
- **Strict collapse absent.** The optional strict-collapse counts fail; this does not kill S1 but
  forbids strict-collapse language in successors.
- **Protocol breach.** Any use of iteration-12 outcomes, hidden scene search, hidden threshold
  search, heldout retuning, post-data split movement, or use of iter22/iter23 rows in
  confirmatory counts voids the result.
- **Overclaim attempt.** Any RESULT language that treats support counts as mechanism evidence,
  probe evidence, causal evidence, or deployable plan-B recovery must be corrected before
  publication.

## Required proof artifacts

Before any GPU launch:

- this `HYPOTHESIS.md`;
- availability/split manifest generator, manifest, exclusion report, command record, and SHA256;
- extraction patch, feeder, canary/full extraction run scripts, S0 analyzer, label-atlas
  analyzer, and canonical hashing routine.

With the RESULT:

- raw canary logs, full extraction logs, and JSONL/gzip artifacts;
- canonical SHA256 table for canary runs and full extraction artifacts;
- split/scene/frame availability table and actual row-count table;
- firewall exclusion table listing iter22/iter23/NeuroNCAP/iteration-12 exclusions by scene name;
- join-integrity report with error-type counts even if zero;
- tensor shape/dtype summaries;
- label counts by split and by scene for every label above;
- count and distribution bar report, including failures;
- exact command lines for every artifact;
- claim-boundary paragraph in `RESULT.md`.

## Protocol

1. Commit this hypothesis.
2. Commit the manifest generator and extraction/analysis surface before any GPU launch.
3. Generate and commit the availability manifest before any model extraction.
4. Run the two-run canary only if the availability bar passes.
5. Run full extraction only if the canary passes.
6. Compute the label atlas only if full S0 passes.
7. Publish the result at full weight whether S1 passes or fails.
8. A pass authorizes only a separate successor pre-registration. It does not authorize probe
   fitting, activation intervention, iteration-12 scoring, selector evaluation, or closed-loop
   evaluation.
