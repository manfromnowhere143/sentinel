# Iteration 130 - support-core generated-artifact schema and metadata preflight

Frozen after iteration 129 and its handoff were published. Frozen before any iteration-130
generator/verifier, schema note, proof artifact, result, index update, or handoff refresh.

This is an offline schema and metadata-contract preflight over the committed iteration-129
artifact naming/destination reservation ledger. It may create proof artifacts that define schema
contracts and path-to-schema bindings. It must not create any reserved future artifact path,
write any generated scenario artifact, generate scenarios, choose execution slots, launch HUGSIM,
inspect raw GPU logs, change Sentinel thresholds, change planner/action code, change HUGSIM
metrics, run learning/update steps, repair Sentinel, or retune Sentinel.

## Frozen question

Can the committed iteration-129 artifact reservation ledger be converted into a deterministic
schema and metadata contract for the three reserved future artifact types, binding all `30`
reserved relative paths to exactly one inert schema each, while authorizing no reserved file
creation, generated artifact writing, scenario generation, HUGSIM execution, GPU launch, metric
change, threshold retuning, learning/update, repair, or claim upgrade?

## Frozen inputs

- Iteration 129 naming/destination report:
  `experiments/iter129_support_core_artifact_naming_preflight/proof-naming/support_core_artifact_naming_preflight_report.json`
- Iteration 129 result:
  `experiments/iter129_support_core_artifact_naming_preflight/RESULT.md`
- Iteration 129 naming/destination note:
  `docs/research/SUPPORT_CORE_ARTIFACT_NAMING_PREFLIGHT_2026-07-14.md`

## Success bars

S0 provenance and boundary pass:

- the iteration-129 report verdict is exactly `SUPPORT_CORE_ARTIFACT_NAMING_PREFLIGHT_COMPLETE`;
- the iteration-129 result contains the same verdict;
- the iteration-129 note states that the reserved paths are not created and preserves the
  no-reserved-path-creation, no-generated-artifact, no-scenario-generation, no-HUGSIM-run,
  no-GPU, no-learning/update, no-retuning, no-repair, no-safety, no-deployment, no-production,
  and no-commercial-claim boundary.

S1 reservation integrity pass:

- exactly `10` artifact reservations are read;
- exactly `30` reserved relative paths are read;
- every reservation has exactly three path types: `scenario_spec`, `provenance_receipt`, and
  `validation_manifest`;
- every reserved relative path is unique, under
  `future_artifacts/support_core_blindspot_generation/`, and nonexistent on disk;
- every iteration-129 authorization flag remains false.

S2 schema contract pass:

- exactly `3` schema specs are produced, one per artifact type:
  - `scenario_spec`;
  - `provenance_receipt`;
  - `validation_manifest`;
- each schema spec has `schema_id`, `schema_version`, `artifact_type`,
  `required_top_level_fields`, `required_metadata_fields`, `required_identity_fields`,
  `required_boundary_fields`, `allowed_payload_sections`, `forbidden_fields`,
  `validation_rules`, and explicit false authorization flags;
- common required identity fields include `candidate_id`, `source_pool_id`, `operator_id`,
  `binding_id`, `reservation_id`, `artifact_stem`, `reserved_relative_path`, and
  `artifact_type`;
- common required boundary fields include `creation_hypothesis_id`, `creation_authorized`,
  `scenario_generation_authorized`, `execution_slot_selection_authorized`, `gpu_authorized`,
  `hugsim_run_authorized`, `learning_update_authorized`, `repair_authorized`,
  `safety_claim_authorized`, `deployment_authorized`, `production_authorized`,
  `commercial_claim_authorized`, and `claim_boundary`;
- no schema contains a launch command, HUGSIM command, GPU path, raw-log path, execution slot,
  generated artifact bytes, scenario file bytes, threshold-change instruction, metric-change
  instruction, planner-code-change instruction, runtime-code-change instruction, learning/update
  authorization, repair claim, safety claim, deployment claim, production claim, or commercial
  claim.

S3 reservation-to-schema binding pass:

- exactly `30` schema bindings are produced, one per reserved relative path;
- every binding references one existing reservation and one existing schema spec;
- every reservation has exactly three schema bindings, one per path type;
- every binding has false authorization flags and does not authorize file creation.

S4 claim-boundary pass:

- the verifier verdict is exactly `SUPPORT_CORE_ARTIFACT_SCHEMA_PREFLIGHT_COMPLETE`;
- the generated note states that a later successor still needs a fresh `HYPOTHESIS.md` before any
  reserved path is created, generated artifact is written, scenario generation is run, execution
  slot is selected, HUGSIM execution starts, GPU is used, learning/update step occurs, repair is
  claimed, or claim is upgraded.

## Falsifiers

Return `SUPPORT_CORE_ARTIFACT_SCHEMA_PREFLIGHT_INFRA_NULL` if any frozen input is missing or
malformed; any required boundary text is absent; reservation, reserved-path, schema, or binding
counts differ from the frozen bars; any reserved path is duplicated, outside the frozen root, or
already exists on disk; any required schema field is missing; any path type lacks exactly one
schema; any binding references a missing reservation or schema; any authorization flag is true or
missing; or any launch command, HUGSIM command, GPU path, raw-log path, execution slot, generated
artifact bytes, scenario file bytes, threshold-change instruction, metric-change instruction,
planner-code-change instruction, runtime-code-change instruction, learning/update authorization,
repair claim, safety claim, deployment claim, production claim, or commercial claim appears.

## Required proof artifacts

- generator/verifier source plus unit tests;
- `proof-schema/support_core_artifact_schema_preflight_report.json`;
- `proof-schema/support_core_artifact_schema_preflight.md`;
- `proof-schema/generate_support_core_artifact_schema_preflight.command.txt`;
- generated-artifact schema note under `docs/research/`;
- published `RESULT.md`;
- README, `docs/NEXT_PHASE.md`, `CONTINUITY.md`, and `HANDOFF.md` updates after success.

## Protocol

1. Commit this `HYPOTHESIS.md` alone.
2. Add generator/verifier, tests, and note writer; run focused ruff/tests and docs guard.
3. Run the generator/verifier once.
4. Publish `RESULT.md`, run `ruff check .`, `pytest -q`, and `python3 scripts/validate_docs.py`,
   then push and refresh handoff.

## Claim boundary

Generated-artifact schema and metadata preflight only; no reserved path creation, generated
scenario artifact, scenario generation, execution-slot selection, GPU launch, HUGSIM run,
learning/update step, repair, actor-causality, threshold-value, transfer upgrade, safety,
deployment, robustness, benchmark, population-rate, HD-Score-invariance, real-world behavior,
first-responder behavior, acquisition-value, retuning, production, commercial claim, or
frontier-stack equivalence claim.
