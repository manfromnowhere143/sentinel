# Iteration 56 - HUGSIM provenance instrumentation patch design

Frozen before any iteration-56 source inspection beyond the published iteration-55 proof, any patch
draft, verifier run, result, or claim. This is a source-only patch-design gate: zero GPU work,
zero gcloud commands, zero simulator launches, zero HUGSIM episodes, zero planner edits, zero
Sentinel monitor retuning, and zero metric-threshold edits.

## Process disclosure

This is not blind. Iteration 55 is already published and identified two source-map candidates in
the frozen HUGSIM checkout at `62c690d39fd90020e68a196bd8bcc1c4d4191f2e`:

- `sim/utils/score_calculator.py`;
- `closed_loop.py`.

No additional post-iteration-55 HUGSIM source lines are inspected before freezing this file.
Iteration 56 therefore makes no inferential surprise claim; it is an engineering gate for whether
the source map can be converted into an auditable no-metric-change instrumentation patch.

## Research question

Can Sentinel draft and statically verify a HUGSIM patch that records collision/contact/proximity
provenance for a future actor-match run while preserving the existing metric semantics?

The patch may add provenance outputs. It must not authorize or perform a HUGSIM run.

## Frozen evidence inputs

Allowed inputs:

- a read-only local clone of `https://github.com/hyzhou404/HUGSIM` checked out exactly at
  `62c690d39fd90020e68a196bd8bcc1c4d4191f2e`;
- iteration-55 proof artifacts:
  - `experiments/iter55_hugsim_collision_instrumentation_source_audit/RESULT.md`;
  - `experiments/iter55_hugsim_collision_instrumentation_source_audit/proof-source/source_map_report.json`;
  - `experiments/iter55_hugsim_collision_instrumentation_source_audit/proof-source/source_map.md`;
- committed HUGSIM launch scripts from iterations 48/49 for output-path context only.

Forbidden inputs:

- `sentinel-gpu` or any other remote box;
- any simulator run, smoke test, HUGSIM episode, planner process, or named-pipe execution;
- staged datasets, scenario YAMLs, or simulator outputs outside committed proof trees;
- source checkout at any SHA other than `62c690d39fd90020e68a196bd8bcc1c4d4191f2e`;
- changing Sentinel monitor thresholds, HUGSIM metric constants, scenario selection, planner
  behavior, action selection, or HD-Score calculation.

## Frozen method

1. Inspect only the frozen HUGSIM source candidates identified by iteration 55 and their immediate
   local dependencies as needed for patch context.
2. Draft a patch file under `proof-patch/hugsim_provenance_instrumentation.patch`.
3. The patch may add a provenance sidecar or optional metadata field that records collision actor,
   contact, distance, or proximity candidates. It may not remove, rename, or alter existing scalar
   metric keys.
4. Add a static verifier that:
   - verifies the source checkout SHA;
   - applies the patch cleanly to a temporary copy of the frozen source;
   - lists changed files and hunks;
   - rejects changes to known scalar metric names, metric constants, scenario selection, monitor
     parameters, or planner/action control outside additive provenance code;
   - records whether the changed Python files still parse or compile without importing HUGSIM.
5. Run the verifier once and publish its report at full weight.

## Verdicts

- `INSTRUMENTATION_PATCH_DESIGN_NULL`: the patch cannot be drafted, does not apply cleanly, fails
  static guards, alters metric/control semantics, or cannot be verified without running HUGSIM.
- `INSTRUMENTATION_PATCH_DESIGN_COMPLETE`: the patch applies cleanly to the frozen source and static
  guards support that it is additive provenance instrumentation only.

Either verdict is acceptable. A complete patch design does not authorize a simulator run by itself.

## Forbidden claims

No actor-match result, collision-cause result, HUGSIM performance result, safety claim, transfer
claim, deployment claim, benchmark-ranking claim, real-world claim, robustness claim, retuning claim,
or claim that HD-Score is unchanged in execution. Static verification can only say the patch design
is additive by source diff inspection.

## Required proof artifacts

- patch file: `proof-patch/hugsim_provenance_instrumentation.patch`;
- verifier source and unit tests;
- `proof-patch/patch_verification_report.json`;
- `proof-patch/patch_verification.md`;
- `proof-patch/verify_patch.command.txt`;

## Protocol

1. Commit this `HYPOTHESIS.md` ALONE.
2. Add and commit verifier/tests; run `ruff check .`, `pytest -q`, and
   `python3 scripts/validate_docs.py`.
3. Draft the patch against a temporary frozen HUGSIM checkout outside the Sentinel repo.
4. Run the verifier ONCE over the frozen checkout and patch.
5. Publish `RESULT.md` at full weight.
6. Update README, NEXT_PHASE, CONTINUITY, HANDOFF, verify, and push.
