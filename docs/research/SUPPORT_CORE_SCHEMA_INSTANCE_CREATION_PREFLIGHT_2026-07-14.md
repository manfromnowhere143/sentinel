# HUGSIM support-core schema-instance creation preflight

Status: iteration-132 schema-instance creation preflight note. This defines inert
schema-instance templates, a validator contract, and reserved-path-to-template
bindings only; it authorizes no reserved path creation, generated scenario artifact,
scenario generation, execution-slot selection, HUGSIM run, GPU launch, learning/update
step, retuning, repair, safety, deployment, production, or commercial claim.

## Source

- Iteration 130 schema proof:
  [`support_core_artifact_schema_preflight_report.json`](../../experiments/iter130_support_core_artifact_schema_preflight/proof-schema/support_core_artifact_schema_preflight_report.json)
- Iteration 132 proof:
  [`support_core_schema_instance_creation_preflight_report.json`](../../experiments/iter132_support_core_schema_instance_creation_preflight/proof-instance/support_core_schema_instance_creation_preflight_report.json)

## Instance Rule

Each iteration-130 schema binding receives exactly one inert instance-template binding.
The three templates correspond to `scenario_spec`, `provenance_receipt`, and
`validation_manifest`. The validator contract checks shape, identity, metadata,
boundary flags, payload section names, forbidden fields, binding match, duplicate-path
prevention, and reserved-path nonexistence. It does not write any reserved path.

## Instance Templates

### `scinst_template_scenario_spec_v1`

- artifact type: `scenario_spec`
- schema: `scschema_scenario_spec_v1`
- top-level shape: `['schema_version', 'metadata', 'identity', 'boundary', 'payload']`
- template only: `True`
- payload sections:
  - `symbolic_scene_blueprint`
  - `mutation_operator_parameters`
  - `source_context_summary`
  - `validation_expectations`

### `scinst_template_provenance_receipt_v1`

- artifact type: `provenance_receipt`
- schema: `scschema_provenance_receipt_v1`
- top-level shape: `['schema_version', 'metadata', 'identity', 'boundary', 'payload']`
- template only: `True`
- payload sections:
  - `source_manifest_references`
  - `operator_binding_references`
  - `reservation_integrity_checks`
  - `future_creation_receipt`

### `scinst_template_validation_manifest_v1`

- artifact type: `validation_manifest`
- schema: `scschema_validation_manifest_v1`
- top-level shape: `['schema_version', 'metadata', 'identity', 'boundary', 'payload']`
- template only: `True`
- payload sections:
  - `schema_checks`
  - `path_checks`
  - `boundary_checks`
  - `duplicate_handling_checks`
  - `future_gate_checks`

## Validator Checks

- `top_level_fields`
- `schema_id_and_version`
- `metadata_fields`
- `identity_fields`
- `boundary_fields`
- `payload_section_names`
- `forbidden_fields_absent`
- `reserved_path_nonexistence`
- `schema_binding_match`
- `duplicate_path_prevention`

## Binding Counts

- `scenario_spec`: `10`
- `provenance_receipt`: `10`
- `validation_manifest`: `10`

## Future Gates

- fresh HYPOTHESIS.md authorizes creation of reserved paths
- schema instance validator is run before any reserved file is written
- reserved path nonexistence is rechecked immediately before creation
- scenario generation remains separate from execution-slot selection
- HUGSIM/GPU execution remains a later separately registered step
- learning/update and repair claims remain forbidden unless later evidence proves them

## Claim Boundary

schema-instance creation preflight only; no reserved path creation, generated scenario artifact, scenario generation, execution-slot selection, GPU launch, HUGSIM run, learning/update step, repair, actor-causality, threshold-value, transfer upgrade, safety, deployment, robustness, benchmark, population-rate, HD-Score-invariance, real-world behavior, first-responder behavior, acquisition-value, retuning, production, commercial claim, or frontier-stack equivalence claim
