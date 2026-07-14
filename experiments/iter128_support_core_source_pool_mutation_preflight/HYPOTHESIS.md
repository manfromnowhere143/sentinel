# Iteration 128 - support-core source-pool and mutation-operator preflight

Frozen after iteration 127 and its handoff were published. Frozen before any iteration-128
generator/verifier, source-pool note, proof artifact, result, index update, or handoff refresh.

This is an offline pre-generation freeze over the committed iteration-126 support-core
candidate-generation manifest. It may create symbolic source-pool and mutation-operator artifacts.
It must not generate scenarios, choose execution slots, launch HUGSIM, inspect raw GPU logs, change
Sentinel thresholds, change planner/action code, change HUGSIM metrics, or retune Sentinel.

## Frozen question

Can the committed iteration-126 candidate manifest be converted into a deterministic
source-pool and mutation-operator freeze sheet that binds every symbolic candidate to one frozen
source pool and one frozen mutation operator, while authorizing no scenario generation, HUGSIM
execution, GPU launch, metric change, threshold retuning, or claim upgrade?

## Frozen inputs

- Iteration 126 manifest report:
  `experiments/iter126_support_core_candidate_manifest_preflight/proof-manifest/support_core_candidate_manifest_report.json`
- Iteration 126 result:
  `experiments/iter126_support_core_candidate_manifest_preflight/RESULT.md`
- Iteration 126 manifest note:
  `docs/research/SUPPORT_CORE_CANDIDATE_GENERATION_MANIFEST_2026-07-14.md`
- Iteration 127 alignment audit result:
  `experiments/iter127_post_iter126_mission_alignment_audit/RESULT.md`
- Iteration 127 alignment audit note:
  `docs/research/SENTINEL_POST_ITER126_MISSION_ALIGNMENT_AUDIT_2026-07-14.md`

## Success bars

S0 provenance and boundary pass:

- the iteration-126 report verdict is exactly
  `SUPPORT_CORE_CANDIDATE_MANIFEST_PREFLIGHT_COMPLETE`;
- the iteration-126 result contains the same verdict;
- the iteration-127 result contains `POST_ITER126_MISSION_ALIGNMENT_AUDIT_COMPLETE`;
- the iteration-126 manifest note and iteration-127 audit note both preserve the no-generation,
  no-HUGSIM-run, no-GPU, no-retuning, no-repair, no-safety, no-deployment, no-production, and
  no-commercial-claim boundary.

S1 manifest integrity pass:

- exactly `10` committed symbolic candidates are read;
- exactly `5` archetypes are present;
- role counts are exactly `branch_stress=5` and `counterfactual_control=5`;
- every candidate has non-empty `candidate_id`, `archetype_id`, `candidate_role`,
  `mutation_family`, `source_slot_ids`, `source_scenarios`, `timing_gap_class`,
  `selected_rank_condition`, `candidate_generation_knobs`, and `required_gates`;
- every candidate has `execution_authorized=false`, `gpu_authorized=false`,
  `hugsim_run_authorized=false`, `scenario_generation_authorized=false`,
  `metric_change_authorized=false`, `threshold_change_authorized=false`,
  `planner_code_change_authorized=false`, and `runtime_code_change_authorized=false`.

S2 source-pool freeze pass:

- exactly `10` source pools are produced, one per committed candidate;
- every source pool has deterministic `source_pool_id`, `candidate_id`, `archetype_id`,
  `source_slot_ids`, `source_scenarios`, `source_pool_kind`, `selection_key`,
  `duplicate_handling_rule`, `allowed_source_fields`, and explicit false authorization flags;
- every source slot from iteration 126 appears in at least one source pool;
- no source pool contains generated scenario paths, launch commands, raw-log paths, GPU paths,
  output directories, or execution slot selections.

S3 mutation-operator freeze pass:

- exactly `8` mutation operators are produced, one per unique iteration-126 mutation family;
- exactly `10` candidate-to-operator bindings are produced;
- every candidate binds to exactly one mutation operator;
- every operator has deterministic `operator_id`, `mutation_family`, `operator_kind`,
  `allowed_controls`, `invariants`, `prohibited_actions`, `required_pre_generation_checks`, and
  explicit false authorization flags;
- every operator preserves frozen thresholds, HUGSIM metrics, planner code, runtime code, and
  claim boundaries.

S4 claim-boundary pass:

- the verifier verdict is exactly `SUPPORT_CORE_SOURCE_POOL_MUTATION_PREFLIGHT_COMPLETE`;
- the generated note states that a later successor still needs a fresh `HYPOTHESIS.md` before any
  scenario generation, generated-artifact creation, slot selection, HUGSIM execution, GPU launch,
  learning/update step, repair, or claim upgrade.

## Falsifiers

Return `SUPPORT_CORE_SOURCE_POOL_MUTATION_PREFLIGHT_INFRA_NULL` if any frozen input is missing or
malformed; any required boundary text is absent; the candidate, archetype, role, source-pool,
operator, or binding counts differ from the frozen bars; any candidate/source-pool/operator
authorization flag is true or missing; any generated scenario path, launch command, raw-log path,
GPU path, output directory, execution slot selection, threshold-change instruction,
metric-change instruction, planner-code-change instruction, runtime-code-change instruction,
learning/update authorization, repair claim, safety claim, deployment claim, production claim, or
commercial claim appears.

## Required proof artifacts

- generator/verifier source plus unit tests;
- `proof-preflight/support_core_source_pool_mutation_preflight_report.json`;
- `proof-preflight/support_core_source_pool_mutation_preflight.md`;
- `proof-preflight/generate_support_core_source_pool_mutation_preflight.command.txt`;
- source-pool/mutation-operator note under `docs/research/`;
- published `RESULT.md`;
- README, `docs/NEXT_PHASE.md`, `CONTINUITY.md`, and `HANDOFF.md` updates after success.

## Protocol

1. Commit this `HYPOTHESIS.md` alone.
2. Add generator/verifier, tests, and note writer; run focused ruff/tests and docs guard.
3. Run the generator/verifier once.
4. Publish `RESULT.md`, run `ruff check .`, `pytest -q`, and `python3 scripts/validate_docs.py`,
   then push and refresh handoff.

## Claim boundary

Source-pool and mutation-operator preflight only; no scenario-generation execution, generated
scenario artifact, execution-slot selection, GPU launch, HUGSIM run, learning/update step, repair,
actor-causality, threshold-value, transfer upgrade, safety, deployment, robustness, benchmark,
population-rate, HD-Score-invariance, real-world behavior, first-responder behavior,
acquisition-value, retuning, production, commercial claim, or frontier-stack equivalence claim.
