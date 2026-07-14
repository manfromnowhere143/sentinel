# Iteration 129 - support-core generated-artifact naming and destination preflight

Frozen after iteration 128 and its handoff were published. Frozen before any iteration-129
generator/verifier, naming note, proof artifact, result, index update, or handoff refresh.

This is an offline naming and destination-reservation preflight over the committed iteration-128
source-pool/mutation-operator freeze sheet. It may create proof artifacts that reserve future
artifact names and destination templates. It must not create generated scenario artifacts, choose
execution slots, launch HUGSIM, inspect raw GPU logs, change Sentinel thresholds, change
planner/action code, change HUGSIM metrics, run learning/update steps, or retune Sentinel.

## Frozen question

Can the committed iteration-128 source-pool/mutation-operator preflight be converted into a
deterministic future generated-artifact naming and destination reservation ledger, binding every
source pool and operator binding to unique planned future artifact names, while authorizing no
artifact creation, scenario generation, HUGSIM execution, GPU launch, metric change, threshold
retuning, learning/update, or claim upgrade?

## Frozen inputs

- Iteration 128 preflight report:
  `experiments/iter128_support_core_source_pool_mutation_preflight/proof-preflight/support_core_source_pool_mutation_preflight_report.json`
- Iteration 128 result:
  `experiments/iter128_support_core_source_pool_mutation_preflight/RESULT.md`
- Iteration 128 source-pool/mutation note:
  `docs/research/SUPPORT_CORE_SOURCE_POOL_MUTATION_PREFLIGHT_2026-07-14.md`
- Iteration 126 candidate manifest report:
  `experiments/iter126_support_core_candidate_manifest_preflight/proof-manifest/support_core_candidate_manifest_report.json`

## Success bars

S0 provenance and boundary pass:

- the iteration-128 report verdict is exactly
  `SUPPORT_CORE_SOURCE_POOL_MUTATION_PREFLIGHT_COMPLETE`;
- the iteration-128 result contains the same verdict;
- the iteration-128 note preserves the no-scenario-generation, no-generated-artifact,
  no-HUGSIM-run, no-GPU, no-learning/update, no-retuning, no-repair, no-safety, no-deployment,
  no-production, and no-commercial-claim boundary.

S1 source-pool/operator integrity pass:

- exactly `10` source pools are read;
- exactly `8` mutation operators are read;
- exactly `10` candidate-to-operator bindings are read;
- every binding references one existing source pool and one existing mutation operator;
- every source pool has false authorization flags for scenario generation, generated artifact
  creation, execution slot selection, GPU, HUGSIM, learning/update, repair, safety, deployment,
  production, and commercial claims.

S2 naming and destination reservation pass:

- exactly `10` future artifact reservations are produced, one per source pool/candidate;
- each reservation has deterministic `reservation_id`, `candidate_id`, `source_pool_id`,
  `operator_id`, `binding_id`, `artifact_stem`, `reserved_destination_root`,
  `reserved_relative_paths`, `path_collision_key`, `duplicate_handling_rule`,
  `required_future_creation_checks`, and explicit false authorization flags;
- each reservation has exactly three reserved relative paths:
  - `scenario_spec`;
  - `provenance_receipt`;
  - `validation_manifest`;
- exactly `30` reserved relative paths are produced;
- all reserved relative paths are unique;
- every reserved relative path is under the frozen root
  `future_artifacts/support_core_blindspot_generation/`;
- no reserved relative path currently exists on disk;
- no reservation includes a launch command, HUGSIM command, GPU path, raw-log path, execution
  slot selection, threshold-change instruction, metric-change instruction, planner-code-change
  instruction, runtime-code-change instruction, learning/update authorization, repair claim,
  safety claim, deployment claim, production claim, or commercial claim.

S3 claim-boundary pass:

- the verifier verdict is exactly `SUPPORT_CORE_ARTIFACT_NAMING_PREFLIGHT_COMPLETE`;
- the generated note states that a later successor still needs a fresh `HYPOTHESIS.md` before any
  reserved path is created, any generated artifact is written, any scenario generation is run, any
  execution slot is selected, any HUGSIM execution starts, any GPU is used, any learning/update
  step occurs, any repair is claimed, or any claim is upgraded.

## Falsifiers

Return `SUPPORT_CORE_ARTIFACT_NAMING_PREFLIGHT_INFRA_NULL` if any frozen input is missing or
malformed; any required boundary text is absent; source-pool, operator, binding, reservation, or
reserved-path counts differ from the frozen bars; any binding references a missing source pool or
operator; any reserved path is duplicated, outside the frozen root, or already exists on disk; any
authorization flag is true or missing; or any launch command, HUGSIM command, GPU path, raw-log
path, execution slot selection, threshold-change instruction, metric-change instruction,
planner-code-change instruction, runtime-code-change instruction, learning/update authorization,
repair claim, safety claim, deployment claim, production claim, or commercial claim appears.

## Required proof artifacts

- generator/verifier source plus unit tests;
- `proof-naming/support_core_artifact_naming_preflight_report.json`;
- `proof-naming/support_core_artifact_naming_preflight.md`;
- `proof-naming/generate_support_core_artifact_naming_preflight.command.txt`;
- generated-artifact naming note under `docs/research/`;
- published `RESULT.md`;
- README, `docs/NEXT_PHASE.md`, `CONTINUITY.md`, and `HANDOFF.md` updates after success.

## Protocol

1. Commit this `HYPOTHESIS.md` alone.
2. Add generator/verifier, tests, and note writer; run focused ruff/tests and docs guard.
3. Run the generator/verifier once.
4. Publish `RESULT.md`, run `ruff check .`, `pytest -q`, and `python3 scripts/validate_docs.py`,
   then push and refresh handoff.

## Claim boundary

Generated-artifact naming and destination preflight only; no generated scenario artifact, scenario
generation, execution-slot selection, GPU launch, HUGSIM run, learning/update step, repair,
actor-causality, threshold-value, transfer upgrade, safety, deployment, robustness, benchmark,
population-rate, HD-Score-invariance, real-world behavior, first-responder behavior,
acquisition-value, retuning, production, commercial claim, or frontier-stack equivalence claim.
