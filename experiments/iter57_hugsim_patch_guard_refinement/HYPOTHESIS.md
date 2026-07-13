# Iteration 57 - HUGSIM provenance patch guard refinement

Frozen before any iteration-57 verifier edit, verifier run, result, or claim.
This is a static verifier refinement only: zero GPU work, zero gcloud commands, zero simulator
launches, zero HUGSIM episodes, zero planner process, zero patch-content changes, zero Sentinel
monitor retuning, and zero metric-threshold edits.

## Process disclosure

Iteration 56 produced `INSTRUMENTATION_PATCH_DESIGN_NULL`. The patch draft applied cleanly and
`sim/utils/score_calculator.py` compiled, but the registered static guard rejected this added line:

`if score_nc == 0.0:`

The guard failed because it matched the substring `score_nc =` inside a comparison. That is
disclosed up front. Iteration 57 is not allowed to edit the patch to escape the guard.

## Bound patch

The only patch under test is the iteration-56 patch:

`experiments/iter56_hugsim_provenance_instrumentation_patch/proof-patch/hugsim_provenance_instrumentation.patch`

Its required SHA256 is:

`49eee7611e4b881d2bb6233e8767913019c6a097c6883762414005d5b2284ecd`

If the patch hash differs, this iteration must return null.

## Research question

Can a refined static verifier distinguish metric/control assignments from read-only branch
conditions and verify the byte-identical iteration-56 provenance patch as additive instrumentation
only?

This iteration does not authorize a HUGSIM run.

## Frozen evidence inputs

Allowed inputs:

- the byte-identical iteration-56 patch named above;
- the frozen HUGSIM source checkout at `62c690d39fd90020e68a196bd8bcc1c4d4191f2e`;
- iteration-56 proof artifacts and result.

Forbidden inputs:

- any modified instrumentation patch;
- `sentinel-gpu` or any remote box;
- any simulator run, smoke test, HUGSIM episode, planner process, or named-pipe execution;
- staged datasets, scenario YAMLs, or simulator outputs outside committed proof trees;
- source checkout at any SHA other than `62c690d39fd90020e68a196bd8bcc1c4d4191f2e`;
- changing Sentinel monitor thresholds, HUGSIM metric constants, scenario selection, planner
  behavior, action selection, or HD-Score calculation.

## Frozen method

1. Build a refined verifier that:
   - verifies the patch SHA256 exactly;
   - verifies the source checkout SHA;
   - applies the patch cleanly to a temporary clone of the frozen source;
   - rejects changed files outside the iteration-55 source-map allowance;
   - rejects added or removed assignments/augmented assignments/walrus assignments to metric or
     control-sensitive names (`score_nc`, `score_dac`, `score_ttc`, `score_c`, `score_pdms`,
     `mean_score`, `route_completion`, `driving_score`, `score_weight`, `boundaries`, `action`);
   - rejects changes to control calls such as `traj2control` or `env.step`;
   - permits read-only references to existing metric variables in branch conditions;
   - verifies the changed Python files parse or compile without importing HUGSIM.
2. Run the refined verifier once.
3. Publish the result at full weight, including nulls.

## Verdicts

- `PATCH_GUARD_REFINEMENT_NULL`: patch SHA mismatch, source SHA mismatch, patch apply failure,
  compile failure, changed file outside the allowed set, metric/control assignment detected, or
  required provenance fields missing.
- `PATCH_GUARD_REFINEMENT_COMPLETE`: the byte-identical iteration-56 patch passes the refined
  static verifier as additive provenance instrumentation only.

Either verdict is acceptable. A complete static guard result does not authorize a simulator run by
itself.

## Forbidden claims

No HUGSIM performance result, actor-match result, collision-cause result, safety claim, transfer
claim, deployment claim, benchmark-ranking claim, real-world claim, robustness claim, retuning claim,
or claim that HD-Score is unchanged in execution. Static verification can only say the patch is
additive by source diff inspection under the refined guard.

## Required proof artifacts

- verifier source and unit tests;
- `proof-refined/guard_refinement_report.json`;
- `proof-refined/guard_refinement.md`;
- `proof-refined/verify_refined_guard.command.txt`.

## Protocol

1. Commit this `HYPOTHESIS.md` ALONE.
2. Add and commit verifier/tests; run `ruff check .`, `pytest -q`, and
   `python3 scripts/validate_docs.py`.
3. Run the refined verifier ONCE over the frozen checkout and byte-identical patch.
4. Publish `RESULT.md` at full weight.
5. Update README, NEXT_PHASE, CONTINUITY, HANDOFF, verify, and push.
