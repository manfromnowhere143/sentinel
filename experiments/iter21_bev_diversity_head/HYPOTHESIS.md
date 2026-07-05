# Iteration 21 — BEV-conditioned diversity head: pre-registration (offline stage first)

Frozen before any extraction, training, replay, or GPU work for this iteration. This is the
surviving variant named by iteration 19, not a retune of the failed planning-query head.

## Why this line exists

The campaign has now measured the plan-B deficit three ways:

- UniAD's command-conditioned candidates collapse under threat: **0/37** dangerous frames have
  an escape candidate ([iteration 12](../iter12_plan_selection/RESULT.md)).
- VAD's native modes retain only partial threat diversity: **21%**, below the frozen 30% bar
  ([VAD transfer](../vad_generalization/RESULT.md)).
- A trained K=8 head conditioned on UniAD's own planning-query embeddings is faithful on benign
  frames but yields **0/37 feasible escapes**; every diverging candidate is kinematically
  infeasible ([iteration 19](../iter19_diversity_head/RESULT.md)).

Iteration 19's falsifier fired exactly: the planner's planning-query representation no longer
contains feasible alternatives under threat. The remaining question is sharper and more
expensive: does feasible-alternative information exist earlier in the frozen planner's
scene-level BEV representation, before the planning state collapses?

## Mechanism

A BEV-conditioned candidate head, with the frozen planner untouched, emits K=8 alternative ego
trajectories over the planner horizon. The released union's label-free risk score is only the
future selector; it is not a training label. The committed stop remains the safety floor.

Frozen design choices:

- **Conditioning signal:** scene-level BEV features from the frozen UniAD inference graph,
  extracted before the final planning-query bottleneck, plus ego kinematics. The exact tensor
  names and hook points will be documented in the extraction patch when built. Planning-query
  embeddings alone are not an allowed conditioning path in this iteration.
- **Compression:** a small spatial encoder over BEV tokens or feature maps, followed by a
  recurrent/attention trajectory decoder. Parameter count **<= 15M**.
- **Outputs:** K=8 candidate trajectories on the same horizon and coordinate frame as the
  planner's executed trajectory.
- **Training objective:** winner-takes-all imitation to logged future, inter-candidate
  repulsion, and an explicit feasibility regularizer on curvature, acceleration, and first-step
  continuity. Diversity that is infeasible is a null by design.
- **Data discipline:** training data only from nuScenes train-split scenes disjoint from every
  NeuroNCAP evaluation scene and disjoint from the iteration-12 dangerous-frame corpus. The
  iteration-12 frame corpus is **evaluation-only**. Any training, hyperparameter selection, or
  architecture choice using those frames voids the result.

## Offline gate — bars frozen now

Evaluated on the committed iteration-12 corpus with iteration-12 definitions: dangerous means
executed-plan closest approach < 3.5 m; escape means a candidate closest approach > 5.0 m.
Counts are over the same 37 dangerous frames unless stated otherwise.

- **B0 — extraction integrity:** evaluation extraction must join the committed iteration-12
  frames exactly, with zero executed-plan mismatches against the committed candidate log. A
  broken join, missing dangerous frame, or changed executed plan fails the gate before model
  scoring.
- **B1 — feasible escape rate:** at least **12/37** dangerous frames (>30%) contain a feasible
  escape candidate. Feasible escapes must satisfy B2 and are reported with a binomial interval.
- **B2 — candidate feasibility:** every candidate counted by B1 respects
  `|curvature| <= 0.2 1/m`, `|accel| <= 4 m/s^2`, and first-step continuity with the ego state.
  Across all evaluation frames, at least **90%** of emitted candidates must satisfy those same
  limits. If the head buys diversity with invalid trajectories, the gate fails.
- **B3 — benign fidelity:** on benign frames of the same corpus, best-of-K displacement error to
  the executed plan must be **<= 0.780 m** (the iteration-19 bar, unchanged).
- **B4 — selector compatibility:** among dangerous frames where B1 finds a feasible escape, the
  released-union risk score must rank a feasible escape ahead of the executed plan in at least
  **75%** of those frames. A candidate set the label-free selector cannot choose is not a
  deployable plan B.

**Gate rule:** B0 through B4 must all pass before any closed-loop pre-registration. If any bar
fails, the null publishes at full weight and no GPU closed-loop run launches from this
hypothesis.

## Falsifiers, named up front

- **BEV also lacks the missing plan B.** If B1 fails, the representation-level collapse extends
  earlier than planning queries for this mechanism and evidence.
- **Diversity remains physically invalid.** If B1 fails because candidates diverge but B2
  rejects them, iteration 19's infeasible-divergence failure reproduced under richer
  conditioning.
- **Faithful but not safety-useful.** If B3 passes while B1 fails, the head learned ordinary
  driving but not threat-conditioned alternatives.
- **Selector mismatch.** If B1/B2 pass but B4 fails, the candidate source is not enough: the
  external geometric risk score cannot pick the alternative it needs.
- **Storage/engineering bottleneck.** If BEV extraction cannot be made deterministic and
  git-sized under the campaign evidence rules, the result publishes as an infrastructure null,
  not as evidence for or against the mechanism.
- **Small evaluation corpus.** The 37 dangerous frames are few. The guard is fixed: no training
  or tuning touches them, the gate reports exact counts and intervals, and any closed-loop
  stage must be separately pre-registered on unseen deterministic episodes.

## Protocol

1. Commit this `HYPOTHESIS.md`.
2. Build and commit the BEV extraction patch and run script before running extraction.
3. Extract train-split BEV features and logged futures; commit proof logs and git-sized
   artifacts or documented part files.
4. Train the head; commit config, training log, and checkpoint.
5. Build and commit the offline gate harness before running it.
6. Run the gate once from committed artifacts; commit stdout under `proof-gate/` and publish
   `RESULT.md`, pass or fail.
7. Only if the offline gate passes, write a separate closed-loop pre-registration with arms,
   bars, and falsifiers before any closed-loop GPU run.
