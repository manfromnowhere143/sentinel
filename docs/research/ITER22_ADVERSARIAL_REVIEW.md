# Iteration 22 adversarial review - causal planner interpretability draft

Status: planning-only review. This file does not authorize extraction, probe training,
activation patching, GPU work, gcloud access, closed-loop evaluation, commits, or creation of
`experiments/iter22_*`.

Reviewer stance: skeptical ML safety / mechanistic interpretability reviewer. The draft is
scientifically promising, but it currently tries to compress localization, causal intervention,
plan-B recovery, feasibility, selector compatibility, and deployment gating into one offline
experiment. That creates too many hidden degrees of freedom for the result to be clean.

## Major concerns

### 1. Leakage risk is still too high

The draft correctly keeps the 311 iteration-12 frames evaluation-only, but it still makes those
frames central to A0, A4, A5, A6, A7, and A8. Even if no training touches them, the experimenter
could iteratively improve tensor choice, intervention form, and patch magnitude by looking at
which iter12 bars fail. That is practical leakage.

The strongest fix is procedural: Stage 1 should never run on the iter12 corpus. Stage 1 should
freeze the split manifest, tensor list, labels, probe family, intervention grid, and evidence
format using non-evaluation scenes only. Iter12 should enter only in Stage 2, after Stage 1
publishes its result and freezes one intervention.

The draft also says iter22 must create its own split manifest, which is right. The real
pre-registration should add an explicit prohibition on using uncommitted iter19/iter21 scene
lists, logs, shell history, or remembered scene names as split inputs.

### 2. A0-A8 is too much for one experiment

A0-A8 mixes at least four claim types:

- representation localization: A1 and A2;
- causal effect inside the planner: A3 and A4;
- physical plan-B recovery: A5 and A6;
- deployability through the released selector: A7 and A8.

This invites ambiguous outcomes. For example, A1/A2/A3 could pass while A5/A8 fail; that would
be a meaningful mechanistic result, but the all-bars gate would label the whole experiment as a
failure. Conversely, a marginal A5 result could distract from weak localization.

Top-tier reviewers will ask: what is the single claim of iter22? If the answer is causal
interpretability, selector compatibility belongs in a later deployability stage. If the answer
is plan-B recovery, the probe work is not sufficient evidence.

### 3. Missing minimum positive-count rules

A1 and A2 use AUC, AP multiples, and balanced accuracy without requiring enough positives per
split. That is brittle. AUC can look strong with very few positive frames, and AP at `2.0x` base
rate is weak when base rate is tiny.

The real hypothesis needs minimum counts before scoring, for example:

- at least 30 high-risk positives and 30 low-risk controls in heldout for danger localization;
- at least 30 collapsed and 30 high-diversity frames in heldout for collapse localization;
- at least 20 eligible high-risk heldout frames and 20 low-risk controls for intervention
  scoring.

If the split cannot supply those counts, publish an infrastructure/data-null rather than
relaxing thresholds.

### 4. The intervention grid is underspecified

"Mean-substitution, donor activation patching, or scalar ablation from a pre-declared grid" is
not enough. The grid itself is the intervention. Without exact details, the operator can tune
by trying variants until one moves the desired metric.

The hypothesis should freeze:

- tensor names and hook sites;
- patch timing relative to planner forward pass;
- whether patching is per-frame, per-token, per-query, or pooled;
- donor pool construction and exclusion rules;
- exact scalar values, for example `alpha in {-1.0, -0.5, 0.0, 0.5, 1.0}`;
- selection rule for choosing one grid cell from calibration;
- tie-breaking rule;
- maximum number of attempted failed implementation variants before the protocol is void or
  restarted with a new pre-registration.

Without this, the causal claim is vulnerable to hidden search.

### 5. Probe-equals-explanation risk remains

The draft says a probe is not an explanation, but A1/A2 still occupy a large part of the gate.
A linear probe can exploit correlates of scene type, frame timing, velocity, object count, or
episode phase. That would not locate the mechanism that causes candidate collapse.

At minimum, the proof plan should include negative controls:

- ego-kinematics-only probe;
- scene/run metadata probe if metadata is available;
- shuffled-label probe with the same split;
- late-output probe separated from internal-state probes.

The result should be forbidden from saying "the representation contains the cause" from probe
success alone. Acceptable language: "this tensor carries linearly decodable information about
the frozen label under this split."

### 6. Causal claims are unclear

A3 and A4 define causal movement using candidate spread and closest-gap movement, but it is not
clear whether the intervention changes the model's internal causal pathway or simply corrupts a
state enough to increase variance. More spread is not necessarily more causal understanding.

The causal claim should be narrower:

- "Under a frozen intervention at tensor T, changing activation component C changes downstream
  candidate geometry while preserving benign controls."

It should not claim:

- where the planner "loses alternatives" globally;
- that the intervention recovered the planner's latent plan B;
- that the tensor is the cause rather than part of a causal path.

### 7. Some bars are broad, weak, or misaligned

A3 uses "predicted direction" and "pre-declared high-risk heldout frames" without defining the
direction, eligibility, or minimum count. This is too flexible.

A4 requires spread and closest-gap movement in `12/37`, but movement is weaker than plan-B
recovery. A model can increase spread by producing physically invalid or irrelevant paths.

A7 uses median endpoint displacement on benign frames. A median can hide tail failures; the
bar should also bound a high percentile or exact count of large benign degradations.

A8 uses selector compatibility only after A5 succeeds. That is reasonable for deployability,
but it makes the experiment depend on a risk-score system that is not part of the causal
interpretability claim.

### 8. Artifact and proof gaps

The proof plan is directionally right but should require more audit detail:

- exact split manifest and generator script, not just the manifest;
- all exclusion matches against NeuroNCAP and iter12 scene/frame identities;
- hash of the UniAD source tree or exact commit plus diff for extraction/patch hooks;
- tensor-shape, dtype, and row-count summaries for every extracted tensor;
- per-grid-cell calibration metrics, including failed cells, to prove no unreported search;
- negative-control probe outputs;
- per-frame intervention eligibility decisions;
- deterministic rerun evidence for a small extraction subset before full extraction;
- exact command lines used for every artifact.

Without failed-grid and negative-control artifacts, the result can accidentally look more
targeted than it was.

### 9. Result could overclaim even if all bars pass

Even a full A0-A8 pass would establish only that one frozen intervention on one model and one
corpus changes offline candidate geometry under fixed rules. It would not establish:

- general mechanistic understanding of UniAD;
- that the model internally had a human-legible alternative plan;
- that plan-B failure is solved;
- that the intervention is safe in closed loop;
- that the same mechanism holds for VAD or other planners.

The `RESULT.md` should be required to include a claim-boundary paragraph before any positive
interpretation.

## Recommended tighter Stage 1-only iter22

- **Objective:** Establish whether a pre-declared frozen UniAD tensor carries a stable,
  low-capacity diagnostic signal for danger/candidate collapse and whether one pre-declared
  simple intervention causally changes downstream candidate geometry on non-evaluation heldout
  scenes. Do not touch the iteration-12 corpus in Stage 1.

- **Offline bar S0 - split and extraction integrity:** Iter22 creates and commits its own
  split manifest before extraction. The heldout split must contain at least 30 danger positives,
  30 safe controls, 30 collapsed frames, and 30 high-diversity controls under frozen labels.
  Extraction must produce exact row counts, tensor shapes, source hash, and deterministic
  subset rerun evidence. If counts are insufficient, Stage 1 stops as a data-null.

- **Offline bar S1 - low-capacity localization:** On heldout non-evaluation scenes, one
  pre-declared linear/logistic probe for danger or collapse reaches AUC `>= 0.80`, balanced
  accuracy `>= 0.70`, and beats ego-kinematics-only and shuffled-label controls by at least
  `0.10` AUC.

- **Offline bar S2 - frozen intervention effect:** Using one intervention selected from the
  pre-registered calibration grid, heldout high-risk frames show candidate endpoint-spread
  movement in the pre-declared direction on at least `60%` of eligible frames, with median
  spread change `>= 0.75 m`. Eligibility and direction must be frozen before calibration.

- **Offline bar S3 - benign control:** On heldout low-risk controls, median executed-plan
  endpoint displacement must be `<= 0.780 m`, 95th percentile displacement must be `<= 1.5 m`,
  and no more than `5%` of controls may cross the frozen danger threshold after intervention.

- **Named falsifiers:** no stable localized signal; metadata/kinematics control explains the
  signal; diagnostic but not causal; causal but nonspecific corruption; benign harm; inadequate
  positive counts; extraction nondeterminism; protocol breach.

- **Explicit stop condition:** If S0, S1, S2, or S3 fails, publish a Stage 1 null and stop. Do
  not run the iteration-12 gate, do not tune the tensor or grid, do not create a candidate head,
  and do not write a closed-loop pre-registration.

- **Deferred to Stage 2:** iteration-12 exact join, feasible-escape recovery, iteration-21
  physical-validity gate, released-union selector compatibility, per-frame proof dump over all
  311 iter12 frames, and any closed-loop claim. Stage 2 must be a separate pre-registration
  that freezes the single Stage 1 tensor and intervention before touching iter12 frames.
