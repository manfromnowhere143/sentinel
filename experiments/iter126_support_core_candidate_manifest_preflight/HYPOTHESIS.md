# Iteration 126 - support-core candidate-generation manifest preflight

## Frozen question

Can the committed iteration-125 support-core blind-spot design surface be converted into a
deterministic candidate-generation manifest that covers every registered archetype with paired
future candidate specs, while authorizing no scenario generation, HUGSIM execution, GPU launch,
metric change, threshold retuning, or claim upgrade?

This is a preflight-only iteration. It may write manifest artifacts and a bounded research note.
It must not create generated scenarios, launch HUGSIM, inspect raw GPU logs, change Sentinel
runtime code, change HUGSIM metrics, or claim any improvement.

## Frozen inputs

- Iteration 125 proof report:
  `experiments/iter125_support_core_blind_spot_scenario_design/proof-design/support_core_blind_spot_scenario_design_report.json`
- Iteration 125 result:
  `experiments/iter125_support_core_blind_spot_scenario_design/RESULT.md`
- Iteration 125 design note:
  `docs/research/SUPPORT_CORE_BLIND_SPOT_SCENARIO_DESIGN_2026-07-14.md`

## Success bars

S0 provenance and boundary pass:

- the iteration-125 report verdict is exactly
  `SUPPORT_CORE_BLIND_SPOT_SCENARIO_DESIGN_COMPLETE`;
- the iteration-125 result contains that same verdict;
- the iteration-125 design note states that it authorizes no scenario generation, HUGSIM run,
  GPU launch, retuning, repair, safety, deployment, benchmark, population-rate, production, or
  commercial claim.

S1 archetype coverage pass:

- exactly `5` archetypes are read from the iteration-125 report;
- every archetype has non-empty source slots, source scenarios, candidate-generation knobs,
  future validation gates, timing-gap class, and selected-rank condition;
- every source slot from the five archetypes is covered by at least one manifest candidate.

S2 manifest construction pass:

- exactly `10` future candidate specs are produced: `2` specs per archetype;
- each archetype has exactly one `branch_stress` spec and one `counterfactual_control` spec;
- every candidate has a deterministic candidate ID, source archetype ID, source slots, source
  scenarios, mutation family, candidate-generation knobs, required gates, and explicit
  `execution_authorized=false`, `gpu_authorized=false`, and `hugsim_run_authorized=false` flags;
- no candidate includes a generated scenario path, launch command, metric-change instruction, or
  threshold-change instruction.

S3 claim-boundary pass:

- the manifest report verdict is exactly
  `SUPPORT_CORE_CANDIDATE_MANIFEST_PREFLIGHT_COMPLETE`;
- the manifest and note state that a later successor still needs a fresh `HYPOTHESIS.md` before
  scenario generation, slot selection, HUGSIM execution, GPU launch, repair, or claim upgrade.

## Falsifiers

Return `SUPPORT_CORE_CANDIDATE_MANIFEST_PREFLIGHT_INFRA_NULL` if any frozen input is missing or
malformed, any required iteration-125 boundary text is absent, the archetype count is not exactly
`5`, any archetype lacks required fields, the manifest count is not exactly `10`, any archetype
does not have exactly the two frozen roles, any authorization flag is true, any generated scenario
path or launch command appears, or any candidate suggests threshold, metric, planner, or runtime
code changes.

## Claim boundary

Manifest preflight only; no scenario-generation execution, GPU launch, HUGSIM run, repair,
actor-causality, threshold-value, transfer upgrade, safety, deployment, robustness, benchmark,
population-rate, HD-Score-invariance, real-world behavior, first-responder behavior,
acquisition-value, retuning, production, commercial claim, or frontier-stack equivalence claim.
