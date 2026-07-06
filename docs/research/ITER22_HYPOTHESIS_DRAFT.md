# Iteration 22 - causal planner interpretability: proposed hypothesis draft

Status: planning-only draft. This file is not a frozen experiment pre-registration and does
not authorize data extraction, probe training, activation patching, GPU work, gcloud access,
closed-loop evaluation, commits, or creation of `experiments/iter22_*`.

If this draft is promoted, the real pre-registration should live in a new experiment directory
and be committed before any data is touched.

## Research question

Where, causally, does frozen UniAD lose feasible plan-B alternatives under threat?

The hypothesis is that candidate collapse is controlled by a localized internal planner state:
low-capacity probes should find a stable danger/collapse signal on heldout non-evaluation
scenes, and a frozen activation intervention at that state should change candidate diversity or
risk under the same iteration-12 rulers. The line succeeds only if the effect is causal and
physically valid. A probe that predicts danger without changing planner outputs is a diagnostic
result, not an explanation.

## Proposed mechanism

Inspect a small, pre-declared tensor set from the frozen UniAD inference graph:

- scene-level BEV features before the planning-query bottleneck;
- motion/planning bridge tensors such as `sdc_track_query` and `sdc_traj_query`;
- the planning-query representation used by iteration 19;
- planning-head state immediately before trajectory projection.

The final hypothesis must verify exact source names against committed UniAD code and extraction
patches before any run. No post-hoc layer search is allowed after seeing evaluation effects.

Allowed models and interventions are deliberately weak:

- linear or logistic probes with L2 regularization;
- optional PCA or mean-pooling fitted on the fit split only, with at most 16 components per
  tensor;
- mean-substitution, donor activation patching, or scalar ablation from a pre-declared grid;
- no learned intervention, decoder head, fine-tuning, or threshold selected from iter12 frames.

## Exact data and split discipline

Final evaluation set: the committed iteration-12 candidate corpus,
`experiments/iter12_plan_selection/proof/sentinel_cand.jsonl.gz`.

- Evaluation corpus size is frozen at 311 frames.
- Dangerous frames are exactly those where the executed plan's closest predicted gap is
  `< 3.5 m`; the expected count is 37.
- Benign control frames are the remaining 274 frames.
- Escape means a candidate closest approach `> 5.0 m` and better than the executed plan.
- Feasibility uses the iteration-21 limits: `|curvature| <= 0.2 1/m`, `|accel| <= 4 m/s^2`,
  and first-step continuity with the ego state.
- These 311 frames are evaluation-only. They cannot be used for probe fitting, PCA fitting,
  tensor choice, hyperparameter choice, patch-amplitude choice, donor selection, threshold
  tuning, or deciding whether to rerun a gate.

Non-evaluation causal-atlas data must be frozen before extraction in the real iter22
pre-registration:

- Source: nuScenes train-split scenes only, disjoint from every NeuroNCAP evaluation scene and
  disjoint from the iteration-12 frame corpus.
- Manifest: iter22 must create its own split manifest from nuScenes metadata and commit it
  before any extraction. The manifest must list exact scene names, split assignment, exclusion
  checks against NeuroNCAP and iteration-12 evaluation scenes, and a SHA256 digest. Prior
  iter19/iter21 train scene lists are not a source of truth unless a committed manifest is
  later found.
- Split: sort the committed scene names lexicographically, then assign the first 40 scenes to
  `fit`, the next 10 to `calibration`, and the final 10 to `heldout`.
- Fit split: fit PCA/normalizers, train low-capacity probes, and build donor activation
  centroids.
- Calibration split: choose at most one tensor, one probe family, one patch family, and one
  patch magnitude from the pre-declared grid.
- Heldout split: report non-evaluation probe and intervention metrics once, before the iter12
  gate.
- Iter12 split: run the final offline gate once from committed artifacts.

Any use of iter12 frames before the final gate voids the result.

## Numeric offline bars

All bars are frozen for the proposed hypothesis. A promoted pre-registration may simplify them,
but it must not relax them after data.

| bar | requirement |
|---|---|
| A0 extraction integrity | Final evaluation extraction joins 311/311 iter12 frames, finds exactly 37 dangerous frames, and has zero executed-plan mismatches against the committed iter12 log. Missing frames, changed plans, or a different danger count fail before scoring. |
| A1 heldout danger localization | On the 10-scene heldout non-evaluation split, a linear/logistic probe for `closest_gap < 3.5 m` reaches AUC `>= 0.80` and average precision at least `2.0x` the heldout positive base rate. |
| A2 heldout collapse localization | On the heldout split, a low-capacity probe for candidate collapse reaches AUC `>= 0.85` and balanced accuracy `>= 0.75`. Collapse is frozen as command-candidate endpoint spread `< 0.5 m`; high-diversity control is spread `>= 2.0 m`. Ambiguous frames are excluded before labels are counted. |
| A3 non-eval causal screen | On pre-declared high-risk heldout frames, the chosen intervention changes candidate endpoint spread in the predicted direction on `>= 60%` of frames and increases median spread by `>= 0.75 m`, while low-risk heldout controls have median executed-plan endpoint displacement `<= 0.780 m`. |
| A4 iter12 causal movement | On the 37 dangerous iter12 frames, the intervention increases command-candidate endpoint spread by `>= 1.0 m` in at least `12/37` frames and increases the best candidate closest gap by `>= 0.5 m` in at least `12/37` frames. |
| A5 feasible escape recovery | At least `12/37` dangerous iter12 frames contain a feasible escape candidate under the patched run. This is the iteration-12 `>30%` viability bar expressed as an exact count. |
| A6 physical validity | Every candidate counted by A5 passes the iteration-21 feasibility limits, and at least `90%` of all emitted patched candidates across the 311-frame evaluation corpus pass those limits. Invalid diversity is a null. |
| A7 benign control | On the 274 benign iter12 frames, the same frozen intervention creates at most `13/274` new dangerous frames (`<5%`), keeps median executed-plan endpoint displacement `<= 0.780 m`, and worsens closest gap by `>1.0 m` in at most `5` frames. |
| A8 selector compatibility | Among dangerous frames where A5 finds a feasible escape, the released-union risk score ranks a feasible escape ahead of the executed plan in at least `75%` of those frames. If A5 finds fewer than 12 feasible escapes, A8 fails automatically. |

## Named falsifiers

- **No localized signal.** A1 or A2 fails on heldout non-evaluation scenes. Publish that this
  probe family did not find a stable representation.
- **Diagnostic but not causal.** A1/A2 pass, but A3 or A4 fails. The signal predicts collapse
  but does not control planner outputs under the frozen intervention.
- **Causal but not a plan B.** A4 passes, but A5 fails. The intervention moves trajectories
  without recovering feasible alternatives.
- **Invalid-diversity replay.** A5 nominally improves but A6 fails, reproducing the iteration-19
  and iteration-21 pattern of infeasible divergence.
- **Benign harm.** A7 fails. The intervention is not selective enough for a deployable monitor
  path even if it helps dangerous frames.
- **Selector mismatch.** A5/A6 pass but A8 fails. The external released-union risk score cannot
  choose the recovered feasible alternative.
- **Brittle causal effect.** Effects pass on calibration but fail on heldout or iter12, showing
  scene-specific tuning rather than a stable mechanism.
- **Storage or determinism failure.** Activations, candidate logs, or intervention outputs cannot
  be extracted deterministically and committed under the proof rules.
- **Protocol breach.** Any fitting, tensor selection, thresholding, donor choice, rerun decision,
  or architecture choice uses iter12 evaluation frames before the final gate. The result is void.

## Proof artifact plan

If promoted to a real experiment, commit these artifacts before and after each stage:

- pre-registered `HYPOTHESIS.md` and split manifest with exact scene names, split assignment,
  and SHA256 digest;
- extraction patch and run scripts naming the exact UniAD tensors and printing a patch marker;
- raw activation summaries, candidate logs, and ground-truth sidecars under proof directories,
  split into `.part-*` files if any artifact exceeds the repository size budget;
- probe config, training log, coefficient/checkpoint artifact, heldout metrics, and the frozen
  tensor/patch choice made from calibration only;
- intervention harness with the frozen patch specification, donor-selection rule, and random
  seeds if any deterministic sampling is used;
- per-frame final-gate dump for all 311 iter12 frames containing unpatched and patched
  candidates, closest gaps, endpoint spread, feasibility flags, released-union risk scores, and
  selector outcome;
- `gate_output.txt` with A0-A8 counts and intervals, plus a one-command reproducer;
- `RESULT.md` publishing pass or null at full weight.

Every number in `RESULT.md` must regenerate from committed proof artifacts. No raw secrets,
credentials, live account state, or gcloud output belongs in the evidence.

## No-closed-loop-until-gate rule

No closed-loop run is authorized by this draft. In a promoted iter22 experiment, A0 through A8
must all pass from committed offline artifacts, and the offline `RESULT.md` must be committed
first. Only then may the next operator write a separate closed-loop pre-registration with arms,
numeric bars, and named falsifiers. If any offline bar fails, the null publishes and no
closed-loop GPU run is launched from this hypothesis.
