#!/usr/bin/env python3
"""Iteration 130 support-core generated-artifact schema preflight."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ITER129_VERDICT = "SUPPORT_CORE_ARTIFACT_NAMING_PREFLIGHT_COMPLETE"
COMPLETE_VERDICT = "SUPPORT_CORE_ARTIFACT_SCHEMA_PREFLIGHT_COMPLETE"
INFRA_NULL_VERDICT = "SUPPORT_CORE_ARTIFACT_SCHEMA_PREFLIGHT_INFRA_NULL"
EXPECTED_RESERVATION_COUNT = 10
EXPECTED_RESERVED_PATH_COUNT = 30
EXPECTED_SCHEMA_COUNT = 3
EXPECTED_BINDING_COUNT = 30
SCHEMA_VERSION = "iter130.support_core_artifact_schema.v1"
RESERVED_ROOT = "future_artifacts/support_core_blindspot_generation"
ARTIFACT_TYPES = ("scenario_spec", "provenance_receipt", "validation_manifest")
ITER129_REPORT_PATH = Path(
    "experiments/iter129_support_core_artifact_naming_preflight/proof-naming/"
    "support_core_artifact_naming_preflight_report.json"
)
ITER129_RESULT_PATH = Path("experiments/iter129_support_core_artifact_naming_preflight/RESULT.md")
ITER129_NOTE_PATH = Path(
    "docs/research/SUPPORT_CORE_ARTIFACT_NAMING_PREFLIGHT_2026-07-14.md"
)
ARTIFACT_SCHEMA_NOTE_PATH = Path(
    "docs/research/SUPPORT_CORE_ARTIFACT_SCHEMA_PREFLIGHT_2026-07-14.md"
)
DEFAULT_PROOF_DIR = Path("experiments/iter130_support_core_artifact_schema_preflight/proof-schema")
DEFAULT_REPORT_PATH = DEFAULT_PROOF_DIR / "support_core_artifact_schema_preflight_report.json"
DEFAULT_MARKDOWN_PATH = DEFAULT_PROOF_DIR / "support_core_artifact_schema_preflight.md"
DEFAULT_COMMAND_PATH = DEFAULT_PROOF_DIR / "generate_support_core_artifact_schema_preflight.command.txt"
BOUNDARY = (
    "generated-artifact schema and metadata preflight only; no reserved path creation, generated "
    "scenario artifact, scenario generation, execution-slot selection, GPU launch, HUGSIM run, "
    "learning/update step, repair, actor-causality, threshold-value, transfer upgrade, safety, "
    "deployment, robustness, benchmark, population-rate, HD-Score-invariance, real-world "
    "behavior, first-responder behavior, acquisition-value, retuning, production, commercial "
    "claim, or frontier-stack equivalence claim"
)
BOUNDARY_NEEDLES = (
    "reserved path is created",
    "no reserved path creation",
    "generated scenario artifact",
    "scenario generation",
    "HUGSIM run",
    "GPU launch",
    "learning/update",
    "retuning",
    "repair",
    "safety",
    "deployment",
    "production",
    "commercial claim",
)
ITER129_FALSE_AUTHORIZATION_FIELDS = (
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
COMMON_IDENTITY_FIELDS = (
    "candidate_id",
    "source_pool_id",
    "operator_id",
    "binding_id",
    "reservation_id",
    "artifact_stem",
    "reserved_relative_path",
    "artifact_type",
)
COMMON_BOUNDARY_FIELDS = (
    "creation_hypothesis_id",
    "creation_authorized",
    "reserved_path_creation_authorized",
    "scenario_generation_authorized",
    "execution_slot_selection_authorized",
    "gpu_authorized",
    "hugsim_run_authorized",
    "learning_update_authorized",
    "repair_authorized",
    "safety_claim_authorized",
    "deployment_authorized",
    "production_authorized",
    "commercial_claim_authorized",
    "claim_boundary",
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
PAYLOAD_SECTIONS: dict[str, tuple[str, ...]] = {
    "scenario_spec": (
        "symbolic_scene_blueprint",
        "mutation_operator_parameters",
        "source_context_summary",
        "validation_expectations",
    ),
    "provenance_receipt": (
        "source_manifest_references",
        "operator_binding_references",
        "reservation_integrity_checks",
        "future_creation_receipt",
    ),
    "validation_manifest": (
        "schema_checks",
        "path_checks",
        "boundary_checks",
        "duplicate_handling_checks",
        "future_gate_checks",
    ),
}


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


def validate_iter129_report(report: dict[str, Any], problems: list[str]) -> None:
    if report.get("verdict") != ITER129_VERDICT:
        problems.append(f"iter129-verdict-mismatch:{report.get('verdict')!r}")
    summary = report.get("summary")
    if not isinstance(summary, dict):
        problems.append("iter129-summary-not-dict")
        return
    expected = {
        "artifact_reservation_count": EXPECTED_RESERVATION_COUNT,
        "reserved_relative_path_count": EXPECTED_RESERVED_PATH_COUNT,
        "true_authorization_count": 0,
        "existing_reserved_path_count": 0,
        "duplicate_reserved_path_count": 0,
        "bad_reserved_path_count": 0,
        "forbidden_key_count": 0,
        "forbidden_text_count": 0,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            problems.append(f"iter129-summary-{key}-mismatch:{summary.get(key)!r}!={value!r}")
    if summary.get("reservation_type_counts") != {artifact_type: 10 for artifact_type in ARTIFACT_TYPES}:
        problems.append(
            "iter129-reservation-type-counts-mismatch:"
            f"{summary.get('reservation_type_counts')!r}"
        )


def require_reservations(report: dict[str, Any], problems: list[str]) -> list[dict[str, Any]]:
    value = report.get("artifact_reservations")
    if not isinstance(value, list):
        problems.append("iter129-artifact_reservations-not-list")
        return []
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            problems.append(f"iter129-reservation-item-not-dict:{index}")
            continue
        rows.append(item)
    if len(rows) != EXPECTED_RESERVATION_COUNT:
        problems.append(
            f"iter129-artifact_reservations-count-mismatch:{len(rows)}!="
            f"{EXPECTED_RESERVATION_COUNT}"
        )
    return rows


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


def validate_reservations(
    repo_root: Path,
    reservations: list[dict[str, Any]],
    problems: list[str],
) -> dict[str, int]:
    true_authorization_count = 0
    missing_reservation_content_count = 0
    bad_reserved_path_count = 0
    existing_reserved_path_count = 0
    forbidden_key_count = 0
    all_paths: list[str] = []
    seen_reservation_ids: set[str] = set()
    for reservation in reservations:
        reservation_id = reservation.get("reservation_id")
        if not isinstance(reservation_id, str) or not reservation_id:
            missing_reservation_content_count += 1
            problems.append(f"reservation-id-missing:{reservation_id!r}")
        elif reservation_id in seen_reservation_ids:
            problems.append(f"reservation-id-duplicate:{reservation_id}")
        else:
            seen_reservation_ids.add(reservation_id)
        for field in (
            "candidate_id",
            "source_pool_id",
            "operator_id",
            "binding_id",
            "artifact_stem",
            "reserved_destination_root",
            "reserved_relative_paths",
        ):
            if reservation.get(field) in (None, "", [], {}):
                missing_reservation_content_count += 1
                problems.append(f"reservation-missing-{field}:{reservation_id}")
        for field in ITER129_FALSE_AUTHORIZATION_FIELDS:
            if reservation.get(field) is not False:
                true_authorization_count += int(reservation.get(field) is True)
                problems.append(f"reservation-auth-not-false:{reservation_id}:{field}")
        relpaths = reservation.get("reserved_relative_paths")
        if not isinstance(relpaths, dict):
            bad_reserved_path_count += 1
            problems.append(f"reservation-paths-not-dict:{reservation_id}")
            continue
        if set(relpaths) != set(ARTIFACT_TYPES):
            bad_reserved_path_count += 1
            problems.append(f"reservation-path-types-mismatch:{reservation_id}:{sorted(relpaths)}")
        for artifact_type, relpath in relpaths.items():
            path_text = str(relpath)
            all_paths.append(path_text)
            if artifact_type not in ARTIFACT_TYPES:
                bad_reserved_path_count += 1
                problems.append(f"reservation-unknown-artifact-type:{reservation_id}:{artifact_type}")
            if not path_text.startswith(f"{RESERVED_ROOT}/"):
                bad_reserved_path_count += 1
                problems.append(f"reservation-path-outside-root:{reservation_id}:{path_text}")
            if (repo_root / path_text).exists():
                existing_reserved_path_count += 1
                problems.append(f"reservation-path-exists:{reservation_id}:{path_text}")
        forbidden_keys = check_forbidden_keys(reservation, "reservation")
        forbidden_key_count += len(forbidden_keys)
        problems.extend(forbidden_keys)
    duplicate_path_count = sum(count - 1 for count in Counter(all_paths).values() if count > 1)
    if duplicate_path_count:
        problems.append(f"reserved-path-duplicate-count:{duplicate_path_count}")
    return {
        "reservation_true_authorization_count": true_authorization_count,
        "missing_reservation_content_count": missing_reservation_content_count,
        "bad_reserved_path_count": bad_reserved_path_count,
        "existing_reserved_path_count": existing_reserved_path_count,
        "duplicate_reserved_path_count": duplicate_path_count,
        "reservation_forbidden_key_count": forbidden_key_count,
        "reserved_relative_path_count": len(all_paths),
    }


def schema_id(artifact_type: str) -> str:
    return f"scschema_{artifact_type}_v1"


def build_schema_specs() -> list[dict[str, Any]]:
    schemas: list[dict[str, Any]] = []
    for artifact_type in ARTIFACT_TYPES:
        schemas.append(
            {
                "schema_id": schema_id(artifact_type),
                "schema_version": SCHEMA_VERSION,
                "artifact_type": artifact_type,
                "required_top_level_fields": [
                    "schema_version",
                    "metadata",
                    "identity",
                    "boundary",
                    "payload",
                ],
                "required_metadata_fields": [
                    "schema_id",
                    "artifact_type",
                    "created_by_iteration",
                    "source_iteration",
                    "schema_contract_id",
                ],
                "required_identity_fields": list(COMMON_IDENTITY_FIELDS),
                "required_boundary_fields": list(COMMON_BOUNDARY_FIELDS),
                "allowed_payload_sections": list(PAYLOAD_SECTIONS[artifact_type]),
                "forbidden_fields": list(FORBIDDEN_FIELDS),
                "validation_rules": [
                    "reserved_relative_path must match the iteration-129 reservation binding",
                    "identity fields must match the reservation before any future file is written",
                    "boundary booleans must remain false unless a future HYPOTHESIS.md changes scope",
                    "payload sections are structural names only in this preflight",
                ],
                **false_authorizations(),
            }
        )
    return schemas


def build_schema_bindings(reservations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    bindings: list[dict[str, Any]] = []
    for reservation_index, reservation in enumerate(
        sorted(reservations, key=lambda item: str(item.get("reservation_id"))),
        start=1,
    ):
        relpaths = reservation["reserved_relative_paths"]
        for artifact_type in ARTIFACT_TYPES:
            bindings.append(
                {
                    "schema_binding_id": (
                        f"scschema_bind_{reservation_index:03d}_{artifact_type}_"
                        f"{reservation['reservation_id']}"
                    ),
                    "reservation_id": reservation["reservation_id"],
                    "candidate_id": reservation["candidate_id"],
                    "source_pool_id": reservation["source_pool_id"],
                    "operator_id": reservation["operator_id"],
                    "candidate_operator_binding_id": reservation["binding_id"],
                    "artifact_stem": reservation["artifact_stem"],
                    "artifact_type": artifact_type,
                    "reserved_relative_path": relpaths[artifact_type],
                    "schema_id": schema_id(artifact_type),
                    "schema_version": SCHEMA_VERSION,
                    "file_creation_rule": "fresh pre-registration required before writing this path",
                    "schema_binding_authorizes_file_creation": False,
                    **false_authorizations(),
                }
            )
    return bindings


def count_true_authorizations(
    items: list[dict[str, Any]],
    auth_fields: tuple[str, ...],
    problems: list[str],
    label: str,
) -> int:
    true_count = 0
    for item in items:
        item_id = (
            item.get("schema_id")
            or item.get("schema_binding_id")
            or item.get("reservation_id")
            or "unknown"
        )
        for field in auth_fields:
            if item.get(field) is not False:
                true_count += int(item.get(field) is True)
                problems.append(f"{label}-auth-not-false:{item_id}:{field}")
    return true_count


def validate_schema_specs(schemas: list[dict[str, Any]], problems: list[str]) -> dict[str, int]:
    missing_schema_content_count = 0
    schema_forbidden_key_count = 0
    if len(schemas) != EXPECTED_SCHEMA_COUNT:
        problems.append(f"schema-count-mismatch:{len(schemas)}!={EXPECTED_SCHEMA_COUNT}")
    by_type = {str(schema.get("artifact_type")): schema for schema in schemas}
    if set(by_type) != set(ARTIFACT_TYPES):
        problems.append(f"schema-artifact-types-mismatch:{sorted(by_type)}")
    for schema in schemas:
        schema_label = schema.get("schema_id", "unknown")
        for field in REQUIRED_SCHEMA_FIELDS:
            if schema.get(field) in (None, "", [], {}):
                missing_schema_content_count += 1
                problems.append(f"schema-missing-{field}:{schema_label}")
        if schema.get("schema_version") != SCHEMA_VERSION:
            problems.append(f"schema-version-mismatch:{schema_label}:{schema.get('schema_version')!r}")
        if schema.get("schema_id") != schema_id(str(schema.get("artifact_type"))):
            problems.append(f"schema-id-mismatch:{schema_label}")
        if not set(COMMON_IDENTITY_FIELDS).issubset(set(schema.get("required_identity_fields", []))):
            missing_schema_content_count += 1
            problems.append(f"schema-identity-fields-incomplete:{schema_label}")
        if not set(COMMON_BOUNDARY_FIELDS).issubset(set(schema.get("required_boundary_fields", []))):
            missing_schema_content_count += 1
            problems.append(f"schema-boundary-fields-incomplete:{schema_label}")
        artifact_type = str(schema.get("artifact_type"))
        if tuple(schema.get("allowed_payload_sections", [])) != PAYLOAD_SECTIONS.get(artifact_type):
            problems.append(f"schema-payload-sections-mismatch:{schema_label}")
        if tuple(schema.get("forbidden_fields", [])) != FORBIDDEN_FIELDS:
            problems.append(f"schema-forbidden-fields-mismatch:{schema_label}")
        forbidden_keys = check_forbidden_keys(schema, "schema")
        schema_forbidden_key_count += len(forbidden_keys)
        problems.extend(forbidden_keys)
    return {
        "missing_schema_content_count": missing_schema_content_count,
        "schema_forbidden_key_count": schema_forbidden_key_count,
    }


def validate_schema_bindings(
    repo_root: Path,
    reservations: list[dict[str, Any]],
    schemas: list[dict[str, Any]],
    bindings: list[dict[str, Any]],
    problems: list[str],
) -> dict[str, int]:
    missing_binding_content_count = 0
    bad_schema_reference_count = 0
    binding_forbidden_key_count = 0
    existing_bound_path_count = 0
    reservation_by_id = {str(reservation.get("reservation_id")): reservation for reservation in reservations}
    schema_by_id = {str(schema.get("schema_id")): schema for schema in schemas}
    bindings_by_reservation: dict[str, list[dict[str, Any]]] = defaultdict(list)
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
        reservation_id = str(binding.get("reservation_id"))
        artifact_type = str(binding.get("artifact_type"))
        reservation = reservation_by_id.get(reservation_id)
        if reservation is None:
            bad_schema_reference_count += 1
            problems.append(f"schema-binding-missing-reservation:{binding_id}:{reservation_id}")
        else:
            bindings_by_reservation[reservation_id].append(binding)
            expected_path = reservation["reserved_relative_paths"].get(artifact_type)
            if binding.get("reserved_relative_path") != expected_path:
                bad_schema_reference_count += 1
                problems.append(f"schema-binding-path-mismatch:{binding_id}")
        if str(binding.get("schema_id")) not in schema_by_id:
            bad_schema_reference_count += 1
            problems.append(f"schema-binding-missing-schema:{binding_id}:{binding.get('schema_id')}")
        if binding.get("schema_id") != schema_id(artifact_type):
            bad_schema_reference_count += 1
            problems.append(f"schema-binding-schema-type-mismatch:{binding_id}")
        relpath = str(binding.get("reserved_relative_path"))
        if (repo_root / relpath).exists():
            existing_bound_path_count += 1
            problems.append(f"schema-binding-path-exists:{binding_id}:{relpath}")
        forbidden_keys = check_forbidden_keys(binding, "schema_binding")
        binding_forbidden_key_count += len(forbidden_keys)
        problems.extend(forbidden_keys)
    for reservation_id in reservation_by_id:
        artifact_types = {str(binding.get("artifact_type")) for binding in bindings_by_reservation[reservation_id]}
        if artifact_types != set(ARTIFACT_TYPES):
            bad_schema_reference_count += 1
            problems.append(f"schema-binding-reservation-type-coverage:{reservation_id}:{sorted(artifact_types)}")
    return {
        "missing_binding_content_count": missing_binding_content_count,
        "bad_schema_reference_count": bad_schema_reference_count,
        "binding_forbidden_key_count": binding_forbidden_key_count,
        "existing_bound_path_count": existing_bound_path_count,
    }


def summarize(
    reservations: list[dict[str, Any]],
    schemas: list[dict[str, Any]],
    bindings: list[dict[str, Any]],
    reservation_counts: dict[str, int],
    schema_counts: dict[str, int],
    binding_counts: dict[str, int],
    preflight_true_authorization_count: int,
) -> dict[str, Any]:
    return {
        "artifact_reservation_count": len(reservations),
        "reserved_destination_root": RESERVED_ROOT,
        "reserved_relative_path_count": reservation_counts["reserved_relative_path_count"],
        "schema_spec_count": len(schemas),
        "schema_artifact_types": [schema.get("artifact_type") for schema in schemas],
        "schema_binding_count": len(bindings),
        "schema_binding_type_counts": {
            artifact_type: sum(1 for item in bindings if item.get("artifact_type") == artifact_type)
            for artifact_type in ARTIFACT_TYPES
        },
        "reservation_schema_binding_counts": {
            reservation_id: count
            for reservation_id, count in sorted(
                Counter(str(binding.get("reservation_id")) for binding in bindings).items()
            )
        },
        "true_authorization_count": (
            reservation_counts["reservation_true_authorization_count"]
            + preflight_true_authorization_count
        ),
        "missing_reservation_content_count": reservation_counts["missing_reservation_content_count"],
        "missing_schema_content_count": schema_counts["missing_schema_content_count"],
        "missing_binding_content_count": binding_counts["missing_binding_content_count"],
        "bad_reserved_path_count": reservation_counts["bad_reserved_path_count"],
        "existing_reserved_path_count": reservation_counts["existing_reserved_path_count"],
        "existing_bound_path_count": binding_counts["existing_bound_path_count"],
        "duplicate_reserved_path_count": reservation_counts["duplicate_reserved_path_count"],
        "bad_schema_reference_count": binding_counts["bad_schema_reference_count"],
        "forbidden_key_count": (
            reservation_counts["reservation_forbidden_key_count"]
            + schema_counts["schema_forbidden_key_count"]
            + binding_counts["binding_forbidden_key_count"]
        ),
    }


def choose_verdict(problems: list[str], summary: dict[str, Any]) -> str:
    if problems:
        return INFRA_NULL_VERDICT
    expected = {
        "artifact_reservation_count": EXPECTED_RESERVATION_COUNT,
        "reserved_relative_path_count": EXPECTED_RESERVED_PATH_COUNT,
        "schema_spec_count": EXPECTED_SCHEMA_COUNT,
        "schema_binding_count": EXPECTED_BINDING_COUNT,
        "true_authorization_count": 0,
        "missing_reservation_content_count": 0,
        "missing_schema_content_count": 0,
        "missing_binding_content_count": 0,
        "bad_reserved_path_count": 0,
        "existing_reserved_path_count": 0,
        "existing_bound_path_count": 0,
        "duplicate_reserved_path_count": 0,
        "bad_schema_reference_count": 0,
        "forbidden_key_count": 0,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            return INFRA_NULL_VERDICT
    if summary.get("schema_artifact_types") != list(ARTIFACT_TYPES):
        return INFRA_NULL_VERDICT
    if summary.get("schema_binding_type_counts") != {
        artifact_type: EXPECTED_RESERVATION_COUNT for artifact_type in ARTIFACT_TYPES
    }:
        return INFRA_NULL_VERDICT
    if set(summary.get("reservation_schema_binding_counts", {}).values()) != {len(ARTIFACT_TYPES)}:
        return INFRA_NULL_VERDICT
    return COMPLETE_VERDICT


def build_report(
    repo_root: Path,
    iter129_report_path: Path,
    iter129_result_path: Path,
    iter129_note_path: Path,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    problems: list[str] = []
    iter129_report, report_problems = load_json(iter129_report_path, "iter129-report")
    iter129_result, result_problems = load_text(iter129_result_path, "iter129-result")
    iter129_note, note_problems = load_text(iter129_note_path, "iter129-note")
    problems.extend(report_problems)
    problems.extend(result_problems)
    problems.extend(note_problems)

    validate_iter129_report(iter129_report, problems)
    require_contains(problems, "iter129-result", iter129_result, ITER129_VERDICT)
    require_boundary(problems, "iter129-note", iter129_note)
    reservations = require_reservations(iter129_report, problems)
    reservation_counts = validate_reservations(repo_root, reservations, problems)

    if problems:
        schemas: list[dict[str, Any]] = []
        bindings: list[dict[str, Any]] = []
        schema_counts = {"missing_schema_content_count": 0, "schema_forbidden_key_count": 0}
        binding_counts = {
            "missing_binding_content_count": 0,
            "bad_schema_reference_count": 0,
            "binding_forbidden_key_count": 0,
            "existing_bound_path_count": 0,
        }
        preflight_true_authorization_count = 0
    else:
        schemas = build_schema_specs()
        bindings = build_schema_bindings(reservations)
        schema_counts = validate_schema_specs(schemas, problems)
        binding_counts = validate_schema_bindings(repo_root, reservations, schemas, bindings, problems)
        preflight_true_authorization_count = count_true_authorizations(
            schemas + bindings,
            PREFLIGHT_FALSE_AUTHORIZATION_FIELDS,
            problems,
            "schema-preflight",
        )
    summary = summarize(
        reservations,
        schemas,
        bindings,
        reservation_counts,
        schema_counts,
        binding_counts,
        preflight_true_authorization_count,
    )
    return {
        "iteration": 130,
        "inputs": {
            "iter129_report": str(iter129_report_path),
            "iter129_result": str(iter129_result_path),
            "iter129_note": str(iter129_note_path),
        },
        "summary": summary,
        "schema_specs": schemas,
        "schema_bindings": bindings,
        "future_creation_requirements": [
            "fresh HYPOTHESIS.md authorizes creation of reserved paths",
            "schema instance validator checks metadata and boundary fields before creation",
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
        "# Iteration 130 - support-core generated-artifact schema preflight",
        "",
        f"Verdict: `{report['verdict']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Schema specs", ""])
    for schema in report["schema_specs"]:
        lines.extend(
            [
                f"### `{schema['schema_id']}`",
                "",
                f"- artifact type: `{schema['artifact_type']}`",
                f"- schema version: `{schema['schema_version']}`",
                "- allowed payload sections:",
            ]
        )
        for section in schema["allowed_payload_sections"]:
            lines.append(f"  - `{section}`")
        lines.append("")
    lines.extend(["## Schema bindings", ""])
    for binding in report["schema_bindings"]:
        lines.extend(
            [
                f"### `{binding['schema_binding_id']}`",
                "",
                f"- reservation: `{binding['reservation_id']}`",
                f"- artifact type: `{binding['artifact_type']}`",
                f"- schema: `{binding['schema_id']}`",
                f"- reserved path: `{binding['reserved_relative_path']}`",
                f"- creation authorized: `{binding['creation_authorized']}`",
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
        "# HUGSIM support-core generated-artifact schema preflight",
        "",
        "Status: iteration-130 schema/metadata preflight note. This defines schema contracts",
        "and path-to-schema bindings only; it authorizes no reserved path creation, generated",
        "scenario artifact, scenario generation, execution-slot selection, HUGSIM run, GPU launch,",
        "learning/update step, retuning, repair, safety, deployment, production, or commercial claim.",
        "",
        "## Source",
        "",
        "- Iteration 129 naming/destination proof:",
        "  [`support_core_artifact_naming_preflight_report.json`](../../experiments/iter129_support_core_artifact_naming_preflight/proof-naming/support_core_artifact_naming_preflight_report.json)",
        "- Iteration 130 proof:",
        "  [`support_core_artifact_schema_preflight_report.json`](../../experiments/iter130_support_core_artifact_schema_preflight/proof-schema/support_core_artifact_schema_preflight_report.json)",
        "",
        "## Schema Rule",
        "",
        "Each reserved path from iteration 129 is bound to exactly one schema. The three schema",
        "types are `scenario_spec`, `provenance_receipt`, and `validation_manifest`. The schema",
        "contract names required identity, metadata, boundary, payload, and forbidden fields, but",
        "does not write any reserved path or generated artifact.",
        "",
        "## Schema Specs",
        "",
    ]
    for schema in report["schema_specs"]:
        lines.extend(
            [
                f"### `{schema['schema_id']}`",
                "",
                f"- artifact type: `{schema['artifact_type']}`",
                f"- version: `{schema['schema_version']}`",
                "- required identity fields:",
            ]
        )
        for field in schema["required_identity_fields"]:
            lines.append(f"  - `{field}`")
        lines.append("- required boundary fields:")
        for field in schema["required_boundary_fields"]:
            lines.append(f"  - `{field}`")
        lines.append("- allowed payload sections:")
        for section in schema["allowed_payload_sections"]:
            lines.append(f"  - `{section}`")
        lines.append("")
    lines.extend(["## Binding Counts", ""])
    for artifact_type, count in report["summary"]["schema_binding_type_counts"].items():
        lines.append(f"- `{artifact_type}`: `{count}`")
    lines.extend(["", "## Future Gates", ""])
    for requirement in report["future_creation_requirements"]:
        lines.append(f"- {requirement}")
    lines.extend(["", "## Claim Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def write_command(path: Path) -> None:
    command = (
        "python3 experiments/iter130_support_core_artifact_schema_preflight/"
        "generate_support_core_artifact_schema_preflight.py\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(command)


def run_preflight(
    repo_root: Path,
    iter129_report: Path,
    iter129_result: Path,
    iter129_note: Path,
    out: Path,
    markdown_out: Path,
    note_out: Path,
    command_out: Path,
) -> dict[str, Any]:
    report = build_report(repo_root, iter129_report, iter129_result, iter129_note)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(report, markdown_out)
    write_note(report, note_out)
    write_command(command_out)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--iter129-report", type=Path, default=ITER129_REPORT_PATH)
    parser.add_argument("--iter129-result", type=Path, default=ITER129_RESULT_PATH)
    parser.add_argument("--iter129-note", type=Path, default=ITER129_NOTE_PATH)
    parser.add_argument("--out", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_PATH)
    parser.add_argument("--note-out", type=Path, default=ARTIFACT_SCHEMA_NOTE_PATH)
    parser.add_argument("--command-out", type=Path, default=DEFAULT_COMMAND_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_preflight(
        args.repo_root,
        args.iter129_report,
        args.iter129_result,
        args.iter129_note,
        args.out,
        args.markdown_out,
        args.note_out,
        args.command_out,
    )
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
