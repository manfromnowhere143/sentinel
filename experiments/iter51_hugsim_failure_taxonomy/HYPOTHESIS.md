# Iteration 51 - HUGSIM transfer-failure taxonomy pre-registration

Frozen before any iteration-51 analyzer, proof table, aggregate taxonomy, result, or claim.
Committed alone. This is an entirely offline post-result audit over committed HUGSIM proof
artifacts only: zero GPU work, zero gcloud commands, zero box reads, zero new simulator
launches, and zero monitor retuning.

## Research question

Iterations 48 and 49 answered the transfer question for the released union: the byte-identical
NeuroNCAP-frozen monitor fires, latches, and releases on HUGSIM, and collision opportunity is
present, but the paired HD-Score benefit does not measurably transfer. Iteration 50 then made
the key boundary sharper: iteration 49 had primary collision opportunity in `51/52` OFF
episodes, so the failure is real, not opportunity-scarce.

This audit asks the next narrower question: **what kind of HUGSIM failure did the released union
produce?** It classifies each paired HUGSIM episode into a frozen taxonomy using only committed
episode metrics and ON-arm decision logs. The output is mechanism triage for the next
pre-registration, not a new safety, transfer, robustness, or benchmark claim.

## Disclosed pre-registration knowledge

This is not a blind experiment. It is a post-result audit after iterations 48, 49, and 50 were
published. The following facts are already on the record and may motivate the taxonomy:

- iteration 48 verdict `TRANSFER_NULL`, mean paired HD delta `-0.0166`, CI
  `[-0.0551, +0.0255]`, 37/52 ON episodes intervened;
- iteration 49 verdict `TRANSFER_NULL`, mean paired HD delta `-0.0089`, CI
  `[-0.0438, +0.0203]`, 40/52 ON episodes intervened;
- iteration 50 P1 resolution: 51/52 iteration-49 OFF episodes had primary collision
  opportunity, Branch B REFUTED;
- structure-only and spot inspections before this file: `eval.json` has top-level
  `hdscore`, `nc`, `dac`, `ttc`, `c`, `pdms`, `rc`, and `details`; ON decision JSONL rows have
  `frame_index`, `ts`, `fired`, `brake`, `release`, `min_ttc`, `min_cpa`, `objs`, `traj`, and
  frozen `params`; one fired iter49 row showed the monitor can fire with nonempty object rows.

No iteration-51 aggregate category counts, first-collision timing distribution, first-brake
timing distribution, or taxonomy summary has been computed before this freeze.

## Frozen evidence inputs

Committed artifacts only:

- `experiments/iter48_hugsim_transfer_gate/proof-stage2/episodes/`
- `experiments/iter48_hugsim_transfer_gate/proof-stage2/transfer_report.json`
- `experiments/iter49_hugsim_hard_tier_gate/proof-hard/episodes/`
- `experiments/iter49_hugsim_hard_tier_gate/proof-hard/transfer_report.json`
- `experiments/iter50_collision_opportunity_audit/proof-audit/p1_opportunity_report.json`
  for the already-published P1 count cross-check only.

The analyzer must not read the GPU box, staged scenario YAMLs, uncommitted files, external
sources, or any future experiment directory.

## Frozen per-pair fields

Unit: one paired episode, `(scenario, run)`, with OFF `eval.json`, ON `eval.json`, and ON
`sentinel_iter48_decisions.jsonl`.

**OFF/ON collision opportunity.** For each arm, compute `nc_min` as the minimum of top-level
`nc` and every numeric `details.<t>.nc`. Primary collision opportunity/collision is
`nc_min < 1.0`, exactly matching iteration 50. Record the first details timestamp where
`nc < 1.0` as `first_nc_time`. If only the top-level value is below 1.0 and no details row is,
record `first_nc_time = null` and set `first_nc_source = "top_level_only"`.

**Timing proxy.** ON intervention timing is `first_brake_ts`, the first decision row with
`brake == true`; `first_fire_ts` is also recorded. This is a descriptive timing proxy only:
OFF and ON trajectories are stochastic and not frame-identical, so the audit may say "late by
proxy" but may not claim causal lateness.

**Outcome.** `delta_hd = hd_on - hd_off`. A fixed materiality deadband
`MATERIAL_HD_BAR = 0.03` is used only for descriptive flags. Rationale: it is the published
iteration-48 fresh OFF-OFF median absolute spread rounded down to two significant digits
(`0.0307`). It does not define a transfer verdict.

## Frozen primary taxonomy

The categories are mutually exclusive and assigned in this order:

1. `induced_collision`: OFF has no primary collision opportunity and ON has primary collision.
2. `clean_no_off_opportunity`: OFF has no primary collision opportunity and ON has none.
3. `converted_collision_material_gain`: OFF has primary collision opportunity, ON has none,
   and `delta_hd > +0.03`.
4. `converted_collision_no_material_gain`: OFF has primary collision opportunity, ON has none,
   and `delta_hd <= +0.03`.
5. `persistent_collision_no_brake`: OFF and ON both have primary collision, and ON has zero
   brake frames.
6. `persistent_collision_late_by_proxy`: OFF and ON both have primary collision, ON has brake
   frames, and `first_brake_ts` is either missing or greater than OFF `first_nc_time`.
7. `persistent_collision_early_by_proxy`: OFF and ON both have primary collision, ON has brake
   frames, and `first_brake_ts <= first_nc_time`.

If required fields are missing or nonnumeric, publish `TAXONOMY_INFRASTRUCTURE_NULL` and stop
before any mechanism interpretation.

## Frozen summaries and bars

The result reports the category counts over:

- iteration 48 easy+medium pairs (`52`);
- iteration 49 hard/extreme pairs (`52`);
- the combined HUGSIM transfer corpus (`104`);
- OFF-opportunity pairs only;
- iteration 49 `AttackPlanner` scenarios vs non-`AttackPlanner` scenarios, using the schedule
  facts already frozen in iteration 49: all extreme scenarios plus `scene-0041-hard-00` and
  `scene-0411-hard-00`.

**Dominance label.** If one category covers at least `40%` of OFF-opportunity pairs in the
combined corpus, name it as `dominant_category`; otherwise report `mixed_taxonomy`. This is a
triage label only; it is not a statistical claim and cannot upgrade either transfer null.

**Secondary flags, descriptive only:**

- `material_gain`: `delta_hd > +0.03`;
- `material_loss`: `delta_hd < -0.03`;
- `score_loss_under_brake`: ON has at least one brake frame and `material_loss`;
- `converted_collision`: OFF primary collision and ON no primary collision;
- `persistent_collision`: OFF primary collision and ON primary collision;
- `late_by_proxy`: OFF primary collision, ON has brake frames, and `first_brake_ts` is missing
  or greater than OFF `first_nc_time`.

## Forbidden claims

No new safety, transfer, deployment, robustness, benchmark-ranking, real-world, or
monitor-performance claim. This audit may only say how the published HUGSIM nulls decompose
under the frozen taxonomy. It cannot retune the released union, cannot reopen iteration 48 or
49, cannot claim HUGSIM equivalence, and cannot select a new rule family without a later fresh
pre-registration.

## Required proof artifacts

- analyzer source and unit tests;
- `proof-taxonomy/failure_taxonomy_report.json`;
- `proof-taxonomy/failure_pairs.md`;
- `proof-taxonomy/analyze_failure_taxonomy.command.txt`.

## Protocol

1. Commit this `HYPOTHESIS.md` ALONE.
2. Add and commit analyzer/tests; run `ruff check .`, `pytest -q`, and
   `python3 scripts/validate_docs.py`.
3. Run the analyzer ONCE over committed inputs.
4. Publish `RESULT.md` at full weight: either `TAXONOMY_COMPLETE` or
   `TAXONOMY_INFRASTRUCTURE_NULL`.
5. Update README, CONTINUITY, HANDOFF, and push.
