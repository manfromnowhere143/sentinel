# Iteration 125 - support-core blind-spot scenario design

Frozen after iteration 124 was published and handoff was refreshed, before any iteration-125
design generator, design note, verifier/analyzer output, result, or handoff update.

This is an offline design iteration. It converts the committed HUGSIM support-core two-track
taxonomy into a bounded blind-spot/scenario-generation design surface. It reads only committed
repository markdown/json result surfaces. It launches no GPU work, reads no raw decision logs,
reruns no analyzer over raw HUGSIM artifacts, changes no thresholds, changes no planner/action
code, changes no HUGSIM metrics, and does not retune Sentinel.

## Process disclosure

Iterations 123 and 124 left three bounded research/design lanes after publication freshness:

1. blind-spot/scenario-generation design seeded by HUGSIM support-core failures;
2. higher-fidelity perturbation successor;
3. mission/rulebook boundary definition or external claim ledger.

The first lane is the highest-leverage next scientific move because the HUGSIM support-core line
already provides an eight-row mechanism taxonomy with explicit timing/object-identity separation.
The missing step is to turn that taxonomy into a future candidate-generation surface before any
GPU run or scenario mutation is proposed.

## Design question

Can the committed `8/8` support-core two-track taxonomy be converted into a complete, auditable
blind-spot/scenario-generation design surface that covers every observed branch and defines future
candidate-generation gates, without claiming repair, population rate, safety, deployment, or launch
authorization?

## Frozen inputs

- Iteration 121 synthesis report:
  `experiments/iter121_hugsim_support_core_two_track_synthesis/proof-synthesis/support_core_two_track_synthesis_report.json`
- Iteration 122 result:
  `experiments/iter122_support_core_taxonomy_documentation/RESULT.md`
- Iteration 123 audit result:
  `experiments/iter123_mission_evidence_alignment_audit/RESULT.md`
- Iteration 124 freshness result:
  `experiments/iter124_manuscript_report_freshness/RESULT.md`
- Support-core taxonomy note:
  `docs/research/SUPPORT_CORE_TWO_TRACK_TAXONOMY_2026-07-14.md`

## Frozen design rules

1. Require iteration 121 verdict `HUGSIM_SUPPORT_CORE_TWO_TRACK_SYNTHESIS_COMPLETE`.
2. Require exactly `8` synthesis rows, `8` two-track rows, and `8` selected-fire objects labeled
   `selected_never_supported_before_collision`.
3. Build one design archetype for each observed `synthesis_label`; no observed branch may be
   merged away.
4. Each archetype must include:
   - source row count and source slot IDs;
   - support-side branch;
   - selected-side branch;
   - selected rank condition (`selected_nearest`, `selected_not_nearest`, or mixed);
   - timing-gap class (`measured_support_gap`, `post_fire_support`, or `no_pre_fire_support`);
   - candidate-generation knobs;
   - future validation gates;
   - explicit forbidden claims.
5. The design must classify every source row into exactly one archetype and produce coverage
   counts that sum to `8`.
6. Produce a dedicated design note under `docs/research/` that states this is a design surface
   only and authorizes no scenario generation, HUGSIM run, GPU launch, retuning, repair, safety,
   deployment, population-rate, benchmark, production, or commercial claim.

## Frozen bars

- `SUPPORT_CORE_BLIND_SPOT_SCENARIO_DESIGN_INFRA_NULL`: any required input is missing; the
  iteration-121 verdict/count gates fail; any synthesis label lacks an archetype; any row maps to
  zero or multiple archetypes; required knobs/gates/boundaries are missing; docs guard fails; or
  the verifier cannot run.
- `SUPPORT_CORE_BLIND_SPOT_SCENARIO_DESIGN_COMPLETE`: all input gates pass, all observed branches
  receive exactly one archetype, all `8` rows are covered exactly once, the design note and proof
  artifacts are generated, and verifier/tests/repository gates pass.

## Required proof artifacts

- design generator/verifier source plus unit tests;
- `proof-design/support_core_blind_spot_scenario_design_report.json`;
- `proof-design/support_core_blind_spot_scenario_design.md`;
- `proof-design/generate_support_core_blind_spot_design.command.txt`;
- dedicated design note under `docs/research/`;
- README/NEXT_PHASE/CONTINUITY publication updates after the result.

## Protocol

1. Commit this `HYPOTHESIS.md` alone.
2. Add generator/verifier, tests, and design note; run targeted verifier/tests and
   `python3 scripts/validate_docs.py`.
3. Run the generator once over committed inputs.
4. Publish `RESULT.md`, run `ruff check .`, `pytest -q`, and `python3 scripts/validate_docs.py`,
   then push and refresh handoff.

## Forbidden claims

No scenario-generation execution, GPU launch, HUGSIM run, repair, actor-causality, threshold-value,
transfer upgrade, safety, deployment, robustness, benchmark, population-rate,
HD-Score-invariance, real-world behavior, first-responder behavior, acquisition-value, retuning,
production, commercial claim, or claim that Sentinel matches or exceeds Tesla, Mobileye, SpaceX,
Waymo, NVIDIA, or any current frontier autonomy stack.
