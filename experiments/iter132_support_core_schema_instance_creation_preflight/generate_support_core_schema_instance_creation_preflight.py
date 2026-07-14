#!/usr/bin/env python3
"""Iteration 132 support-core schema-instance creation preflight."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ITER130_VERDICT = "SUPPORT_CORE_ARTIFACT_SCHEMA_PREFLIGHT_COMPLETE"
COMPLETE_VERDICT = "SUPPORT_CORE_SCHEMA_INSTANCE_CREATION_PREFLIGHT_COMPLETE"
INFRA_NULL_VERDICT = "SUPPORT_CORE_SCHEMA_INSTANCE_CREATION_PREFLIGHT_INFRA_NULL"
EXPECTED_RESERVATION_COUNT = 10
EXPECTED_RESERVED_PATH_COUNT = 30
EXPECTED_SCHEMA_COUNT = 3
EXPECTED_SCHEMA_BINDING_COUNT = 30
EXPECTED_TEMPLATE_COUNT = 3
EXPECTED_INSTANCE_BINDING_COUNT = 30
EXPECTED_VALIDATOR_CONTRACT_COUNT = 1
RESERVED_ROOT = "future_artifacts/support_core_blindspot_generation"
ARTIFACT_TYPES = ("scenario_spec", "provenance_receipt", "validation_manifest")
INSTANCE_TEMPLATE_VERSION = "iter132.support_core_schema_instance_template.v1"
ITER130_REPORT_PATH = Path(
    "experiments/iter130_support_core_artifact_schema_preflight/proof-schema/"
    "support_core_artifact_schema_preflight_report.json"
)
ITER130_RESULT_PATH = Path("experiments/iter130_support_core_artifact_schema_preflight/RESULT.md")
ITER130_NOTE_PATH = Path(
    "docs/research/SUPPORT_CORE_ARTIFACT_SCHEMA_PREFLIGHT_2026-07-14.md"
)
INSTANCE_NOTE_PATH = Path(
    "docs/research/SUPPORT_CORE_SCHEMA_INSTANCE_CREATION_PREFLIGHT_2026-07-14.md"
)
DEFAULT_PROOF_DIR = Path(
    "experiments/iter132_support_core_schema_instance_creation_preflight/proof-instance"
)
DEFAULT_REPORT_PATH = DEFAULT_PROOF_DIR / "support_core_schema_instance_creation_preflight_report.json"
DEFAULT_MARKDOWN_PATH = DEFAULT_PROOF_DIR / "support_core_schema_instance_creation_preflight.md"
DEFAULT_COMMAND_PATH = (
    DEFAULT_PROOF_DIR / "generate_support_core_schema_instance_creation_preflight.command.txt"
)
BOUNDARY = (
    "schema-instance creation preflight only; no reserved path creation, generated scenario "
    "artifact, scenario generation, execution-slot selection, GPU launch, HUGSIM run, "
    "learning/update step, repair, actor-causality, threshold-value, transfer upgrade, safety, "
    "deployment, robustness, benchmark, population-rate, HD-Score-invariance, real-world "
    "behavior, first-responder behavior, acquisition-value, retuning, production, commercial "
    "claim, or frontier-stack equivalence claim"
)
BOUNDARY_NEEDLES = (
    "authorizes no reserved path creation",
    "schema contracts",
    "HUGSIM run",
    "GPU launch",
    "learning/update",
    "repair",
    "deployment",
    "production",
    "commercial claim",
)
ITER130_FALSE_AUTHORIZATION_FIELDS = (
    "creation_authorized",
    "reserved_path_creation_authorized",
    "generated_artifact_authorized",
    "scenario_generation_authorized",
    "execution_slot_selection_authorized",
    "execution_authorized",
    "gpu_authorized",
    "hugsim_run_authorized",
    "learning_update_authorized",
    "metric_change_authorized",
    "threshold_change_authorized",
    "planner_code_change_authorized",
    "runtime_code_change_authorized",
    "repair_authorized",
    "safety_claim_authorized",
    "deployment_authorized",
    "production_authorized",
    "commercial_claim_authorized",
)
PREFLIGHT_FALSE_AUTHORIZATION_FIELDS = (
    "creation_authorized",
    "reserved_path_creation_authorized",
    "schema_instance_creation_authorized",
    "generated_artifact_authorized",
    "scenario_generation_authorized",
    "execution_slot_selection_authorized",
    "execution_authorized",
    "gpu_authorized",
    "hugsim_run_authorized",
    "learning_update_authorized",
    "metric_change_authorized",
    "threshold_change_authorized",
    "planner_code_change_authorized",
    "runtime_code_change_authorized",
    "repair_authorized",
    "safety_claim_authorized",
    "deployment_authorized",
    "production_authorized",
    "commercial_claim_authorized",
)
REQUIRED_SCHEMA_FIELDS = (
    "schema_id",
    "schema_version",
    "artifact_type",
    "required_top_level_fields",
    "required_metadata_fields",
    "required_identity_fields",
    "required_boundary_fields",
    "allowed_payload_sections",
    "forbidden_fields",
    "validation_rules",
)
REQUIRED_TEMPLATE_FIELDS = (
    "template_id",
    "template_version",
    "schema_id",
    "schema_version",
    "artifact_type",
    "top_level_shape",
    "metadata_template",
    "identity_template",
    "boundary_template",
    "payload_template",
    "required_validation_checks",
    "forbidden_fields",
    "template_only",
)
FORBIDDEN_FIELDS = (
    "launch_command",
    "launcher_command",
    "hugsim_command",
    "gpu_path",
    "raw_log_path",
    "raw_log_paths",
    "execution_slot_id",
    "execution_slot_selection",
    "generated_artifact_bytes",
    "generated_artifact_path",
    "generated_scenario_path",
    "scenario_file_bytes",
    "threshold_change_instruction",
    "metric_change_instruction",
    "planner_code_change_instruction",
    "runtime_code_change_instruction",
    "learning_update_authorization",
    "repair_claim",
    "safety_claim",
    "deployment_claim",
    "production_claim",
    "commercial_claim",
)
VALIDATOR_CHECKS = (
    "top_level_fields",
    "schema_id_and_version",
    "metadata_fields",
    "identity_fields",
    "boundary_fields",
    "payload_section_names",
    "forbidden_fields_absent",
    "reserved_path_nonexistence",
    "schema_binding_match",
    "duplicate_path_prevention",
)


def load_json(path: Path, label: str) -> tuple[dict[str, Any], list[str]]:
    if not path.exists() or path.stat().st_size == 0:
        return {}, [f"missing-or-empty:{label}:{path}"]
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"read-json-failed:{label}:{path}:{exc}"]
    if not isinstance(data, dict):
        return {}, [f"json-not-dict:{label}:{path}"]
    return data, []


def load_text(path: Path, label: str) -> tuple[str, list[str]]:
    if not path.exists() or path.stat().st_size == 0:
        return "", [f"missing-or-empty:{label}:{path}"]
    try:
        return path.read_text(), []
    except OSError as exc:
        return "", [f"read-text-failed:{label}:{path}:{exc}"]


def normalize(text: str) -> str:
    return " ".join(text.split())


def require_contains(problems: list[str], label: str, text: str, needle: str) -> None:
    if normalize(needle) not in normalize(text):
        problems.append(f"{label}-missing:{needle}")


def require_boundary(problems: list[str], label: str, text: str) -> None:
    normalized = normalize(text)
    for needle in BOUNDARY_NEEDLES:
        if normalize(needle) not in normalized:
            problems.append(f"{label}-missing-boundary:{needle}")


def false_authorizations() -> dict[str, bool]:
    return {field: False for field in PREFLIGHT_FALSE_AUTHORIZATION_FIELDS}


def template_id(artifact_type: str) -> str:
    return f"scinst_template_{artifact_type}_v1"


def placeholder(field: str) -> str:
    return f"{{{{{field}}}}}"


def check_forbidden_keys(item: Any, path: str = "root") -> list[str]:
    problems: list[str] = []
    if isinstance(item, dict):
        for key, value in item.items():
            if key in FORBIDDEN_FIELDS and value not in (None, "", [], {}):
                problems.append(f"forbidden-key-present:{path}.{key}")
            problems.extend(check_forbidden_keys(value, f"{path}.{key}"))
    elif isinstance(item, list):
        for index, value in enumerate(item):
            problems.extend(check_forbidden_keys(value, f"{path}[{index}]"))
    return problems


def count_true_authorizations(
    items: list[dict[str, Any]],
    auth_fields: tuple[str, ...],
    problems: list[str],
    label: str,
) -> int:
    true_count = 0
    for item in items:
        item_id = (
            item.get("template_id")
            or item.get("validator_contract_id")
            or item.get("instance_binding_id")
            or item.get("schema_id")
            or item.get("schema_binding_id")
            or "unknown"
        )
        for field in auth_fields:
            if item.get(field) is not False:
                true_count += int(item.get(field) is True)
                problems.append(f"{label}-auth-not-false:{item_id}:{field}")
    return true_count


def validate_iter130_report(report: dict[str, Any], problems: list[str]) -> None:
    if report.get("verdict") != ITER130_VERDICT:
        problems.append(f"iter130-verdict-mismatch:{report.get('verdict')!r}")
    summary = report.get("summary")
    if not isinstance(summary, dict):
        problems.append("iter130-summary-not-dict")
        return
    expected = {
        "artifact_reservation_count": EXPECTED_RESERVATION_COUNT,
        "reserved_relative_path_count": EXPECTED_RESERVED_PATH_COUNT,
        "schema_spec_count": EXPECTED_SCHEMA_COUNT,
        "schema_binding_count": EXPECTED_SCHEMA_BINDING_COUNT,
        "true_authorization_count": 0,
        "existing_bound_path_count": 0,
        "duplicate_reserved_path_count": 0,
        "bad_schema_reference_count": 0,
        "forbidden_key_count": 0,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            problems.append(f"iter130-summary-{key}-mismatch:{summary.get(key)!r}!={value!r}")
    if summary.get("schema_artifact_types") != list(ARTIFACT_TYPES):
        problems.append(f"iter130-schema-artifact-types-mismatch:{summary.get('schema_artifact_types')!r}")
    if summary.get("schema_binding_type_counts") != {
        artifact_type: EXPECTED_RESERVATION_COUNT for artifact_type in ARTIFACT_TYPES
    }:
        problems.append(
            "iter130-schema-binding-type-counts-mismatch:"
            f"{summary.get('schema_binding_type_counts')!r}"
        )


def require_dict_list(
    report: dict[str, Any],
    key: str,
    expected_count: int,
    problems: list[str],
) -> list[dict[str, Any]]:
    value = report.get(key)
    if not isinstance(value, list):
        problems.append(f"iter130-{key}-not-list")
        return []
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            problems.append(f"iter130-{key}-item-not-dict:{index}")
            continue
        rows.append(item)
    if len(rows) != expected_count:
        problems.append(f"iter130-{key}-count-mismatch:{len(rows)}!={expected_count}")
    return rows


def validate_schema_specs(schemas: list[dict[str, Any]], problems: list[str]) -> dict[str, int]:
    missing_schema_content_count = 0
    forbidden_key_count = 0
    by_type = {str(schema.get("artifact_type")): schema for schema in schemas}
    if set(by_type) != set(ARTIFACT_TYPES):
        problems.append(f"schema-artifact-types-mismatch:{sorted(by_type)}")
    for schema in schemas:
        schema_label = str(schema.get("schema_id", "unknown"))
        for field in REQUIRED_SCHEMA_FIELDS:
            if schema.get(field) in (None, "", [], {}):
                missing_schema_content_count += 1
                problems.append(f"schema-missing-{field}:{schema_label}")
        artifact_type = str(schema.get("artifact_type"))
        if schema.get("schema_id") != f"scschema_{artifact_type}_v1":
            problems.append(f"schema-id-mismatch:{schema_label}")
        if tuple(schema.get("required_top_level_fields", [])) != (
            "schema_version",
            "metadata",
            "identity",
            "boundary",
            "payload",
        ):
            problems.append(f"schema-top-level-shape-mismatch:{schema_label}")
        if tuple(schema.get("forbidden_fields", [])) != FORBIDDEN_FIELDS:
            problems.append(f"schema-forbidden-fields-mismatch:{schema_label}")
        forbidden_keys = check_forbidden_keys(schema, "schema")
        forbidden_key_count += len(forbidden_keys)
        problems.extend(forbidden_keys)
    return {
        "missing_schema_content_count": missing_schema_content_count,
        "schema_forbidden_key_count": forbidden_key_count,
    }


def validate_schema_bindings(
    repo_root: Path,
    schemas: list[dict[str, Any]],
    bindings: list[dict[str, Any]],
    problems: list[str],
) -> dict[str, int]:
    missing_binding_content_count = 0
    bad_schema_reference_count = 0
    existing_reserved_path_count = 0
    duplicate_reserved_path_count = 0
    forbidden_key_count = 0
    schema_ids = {str(schema.get("schema_id")) for schema in schemas}
    all_paths: list[str] = []
    seen_binding_ids: set[str] = set()
    for binding in bindings:
        binding_id = binding.get("schema_binding_id")
        if not isinstance(binding_id, str) or not binding_id:
            missing_binding_content_count += 1
            problems.append(f"schema-binding-id-missing:{binding_id!r}")
        elif binding_id in seen_binding_ids:
            problems.append(f"schema-binding-id-duplicate:{binding_id}")
        else:
            seen_binding_ids.add(binding_id)
        for field in (
            "reservation_id",
            "candidate_id",
            "source_pool_id",
            "operator_id",
            "candidate_operator_binding_id",
            "artifact_stem",
            "artifact_type",
            "reserved_relative_path",
            "schema_id",
            "schema_version",
        ):
            if binding.get(field) in (None, "", [], {}):
                missing_binding_content_count += 1
                problems.append(f"schema-binding-missing-{field}:{binding_id}")
        artifact_type = str(binding.get("artifact_type"))
        schema_id_value = str(binding.get("schema_id"))
        if schema_id_value not in schema_ids:
            bad_schema_reference_count += 1
            problems.append(f"schema-binding-missing-schema:{binding_id}:{schema_id_value}")
        if schema_id_value != f"scschema_{artifact_type}_v1":
            bad_schema_reference_count += 1
            problems.append(f"schema-binding-schema-type-mismatch:{binding_id}")
        relpath = str(binding.get("reserved_relative_path"))
        all_paths.append(relpath)
        if not relpath.startswith(f"{RESERVED_ROOT}/"):
            bad_schema_reference_count += 1
            problems.append(f"schema-binding-path-outside-root:{binding_id}:{relpath}")
        if (repo_root / relpath).exists():
            existing_reserved_path_count += 1
            problems.append(f"schema-binding-path-exists:{binding_id}:{relpath}")
        forbidden_keys = check_forbidden_keys(binding, "schema_binding")
        forbidden_key_count += len(forbidden_keys)
        problems.extend(forbidden_keys)
    duplicate_reserved_path_count = sum(count - 1 for count in Counter(all_paths).values() if count > 1)
    if duplicate_reserved_path_count:
        problems.append(f"schema-binding-duplicate-path-count:{duplicate_reserved_path_count}")
    return {
        "missing_binding_content_count": missing_binding_content_count,
        "bad_schema_reference_count": bad_schema_reference_count,
        "existing_reserved_path_count": existing_reserved_path_count,
        "duplicate_reserved_path_count": duplicate_reserved_path_count,
        "binding_forbidden_key_count": forbidden_key_count,
        "reserved_relative_path_count": len(all_paths),
    }


def build_instance_templates(schemas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    templates: list[dict[str, Any]] = []
    schema_by_type = {str(schema["artifact_type"]): schema for schema in schemas}
    for artifact_type in ARTIFACT_TYPES:
        schema = schema_by_type[artifact_type]
        payload_template = {
            section: {
                "section_status": "placeholder_only",
                "content_authorized": False,
            }
            for section in schema["allowed_payload_sections"]
        }
        templates.append(
            {
                "template_id": template_id(artifact_type),
                "template_version": INSTANCE_TEMPLATE_VERSION,
                "schema_id": schema["schema_id"],
                "schema_version": schema["schema_version"],
                "artifact_type": artifact_type,
                "top_level_shape": list(schema["required_top_level_fields"]),
                "metadata_template": {
                    field: placeholder(field) for field in schema["required_metadata_fields"]
                },
                "identity_template": {
                    field: placeholder(field) for field in schema["required_identity_fields"]
                },
                "boundary_template": {
                    field: (
                        False
                        if field in PREFLIGHT_FALSE_AUTHORIZATION_FIELDS
                        else placeholder(field)
                    )
                    for field in schema["required_boundary_fields"]
                },
                "payload_template": payload_template,
                "required_validation_checks": list(VALIDATOR_CHECKS),
                "forbidden_fields": list(schema["forbidden_fields"]),
                "template_only": True,
                **false_authorizations(),
            }
        )
    return templates


def build_validator_contract(templates: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "validator_contract_id": "scinst_validator_contract_v1",
        "template_version": INSTANCE_TEMPLATE_VERSION,
        "validates_artifact_types": list(ARTIFACT_TYPES),
        "required_checks": list(VALIDATOR_CHECKS),
        "template_ids": [str(template["template_id"]) for template in templates],
        "validation_does_not_create_paths": True,
        "reserved_path_nonexistence_required": True,
        "schema_binding_match_required": True,
        "duplicate_path_prevention_required": True,
        "forbidden_fields": list(FORBIDDEN_FIELDS),
        "claim_boundary": BOUNDARY,
        **false_authorizations(),
    }


def build_instance_bindings(bindings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    instance_bindings: list[dict[str, Any]] = []
    sorted_bindings = sorted(
        bindings,
        key=lambda item: (
            str(item.get("reservation_id")),
            ARTIFACT_TYPES.index(str(item.get("artifact_type"))),
        ),
    )
    for index, binding in enumerate(sorted_bindings, start=1):
        artifact_type = str(binding["artifact_type"])
        instance_bindings.append(
            {
                "instance_binding_id": (
                    f"scinst_bind_{index:03d}_{artifact_type}_{binding['reservation_id']}"
                ),
                "schema_binding_id": binding["schema_binding_id"],
                "template_id": template_id(artifact_type),
                "schema_id": binding["schema_id"],
                "schema_version": binding["schema_version"],
                "template_version": INSTANCE_TEMPLATE_VERSION,
                "reservation_id": binding["reservation_id"],
                "candidate_id": binding["candidate_id"],
                "source_pool_id": binding["source_pool_id"],
                "operator_id": binding["operator_id"],
                "candidate_operator_binding_id": binding["candidate_operator_binding_id"],
                "artifact_stem": binding["artifact_stem"],
                "artifact_type": artifact_type,
                "reserved_relative_path": binding["reserved_relative_path"],
                "creation_status": "not_created",
                "file_creation_rule": "fresh pre-registration required before writing this path",
                "schema_instance_authorizes_file_creation": False,
                **false_authorizations(),
            }
        )
    return instance_bindings


def validate_instance_templates(
    templates: list[dict[str, Any]],
    schemas: list[dict[str, Any]],
    problems: list[str],
) -> dict[str, int]:
    missing_template_content_count = 0
    bad_template_reference_count = 0
    forbidden_key_count = 0
    schema_by_type = {str(schema.get("artifact_type")): schema for schema in schemas}
    if len(templates) != EXPECTED_TEMPLATE_COUNT:
        problems.append(f"template-count-mismatch:{len(templates)}!={EXPECTED_TEMPLATE_COUNT}")
    if {str(template.get("artifact_type")) for template in templates} != set(ARTIFACT_TYPES):
        problems.append("template-artifact-types-mismatch")
    for template in templates:
        template_label = str(template.get("template_id", "unknown"))
        artifact_type = str(template.get("artifact_type"))
        schema = schema_by_type.get(artifact_type)
        for field in REQUIRED_TEMPLATE_FIELDS:
            if template.get(field) in (None, "", [], {}):
                missing_template_content_count += 1
                problems.append(f"template-missing-{field}:{template_label}")
        if template.get("template_id") != template_id(artifact_type):
            bad_template_reference_count += 1
            problems.append(f"template-id-mismatch:{template_label}")
        if template.get("template_only") is not True:
            bad_template_reference_count += 1
            problems.append(f"template-only-not-true:{template_label}")
        if schema is None:
            bad_template_reference_count += 1
            problems.append(f"template-missing-schema-type:{template_label}:{artifact_type}")
        else:
            if template.get("schema_id") != schema.get("schema_id"):
                bad_template_reference_count += 1
                problems.append(f"template-schema-id-mismatch:{template_label}")
            if template.get("schema_version") != schema.get("schema_version"):
                bad_template_reference_count += 1
                problems.append(f"template-schema-version-mismatch:{template_label}")
            if template.get("top_level_shape") != schema.get("required_top_level_fields"):
                bad_template_reference_count += 1
                problems.append(f"template-top-level-shape-mismatch:{template_label}")
            if set(template.get("metadata_template", {})) != set(
                schema.get("required_metadata_fields", [])
            ):
                missing_template_content_count += 1
                problems.append(f"template-metadata-fields-mismatch:{template_label}")
            if set(template.get("identity_template", {})) != set(
                schema.get("required_identity_fields", [])
            ):
                missing_template_content_count += 1
                problems.append(f"template-identity-fields-mismatch:{template_label}")
            if set(template.get("boundary_template", {})) != set(
                schema.get("required_boundary_fields", [])
            ):
                missing_template_content_count += 1
                problems.append(f"template-boundary-fields-mismatch:{template_label}")
            if set(template.get("payload_template", {})) != set(
                schema.get("allowed_payload_sections", [])
            ):
                missing_template_content_count += 1
                problems.append(f"template-payload-sections-mismatch:{template_label}")
            if template.get("forbidden_fields") != schema.get("forbidden_fields"):
                bad_template_reference_count += 1
                problems.append(f"template-forbidden-fields-mismatch:{template_label}")
        if tuple(template.get("required_validation_checks", [])) != VALIDATOR_CHECKS:
            bad_template_reference_count += 1
            problems.append(f"template-validation-checks-mismatch:{template_label}")
        forbidden_keys = check_forbidden_keys(template, "template")
        forbidden_key_count += len(forbidden_keys)
        problems.extend(forbidden_keys)
    return {
        "missing_template_content_count": missing_template_content_count,
        "bad_template_reference_count": bad_template_reference_count,
        "template_forbidden_key_count": forbidden_key_count,
    }


def validate_validator_contract(
    validator_contract: dict[str, Any],
    templates: list[dict[str, Any]],
    problems: list[str],
) -> dict[str, int]:
    missing_validator_content_count = 0
    bad_validator_reference_count = 0
    forbidden_key_count = 0
    for field in (
        "validator_contract_id",
        "template_version",
        "validates_artifact_types",
        "required_checks",
        "template_ids",
        "validation_does_not_create_paths",
        "reserved_path_nonexistence_required",
        "schema_binding_match_required",
        "duplicate_path_prevention_required",
        "forbidden_fields",
    ):
        if validator_contract.get(field) in (None, "", [], {}):
            missing_validator_content_count += 1
            problems.append(f"validator-missing-{field}")
    if validator_contract.get("validates_artifact_types") != list(ARTIFACT_TYPES):
        bad_validator_reference_count += 1
        problems.append("validator-artifact-types-mismatch")
    if tuple(validator_contract.get("required_checks", [])) != VALIDATOR_CHECKS:
        bad_validator_reference_count += 1
        problems.append("validator-checks-mismatch")
    if set(validator_contract.get("template_ids", [])) != {
        str(template["template_id"]) for template in templates
    }:
        bad_validator_reference_count += 1
        problems.append("validator-template-ids-mismatch")
    for field in (
        "validation_does_not_create_paths",
        "reserved_path_nonexistence_required",
        "schema_binding_match_required",
        "duplicate_path_prevention_required",
    ):
        if validator_contract.get(field) is not True:
            bad_validator_reference_count += 1
            problems.append(f"validator-bool-not-true:{field}")
    if validator_contract.get("forbidden_fields") != list(FORBIDDEN_FIELDS):
        bad_validator_reference_count += 1
        problems.append("validator-forbidden-fields-mismatch")
    forbidden_keys = check_forbidden_keys(validator_contract, "validator")
    forbidden_key_count += len(forbidden_keys)
    problems.extend(forbidden_keys)
    return {
        "missing_validator_content_count": missing_validator_content_count,
        "bad_validator_reference_count": bad_validator_reference_count,
        "validator_forbidden_key_count": forbidden_key_count,
    }


def validate_instance_bindings(
    repo_root: Path,
    schema_bindings: list[dict[str, Any]],
    templates: list[dict[str, Any]],
    instance_bindings: list[dict[str, Any]],
    problems: list[str],
) -> dict[str, int]:
    missing_instance_binding_content_count = 0
    bad_instance_binding_reference_count = 0
    existing_reserved_path_count = 0
    forbidden_key_count = 0
    schema_binding_by_id = {
        str(binding.get("schema_binding_id")): binding for binding in schema_bindings
    }
    template_ids = {str(template.get("template_id")) for template in templates}
    seen_ids: set[str] = set()
    all_paths: list[str] = []
    bindings_by_reservation: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for binding in instance_bindings:
        binding_id = binding.get("instance_binding_id")
        if not isinstance(binding_id, str) or not binding_id:
            missing_instance_binding_content_count += 1
            problems.append(f"instance-binding-id-missing:{binding_id!r}")
        elif binding_id in seen_ids:
            bad_instance_binding_reference_count += 1
            problems.append(f"instance-binding-id-duplicate:{binding_id}")
        else:
            seen_ids.add(binding_id)
        for field in (
            "schema_binding_id",
            "template_id",
            "schema_id",
            "schema_version",
            "template_version",
            "reservation_id",
            "candidate_id",
            "source_pool_id",
            "operator_id",
            "candidate_operator_binding_id",
            "artifact_stem",
            "artifact_type",
            "reserved_relative_path",
            "creation_status",
        ):
            if binding.get(field) in (None, "", [], {}):
                missing_instance_binding_content_count += 1
                problems.append(f"instance-binding-missing-{field}:{binding_id}")
        schema_binding_id = str(binding.get("schema_binding_id"))
        template_id_value = str(binding.get("template_id"))
        schema_binding = schema_binding_by_id.get(schema_binding_id)
        artifact_type = str(binding.get("artifact_type"))
        if schema_binding is None:
            bad_instance_binding_reference_count += 1
            problems.append(f"instance-binding-missing-schema-binding:{binding_id}")
        else:
            for field in (
                "schema_id",
                "schema_version",
                "reservation_id",
                "candidate_id",
                "source_pool_id",
                "operator_id",
                "candidate_operator_binding_id",
                "artifact_stem",
                "artifact_type",
                "reserved_relative_path",
            ):
                if binding.get(field) != schema_binding.get(field):
                    bad_instance_binding_reference_count += 1
                    problems.append(f"instance-binding-field-mismatch:{binding_id}:{field}")
            bindings_by_reservation[str(schema_binding.get("reservation_id"))].append(binding)
        if template_id_value not in template_ids:
            bad_instance_binding_reference_count += 1
            problems.append(f"instance-binding-missing-template:{binding_id}:{template_id_value}")
        if template_id_value != template_id(artifact_type):
            bad_instance_binding_reference_count += 1
            problems.append(f"instance-binding-template-type-mismatch:{binding_id}")
        if binding.get("creation_status") != "not_created":
            bad_instance_binding_reference_count += 1
            problems.append(f"instance-binding-created:{binding_id}:{binding.get('creation_status')!r}")
        relpath = str(binding.get("reserved_relative_path"))
        all_paths.append(relpath)
        if (repo_root / relpath).exists():
            existing_reserved_path_count += 1
            problems.append(f"instance-binding-path-exists:{binding_id}:{relpath}")
        forbidden_keys = check_forbidden_keys(binding, "instance_binding")
        forbidden_key_count += len(forbidden_keys)
        problems.extend(forbidden_keys)
    for reservation_id, rows in bindings_by_reservation.items():
        artifact_types = {str(binding.get("artifact_type")) for binding in rows}
        if artifact_types != set(ARTIFACT_TYPES):
            bad_instance_binding_reference_count += 1
            problems.append(f"instance-binding-reservation-type-coverage:{reservation_id}")
    duplicate_path_count = sum(count - 1 for count in Counter(all_paths).values() if count > 1)
    if duplicate_path_count:
        problems.append(f"instance-binding-duplicate-path-count:{duplicate_path_count}")
    return {
        "missing_instance_binding_content_count": missing_instance_binding_content_count,
        "bad_instance_binding_reference_count": bad_instance_binding_reference_count,
        "existing_instance_bound_path_count": existing_reserved_path_count,
        "duplicate_instance_bound_path_count": duplicate_path_count,
        "instance_binding_forbidden_key_count": forbidden_key_count,
    }


def summarize(
    schemas: list[dict[str, Any]],
    schema_bindings: list[dict[str, Any]],
    templates: list[dict[str, Any]],
    validator_contract: dict[str, Any],
    instance_bindings: list[dict[str, Any]],
    schema_counts: dict[str, int],
    schema_binding_counts: dict[str, int],
    template_counts: dict[str, int],
    validator_counts: dict[str, int],
    instance_binding_counts: dict[str, int],
    true_authorization_count: int,
) -> dict[str, Any]:
    return {
        "schema_spec_count": len(schemas),
        "schema_binding_count": len(schema_bindings),
        "artifact_reservation_count": len(
            {str(binding.get("reservation_id")) for binding in schema_bindings}
        ),
        "reserved_relative_path_count": schema_binding_counts["reserved_relative_path_count"],
        "instance_template_count": len(templates),
        "validator_contract_count": int(bool(validator_contract)),
        "instance_binding_count": len(instance_bindings),
        "instance_binding_type_counts": {
            artifact_type: sum(
                1 for binding in instance_bindings if binding.get("artifact_type") == artifact_type
            )
            for artifact_type in ARTIFACT_TYPES
        },
        "reservation_instance_binding_counts": {
            reservation_id: count
            for reservation_id, count in sorted(
                Counter(str(binding.get("reservation_id")) for binding in instance_bindings).items()
            )
        },
        "true_authorization_count": true_authorization_count,
        "missing_schema_content_count": schema_counts["missing_schema_content_count"],
        "missing_schema_binding_content_count": schema_binding_counts[
            "missing_binding_content_count"
        ],
        "missing_template_content_count": template_counts["missing_template_content_count"],
        "missing_validator_content_count": validator_counts["missing_validator_content_count"],
        "missing_instance_binding_content_count": instance_binding_counts[
            "missing_instance_binding_content_count"
        ],
        "bad_schema_reference_count": schema_binding_counts["bad_schema_reference_count"],
        "bad_template_reference_count": template_counts["bad_template_reference_count"],
        "bad_validator_reference_count": validator_counts["bad_validator_reference_count"],
        "bad_instance_binding_reference_count": instance_binding_counts[
            "bad_instance_binding_reference_count"
        ],
        "existing_reserved_path_count": schema_binding_counts["existing_reserved_path_count"],
        "existing_instance_bound_path_count": instance_binding_counts[
            "existing_instance_bound_path_count"
        ],
        "duplicate_reserved_path_count": schema_binding_counts["duplicate_reserved_path_count"],
        "duplicate_instance_bound_path_count": instance_binding_counts[
            "duplicate_instance_bound_path_count"
        ],
        "forbidden_key_count": (
            schema_counts["schema_forbidden_key_count"]
            + schema_binding_counts["binding_forbidden_key_count"]
            + template_counts["template_forbidden_key_count"]
            + validator_counts["validator_forbidden_key_count"]
            + instance_binding_counts["instance_binding_forbidden_key_count"]
        ),
    }


def choose_verdict(problems: list[str], summary: dict[str, Any]) -> str:
    if problems:
        return INFRA_NULL_VERDICT
    expected = {
        "schema_spec_count": EXPECTED_SCHEMA_COUNT,
        "schema_binding_count": EXPECTED_SCHEMA_BINDING_COUNT,
        "artifact_reservation_count": EXPECTED_RESERVATION_COUNT,
        "reserved_relative_path_count": EXPECTED_RESERVED_PATH_COUNT,
        "instance_template_count": EXPECTED_TEMPLATE_COUNT,
        "validator_contract_count": EXPECTED_VALIDATOR_CONTRACT_COUNT,
        "instance_binding_count": EXPECTED_INSTANCE_BINDING_COUNT,
        "true_authorization_count": 0,
        "missing_schema_content_count": 0,
        "missing_schema_binding_content_count": 0,
        "missing_template_content_count": 0,
        "missing_validator_content_count": 0,
        "missing_instance_binding_content_count": 0,
        "bad_schema_reference_count": 0,
        "bad_template_reference_count": 0,
        "bad_validator_reference_count": 0,
        "bad_instance_binding_reference_count": 0,
        "existing_reserved_path_count": 0,
        "existing_instance_bound_path_count": 0,
        "duplicate_reserved_path_count": 0,
        "duplicate_instance_bound_path_count": 0,
        "forbidden_key_count": 0,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            return INFRA_NULL_VERDICT
    if summary.get("instance_binding_type_counts") != {
        artifact_type: EXPECTED_RESERVATION_COUNT for artifact_type in ARTIFACT_TYPES
    }:
        return INFRA_NULL_VERDICT
    if set(summary.get("reservation_instance_binding_counts", {}).values()) != {
        len(ARTIFACT_TYPES)
    }:
        return INFRA_NULL_VERDICT
    return COMPLETE_VERDICT


def build_report(
    repo_root: Path,
    iter130_report_path: Path,
    iter130_result_path: Path,
    iter130_note_path: Path,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    problems: list[str] = []
    iter130_report, report_problems = load_json(iter130_report_path, "iter130-report")
    iter130_result, result_problems = load_text(iter130_result_path, "iter130-result")
    iter130_note, note_problems = load_text(iter130_note_path, "iter130-note")
    problems.extend(report_problems)
    problems.extend(result_problems)
    problems.extend(note_problems)

    validate_iter130_report(iter130_report, problems)
    require_contains(problems, "iter130-result", iter130_result, ITER130_VERDICT)
    require_boundary(problems, "iter130-note", iter130_note)
    schemas = require_dict_list(
        iter130_report,
        "schema_specs",
        EXPECTED_SCHEMA_COUNT,
        problems,
    )
    schema_bindings = require_dict_list(
        iter130_report,
        "schema_bindings",
        EXPECTED_SCHEMA_BINDING_COUNT,
        problems,
    )
    schema_counts = validate_schema_specs(schemas, problems)
    schema_binding_counts = validate_schema_bindings(repo_root, schemas, schema_bindings, problems)
    iter130_true_authorization_count = count_true_authorizations(
        schemas + schema_bindings,
        ITER130_FALSE_AUTHORIZATION_FIELDS,
        problems,
        "iter130",
    )

    if problems:
        templates: list[dict[str, Any]] = []
        validator_contract: dict[str, Any] = {}
        instance_bindings: list[dict[str, Any]] = []
        template_counts = {
            "missing_template_content_count": 0,
            "bad_template_reference_count": 0,
            "template_forbidden_key_count": 0,
        }
        validator_counts = {
            "missing_validator_content_count": 0,
            "bad_validator_reference_count": 0,
            "validator_forbidden_key_count": 0,
        }
        instance_binding_counts = {
            "missing_instance_binding_content_count": 0,
            "bad_instance_binding_reference_count": 0,
            "existing_instance_bound_path_count": 0,
            "duplicate_instance_bound_path_count": 0,
            "instance_binding_forbidden_key_count": 0,
        }
        new_true_authorization_count = 0
    else:
        templates = build_instance_templates(schemas)
        validator_contract = build_validator_contract(templates)
        instance_bindings = build_instance_bindings(schema_bindings)
        template_counts = validate_instance_templates(templates, schemas, problems)
        validator_counts = validate_validator_contract(validator_contract, templates, problems)
        instance_binding_counts = validate_instance_bindings(
            repo_root,
            schema_bindings,
            templates,
            instance_bindings,
            problems,
        )
        new_true_authorization_count = count_true_authorizations(
            templates + [validator_contract] + instance_bindings,
            PREFLIGHT_FALSE_AUTHORIZATION_FIELDS,
            problems,
            "instance-preflight",
        )

    summary = summarize(
        schemas,
        schema_bindings,
        templates,
        validator_contract,
        instance_bindings,
        schema_counts,
        schema_binding_counts,
        template_counts,
        validator_counts,
        instance_binding_counts,
        iter130_true_authorization_count + new_true_authorization_count,
    )
    return {
        "iteration": 132,
        "inputs": {
            "iter130_report": str(iter130_report_path),
            "iter130_result": str(iter130_result_path),
            "iter130_note": str(iter130_note_path),
        },
        "summary": summary,
        "schema_instance_templates": templates,
        "validator_contract": validator_contract,
        "instance_template_bindings": instance_bindings,
        "future_creation_requirements": [
            "fresh HYPOTHESIS.md authorizes creation of reserved paths",
            "schema instance validator is run before any reserved file is written",
            "reserved path nonexistence is rechecked immediately before creation",
            "scenario generation remains separate from execution-slot selection",
            "HUGSIM/GPU execution remains a later separately registered step",
            "learning/update and repair claims remain forbidden unless later evidence proves them",
        ],
        "problems": problems,
        "verdict": choose_verdict(problems, summary),
        "claim_boundary": BOUNDARY,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 132 - support-core schema-instance creation preflight",
        "",
        f"Verdict: `{report['verdict']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Instance Templates", ""])
    for template in report["schema_instance_templates"]:
        lines.extend(
            [
                f"### `{template['template_id']}`",
                "",
                f"- artifact type: `{template['artifact_type']}`",
                f"- schema: `{template['schema_id']}`",
                f"- template only: `{template['template_only']}`",
                "- payload sections:",
            ]
        )
        for section in template["payload_template"]:
            lines.append(f"  - `{section}`")
        lines.append("")
    if report["validator_contract"]:
        validator = report["validator_contract"]
        lines.extend(
            [
                "## Validator Contract",
                "",
                f"- contract: `{validator['validator_contract_id']}`",
                f"- path creation prevented: `{validator['validation_does_not_create_paths']}`",
                "- required checks:",
            ]
        )
        for check_name in validator["required_checks"]:
            lines.append(f"  - `{check_name}`")
        lines.append("")
    lines.extend(["## Instance Bindings", ""])
    for binding in report["instance_template_bindings"]:
        lines.extend(
            [
                f"### `{binding['instance_binding_id']}`",
                "",
                f"- schema binding: `{binding['schema_binding_id']}`",
                f"- template: `{binding['template_id']}`",
                f"- artifact type: `{binding['artifact_type']}`",
                f"- reserved path: `{binding['reserved_relative_path']}`",
                f"- creation status: `{binding['creation_status']}`",
                "",
            ]
        )
    if report["problems"]:
        lines.extend(["## Problems", ""])
        lines.extend(f"- `{problem}`" for problem in report["problems"])
        lines.append("")
    lines.extend(["## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def write_note(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# HUGSIM support-core schema-instance creation preflight",
        "",
        "Status: iteration-132 schema-instance creation preflight note. This defines inert",
        "schema-instance templates, a validator contract, and reserved-path-to-template",
        "bindings only; it authorizes no reserved path creation, generated scenario artifact,",
        "scenario generation, execution-slot selection, HUGSIM run, GPU launch, learning/update",
        "step, retuning, repair, safety, deployment, production, or commercial claim.",
        "",
        "## Source",
        "",
        "- Iteration 130 schema proof:",
        "  [`support_core_artifact_schema_preflight_report.json`](../../experiments/iter130_support_core_artifact_schema_preflight/proof-schema/support_core_artifact_schema_preflight_report.json)",
        "- Iteration 132 proof:",
        "  [`support_core_schema_instance_creation_preflight_report.json`](../../experiments/iter132_support_core_schema_instance_creation_preflight/proof-instance/support_core_schema_instance_creation_preflight_report.json)",
        "",
        "## Instance Rule",
        "",
        "Each iteration-130 schema binding receives exactly one inert instance-template binding.",
        "The three templates correspond to `scenario_spec`, `provenance_receipt`, and",
        "`validation_manifest`. The validator contract checks shape, identity, metadata,",
        "boundary flags, payload section names, forbidden fields, binding match, duplicate-path",
        "prevention, and reserved-path nonexistence. It does not write any reserved path.",
        "",
        "## Instance Templates",
        "",
    ]
    for template in report["schema_instance_templates"]:
        lines.extend(
            [
                f"### `{template['template_id']}`",
                "",
                f"- artifact type: `{template['artifact_type']}`",
                f"- schema: `{template['schema_id']}`",
                f"- top-level shape: `{template['top_level_shape']}`",
                f"- template only: `{template['template_only']}`",
                "- payload sections:",
            ]
        )
        for section in template["payload_template"]:
            lines.append(f"  - `{section}`")
        lines.append("")
    lines.extend(["## Validator Checks", ""])
    for check_name in report["validator_contract"].get("required_checks", []):
        lines.append(f"- `{check_name}`")
    lines.extend(["", "## Binding Counts", ""])
    for artifact_type, count in report["summary"]["instance_binding_type_counts"].items():
        lines.append(f"- `{artifact_type}`: `{count}`")
    lines.extend(["", "## Future Gates", ""])
    for requirement in report["future_creation_requirements"]:
        lines.append(f"- {requirement}")
    lines.extend(["", "## Claim Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def write_command(path: Path) -> None:
    command = (
        "python3 experiments/iter132_support_core_schema_instance_creation_preflight/"
        "generate_support_core_schema_instance_creation_preflight.py\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(command)


def run_preflight(
    repo_root: Path,
    iter130_report: Path,
    iter130_result: Path,
    iter130_note: Path,
    out: Path,
    markdown_out: Path,
    note_out: Path,
    command_out: Path,
) -> dict[str, Any]:
    report = build_report(repo_root, iter130_report, iter130_result, iter130_note)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(report, markdown_out)
    write_note(report, note_out)
    write_command(command_out)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--iter130-report", type=Path, default=ITER130_REPORT_PATH)
    parser.add_argument("--iter130-result", type=Path, default=ITER130_RESULT_PATH)
    parser.add_argument("--iter130-note", type=Path, default=ITER130_NOTE_PATH)
    parser.add_argument("--out", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_PATH)
    parser.add_argument("--note-out", type=Path, default=INSTANCE_NOTE_PATH)
    parser.add_argument("--command-out", type=Path, default=DEFAULT_COMMAND_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_preflight(
        args.repo_root,
        args.iter130_report,
        args.iter130_result,
        args.iter130_note,
        args.out,
        args.markdown_out,
        args.note_out,
        args.command_out,
    )
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
