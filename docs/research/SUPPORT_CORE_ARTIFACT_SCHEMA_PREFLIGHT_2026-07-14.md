# HUGSIM support-core generated-artifact schema preflight

Status: iteration-130 schema/metadata preflight note. This defines schema contracts
and path-to-schema bindings only; it authorizes no reserved path creation, generated
scenario artifact, scenario generation, execution-slot selection, HUGSIM run, GPU launch,
learning/update step, retuning, repair, safety, deployment, production, or commercial claim.

## Source

- Iteration 129 naming/destination proof:
  [`support_core_artifact_naming_preflight_report.json`](../../experiments/iter129_support_core_artifact_naming_preflight/proof-naming/support_core_artifact_naming_preflight_report.json)
- Iteration 130 proof:
  [`support_core_artifact_schema_preflight_report.json`](../../experiments/iter130_support_core_artifact_schema_preflight/proof-schema/support_core_artifact_schema_preflight_report.json)

## Schema Rule

Each reserved path from iteration 129 is bound to exactly one schema. The three schema
types are `scenario_spec`, `provenance_receipt`, and `validation_manifest`. The schema
contract names required identity, metadata, boundary, payload, and forbidden fields, but
does not write any reserved path or generated artifact.

## Schema Specs

### `scschema_scenario_spec_v1`

- artifact type: `scenario_spec`
- version: `iter130.support_core_artifact_schema.v1`
- required identity fields:
  - `candidate_id`
  - `source_pool_id`
  - `operator_id`
  - `binding_id`
  - `reservation_id`
  - `artifact_stem`
  - `reserved_relative_path`
  - `artifact_type`
- required boundary fields:
  - `creation_hypothesis_id`
  - `creation_authorized`
  - `reserved_path_creation_authorized`
  - `scenario_generation_authorized`
  - `execution_slot_selection_authorized`
  - `gpu_authorized`
  - `hugsim_run_authorized`
  - `learning_update_authorized`
  - `repair_authorized`
  - `safety_claim_authorized`
  - `deployment_authorized`
  - `production_authorized`
  - `commercial_claim_authorized`
  - `claim_boundary`
- allowed payload sections:
  - `symbolic_scene_blueprint`
  - `mutation_operator_parameters`
  - `source_context_summary`
  - `validation_expectations`

### `scschema_provenance_receipt_v1`

- artifact type: `provenance_receipt`
- version: `iter130.support_core_artifact_schema.v1`
- required identity fields:
  - `candidate_id`
  - `source_pool_id`
  - `operator_id`
  - `binding_id`
  - `reservation_id`
  - `artifact_stem`
  - `reserved_relative_path`
  - `artifact_type`
- required boundary fields:
  - `creation_hypothesis_id`
  - `creation_authorized`
  - `reserved_path_creation_authorized`
  - `scenario_generation_authorized`
  - `execution_slot_selection_authorized`
  - `gpu_authorized`
  - `hugsim_run_authorized`
  - `learning_update_authorized`
  - `repair_authorized`
  - `safety_claim_authorized`
  - `deployment_authorized`
  - `production_authorized`
  - `commercial_claim_authorized`
  - `claim_boundary`
- allowed payload sections:
  - `source_manifest_references`
  - `operator_binding_references`
  - `reservation_integrity_checks`
  - `future_creation_receipt`

### `scschema_validation_manifest_v1`

- artifact type: `validation_manifest`
- version: `iter130.support_core_artifact_schema.v1`
- required identity fields:
  - `candidate_id`
  - `source_pool_id`
  - `operator_id`
  - `binding_id`
  - `reservation_id`
  - `artifact_stem`
  - `reserved_relative_path`
  - `artifact_type`
- required boundary fields:
  - `creation_hypothesis_id`
  - `creation_authorized`
  - `reserved_path_creation_authorized`
  - `scenario_generation_authorized`
  - `execution_slot_selection_authorized`
  - `gpu_authorized`
  - `hugsim_run_authorized`
  - `learning_update_authorized`
  - `repair_authorized`
  - `safety_claim_authorized`
  - `deployment_authorized`
  - `production_authorized`
  - `commercial_claim_authorized`
  - `claim_boundary`
- allowed payload sections:
  - `schema_checks`
  - `path_checks`
  - `boundary_checks`
  - `duplicate_handling_checks`
  - `future_gate_checks`

## Binding Counts

- `scenario_spec`: `10`
- `provenance_receipt`: `10`
- `validation_manifest`: `10`

## Future Gates

- fresh HYPOTHESIS.md authorizes creation of reserved paths
- schema instance validator checks metadata and boundary fields before creation
- reserved path nonexistence is rechecked immediately before creation
- scenario generation remains separate from execution-slot selection
- HUGSIM/GPU execution remains a later separately registered step
- learning/update and repair claims remain forbidden unless later evidence proves them

## Claim Boundary

generated-artifact schema and metadata preflight only; no reserved path creation, generated scenario artifact, scenario generation, execution-slot selection, GPU launch, HUGSIM run, learning/update step, repair, actor-causality, threshold-value, transfer upgrade, safety, deployment, robustness, benchmark, population-rate, HD-Score-invariance, real-world behavior, first-responder behavior, acquisition-value, retuning, production, commercial claim, or frontier-stack equivalence claim
