# Iteration 54 - HUGSIM provenance support audit

Frozen before any iteration-54 analyzer, proof artifact, result, or claim. Committed alone.
This is an offline support audit over committed HUGSIM proof only: zero GPU work, zero gcloud
commands, zero box reads, zero simulator launches, zero monitor retuning, and zero external data.

## Process disclosure

This is not blind. Iterations 48-53 are already published. Before freezing this file, four
pre-registration inspections were performed:

1. Read `docs/NEXT_PHASE.md` and `HANDOFF.md` to recover the post-iteration-53 successor rule.
2. Listed the committed iteration-48/49 HUGSIM proof episode files.
3. Inspected one ON decision-log row and one HUGSIM `eval.json` schema row.
4. Read the committed iteration-48 HUGSIM client patch to confirm how `min_cpa` and `min_ttc`
   were computed and what was logged.

Those inspections showed that decision rows contain object IDs, object world positions,
velocities, ego pose transforms, ego plan trajectories, and scalar `min_cpa` / `min_ttc`, but
they do not explicitly log the argmin object. The sample `eval.json` contains scalar HUGSIM
metric fields, not an obvious collision actor ID. These inspections are disclosed rather than
hidden. This audit therefore makes no inferential surprise claim and uses no statistical
pass/fail bar.

## Research question

Iteration 53 showed that pre-collision-fire HUGSIM failures split across both sides of the
released union, so the next mature question is object/path provenance rather than threshold
retuning.

This audit asks the narrower support question:

**Do the committed iteration-48/49 HUGSIM artifacts support reconstructing the monitor-side first
hazard object/path, and do they support matching that hazard to the actual HUGSIM collision actor?**

The audit can publish a support null. A support null is valuable: it defines the exact missing
instrumentation before any new HUGSIM run.

## Frozen evidence inputs

Committed artifacts only:

- `experiments/iter48_hugsim_transfer_gate/proof-stage2/episodes/`
- `experiments/iter49_hugsim_hard_tier_gate/proof-hard/episodes/`
- `experiments/iter53_hugsim_first_fire_channel_audit/proof-channel/first_fire_channel_report.json`
  for pair-count and first-fire-channel cross-checks only.

The analyzer must not read the GPU box, staged scenario YAMLs, uncommitted files, external
sources, future experiment directories, rendered images, or simulator output directories outside
the committed proof trees.

## Frozen unit and fields

Unit: one ON-arm HUGSIM paired episode, `(dataset, scenario, run)`.

For each ON episode:

- read ON `eval.json`;
- read `sentinel_iter48_decisions.jsonl` if present;
- identify the first decision row with `fired == true`;
- reconstruct the monitor-side candidate that produced the first-fire scalar(s):
  - CPA reconstruction: transform each local ego-plan point into world coordinates using
    `l2g_r_mat` and `l2g_t`, then compute the minimum distance over each logged object
    extrapolated by logged velocity at horizon `(k + 1) * dt`;
  - TTC reconstruction: compute gap from ego world position to each logged object, closing speed
    from logged velocity, and `gap / closing` under the frozen `min_closing` gate;
  - match reconstructed candidate values to logged `min_cpa` / `min_ttc` within tolerance
    `1e-6` absolute or `1e-6` relative.

First-fire monitor provenance labels:

- `no_fire`: no fired decision row;
- `unique_cpa_object`: first-fire channel is CPA-only and exactly one object reconstructs the
  logged CPA argmin;
- `unique_ttc_object`: first-fire channel is TTC-only and exactly one object reconstructs the
  logged TTC argmin;
- `unique_both_same_object`: first-fire channel is both and the unique CPA and TTC argmins are
  the same object;
- `both_distinct_objects`: first-fire channel is both and CPA/TTC argmins are unique but
  different objects;
- `ambiguous_cpa_object`: CPA-relevant first fire has more than one CPA argmin object;
- `ambiguous_ttc_object`: TTC-relevant first fire has more than one TTC argmin object;
- `argmin_reconstruction_failed`: the logged scalar cannot be reconstructed from logged row
  fields under the frozen formulas;
- `schema_unsupported`: required decision-row fields are missing or malformed.

Collision-actor provenance support labels:

- `collision_actor_supported`: `eval.json` or its per-step `details` contains at least one
  non-scalar field whose key name indicates actor/object/agent/collision identity support;
- `collision_actor_not_logged`: `eval.json` and `details` expose only scalar metric fields for
  collision timing and score, with no actor/object/agent identity field.

This audit does not infer the true collision actor from geometry. It only reports whether the
committed evidence logs such an actor identity.

## Frozen summaries

Report counts for:

- all 104 ON-arm paired episodes;
- the 92 ON-collision episodes from iteration 53;
- the 35 pre-collision-fire ON-collision episodes from iteration 53;
- iteration 48 and iteration 49 separately;
- iteration 49 AttackPlanner vs non-AttackPlanner scenarios;
- first-fire channel crossed with monitor-provenance label;
- collision-actor provenance support label.

Also report a compact per-pair markdown table with scenario, run, first-fire channel, first-fire
time, first ON-collision time, monitor-provenance label, candidate object IDs, and collision-actor
support label.

## Verdicts

- `PROVENANCE_SUPPORT_INFRASTRUCTURE_NULL`: required committed files are missing, pair counts do
  not cross-check against iteration 53, or decision/eval schemas cannot be parsed.
- `PROVENANCE_SUPPORT_NULL`: infrastructure passes, but committed evidence does not support
  matching monitor first-fire hazards to HUGSIM collision actors because collision actor identity
  is not logged.
- `PROVENANCE_SUPPORT_COMPLETE`: infrastructure passes and collision actor identity is logged
  well enough to support a later fresh actor-match audit.

The most likely result, given the disclosed schema inspection, is a support null. That is not a
failure of the iteration; it is the honest boundary of the committed evidence.

## Forbidden claims

No new safety, transfer, deployment, robustness, benchmark-ranking, real-world,
monitor-performance, HUGSIM-equivalence, actor-identity, actor-match, or retuning claim. If the
result is `PROVENANCE_SUPPORT_NULL`, it must not say which object caused any HUGSIM collision.
It may only state what provenance is reconstructable from committed logs and what instrumentation
is missing for a later run.

## Required proof artifacts

- analyzer source and unit tests;
- `proof-provenance/provenance_support_report.json`;
- `proof-provenance/provenance_support_pairs.md`;
- `proof-provenance/analyze_provenance_support.command.txt`.

## Protocol

1. Commit this `HYPOTHESIS.md` ALONE.
2. Add and commit analyzer/tests; run `ruff check .`, `pytest -q`, and
   `python3 scripts/validate_docs.py`.
3. Run the analyzer ONCE over committed inputs.
4. Publish `RESULT.md` at full weight.
5. Update README, CONTINUITY, HANDOFF, and push.
