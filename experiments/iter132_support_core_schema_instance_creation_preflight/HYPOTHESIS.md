# Iteration 132 - support-core schema-instance creation preflight

Frozen after iteration 131 and its handoff were published. Frozen before any iteration-132
generator/verifier, instance-template note, proof artifact, result, index update, or handoff
refresh.

This is an offline schema-instance creation preflight over the committed iteration-130
schema/metadata contract. It may create proof artifacts that define inert instance templates,
validator rules, and reserved-path-to-template bindings. It must not create any reserved future
artifact path, write any schema instance into `future_artifacts/`, write any generated scenario
artifact, generate scenarios, choose execution slots, launch HUGSIM, inspect raw GPU logs, change
Sentinel thresholds, change planner/action code, change HUGSIM metrics, run learning/update steps,
repair Sentinel, or retune Sentinel.

## Frozen question

Can the committed iteration-130 schema/metadata contract be converted into deterministic inert
schema-instance templates and a validator contract for all `30` reserved future paths, while
authorizing no reserved file creation, generated artifact writing, scenario generation, HUGSIM
execution, GPU launch, metric change, threshold retuning, learning/update, repair, or claim
upgrade?

## Frozen inputs

- Iteration 130 schema report:
  `experiments/iter130_support_core_artifact_schema_preflight/proof-schema/support_core_artifact_schema_preflight_report.json`
- Iteration 130 result:
  `experiments/iter130_support_core_artifact_schema_preflight/RESULT.md`
- Iteration 130 schema note:
  `docs/research/SUPPORT_CORE_ARTIFACT_SCHEMA_PREFLIGHT_2026-07-14.md`

## Success bars

S0 provenance and boundary pass:

- the iteration-130 schema report verdict is exactly
  `SUPPORT_CORE_ARTIFACT_SCHEMA_PREFLIGHT_COMPLETE`;
- the iteration-130 result contains the same verdict;
- the iteration-130 note states that schema contracts authorize no reserved path creation;
- the iteration-130 schema report has `3` schema specs, `30` schema bindings, `10` artifact
  reservations, `30` reserved relative paths, `0` true authorization flags, `0` existing bound
  paths, `0` duplicate reserved paths, `0` bad schema references, and `0` forbidden keys.

S1 schema contract integrity pass:

- exactly `3` schema specs are read, one per artifact type: `scenario_spec`,
  `provenance_receipt`, and `validation_manifest`;
- exactly `30` schema bindings are read, ten per artifact type;
- every schema binding references one existing schema spec and one reserved relative path;
- every reserved relative path remains under `future_artifacts/support_core_blindspot_generation/`
  and nonexistent on disk;
- every iteration-130 authorization flag remains false.

S2 instance-template contract pass:

- exactly `3` inert schema-instance templates are produced, one per artifact type;
- each template has `template_id`, `schema_id`, `schema_version`, `artifact_type`,
  `top_level_shape`, `metadata_template`, `identity_template`, `boundary_template`,
  `payload_template`, `required_validation_checks`, `forbidden_fields`,
  `template_only`, and explicit false authorization flags;
- every template's top-level shape is exactly `schema_version`, `metadata`, `identity`,
  `boundary`, and `payload`;
- every template carries placeholders for the iteration-130 required metadata, identity,
  boundary, and allowed payload fields;
- every template has `template_only=true` and every creation/execution/claim authorization flag is
  false.

S3 validator-contract pass:

- exactly one validator contract is produced;
- the validator contract includes checks for top-level fields, schema id/version, metadata fields,
  identity fields, boundary fields, payload section names, forbidden fields, reserved-path
  nonexistence, schema-binding match, and duplicate-path prevention;
- the validator contract states that validation does not create any reserved path or generated
  artifact;
- the validator contract has false creation/execution/claim authorization flags.

S4 reserved-path-to-template binding pass:

- exactly `30` instance-template bindings are produced, one per iteration-130 schema binding;
- every binding references one existing schema binding and one existing template;
- every reservation still has exactly three instance-template bindings;
- every binding has `creation_status` exactly `not_created`;
- every binding has false authorization flags and does not authorize file creation;
- no reserved relative path exists on disk after the verifier runs.

S5 claim-boundary pass:

- the verifier verdict is exactly `SUPPORT_CORE_SCHEMA_INSTANCE_CREATION_PREFLIGHT_COMPLETE`;
- the generated note states that a later successor still needs a fresh `HYPOTHESIS.md` before any
  reserved path is created, generated artifact is written, scenario generation is run, execution
  slot is selected, HUGSIM execution starts, GPU is used, learning/update step occurs, repair is
  claimed, or claim is upgraded.

## Falsifiers

Return `SUPPORT_CORE_SCHEMA_INSTANCE_CREATION_PREFLIGHT_INFRA_NULL` if any frozen input is missing
or malformed; any required boundary text is absent; iteration-130 counts differ from the frozen
bars; schema, binding, template, validator, or instance-binding counts differ from the frozen
bars; any reserved path is duplicated, outside the frozen root, or already exists on disk; any
required template or validator field is missing; any binding references a missing schema binding or
template; any `creation_status` is not `not_created`; any authorization flag is true or missing; or
any launch command, HUGSIM command, GPU path, raw-log path, execution slot, generated artifact
bytes, scenario file bytes, threshold-change instruction, metric-change instruction,
planner-code-change instruction, runtime-code-change instruction, learning/update authorization,
repair claim, safety claim, deployment claim, production claim, or commercial claim appears.

## Required proof artifacts

- generator/verifier source plus unit tests;
- `proof-instance/support_core_schema_instance_creation_preflight_report.json`;
- `proof-instance/support_core_schema_instance_creation_preflight.md`;
- `proof-instance/generate_support_core_schema_instance_creation_preflight.command.txt`;
- schema-instance creation preflight note under `docs/research/`;
- published `RESULT.md`;
- README, `docs/NEXT_PHASE.md`, `CONTINUITY.md`, and `HANDOFF.md` updates after success.

## Protocol

1. Commit this `HYPOTHESIS.md` alone.
2. Add generator/verifier, tests, and note writer; run focused ruff/tests and docs guard.
3. Run the generator/verifier once.
4. Publish `RESULT.md`, run `ruff check .`, `pytest -q`, and `python3 scripts/validate_docs.py`,
   then push and refresh handoff.

## Claim boundary

Schema-instance creation preflight only; no reserved path creation, generated scenario artifact,
scenario generation, execution-slot selection, GPU launch, HUGSIM run, learning/update step,
repair, actor-causality, threshold-value, transfer upgrade, safety, deployment, robustness,
benchmark, population-rate, HD-Score-invariance, real-world behavior, first-responder behavior,
acquisition-value, retuning, production, commercial claim, or frontier-stack equivalence claim.
