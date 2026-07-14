from __future__ import annotations

import importlib.util
from collections import Counter
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter130_support_core_artifact_schema_preflight"
    / "generate_support_core_artifact_schema_preflight.py"
)
SPEC = importlib.util.spec_from_file_location("iter130_schema", MODULE_PATH)
assert SPEC is not None
schema_preflight = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(schema_preflight)


def build_committed_report() -> dict:
    repo = Path(__file__).resolve().parents[1]
    return schema_preflight.build_report(
        repo,
        repo / schema_preflight.ITER129_REPORT_PATH,
        repo / schema_preflight.ITER129_RESULT_PATH,
        repo / schema_preflight.ITER129_NOTE_PATH,
    )


def test_schema_library_covers_three_artifact_types() -> None:
    schemas = schema_preflight.build_schema_specs()

    assert [schema["artifact_type"] for schema in schemas] == list(schema_preflight.ARTIFACT_TYPES)
    assert {schema["schema_id"] for schema in schemas} == {
        "scschema_scenario_spec_v1",
        "scschema_provenance_receipt_v1",
        "scschema_validation_manifest_v1",
    }


def test_committed_inputs_build_complete_preflight() -> None:
    report = build_committed_report()

    assert report["verdict"] == schema_preflight.COMPLETE_VERDICT
    assert not report["problems"]
    assert report["summary"]["artifact_reservation_count"] == 10
    assert report["summary"]["reserved_relative_path_count"] == 30
    assert report["summary"]["schema_spec_count"] == 3
    assert report["summary"]["schema_binding_count"] == 30
    assert report["summary"]["true_authorization_count"] == 0
    assert report["summary"]["forbidden_key_count"] == 0
    assert report["summary"]["existing_reserved_path_count"] == 0
    assert report["summary"]["existing_bound_path_count"] == 0


def test_each_reservation_has_three_schema_bindings() -> None:
    report = build_committed_report()
    counts = Counter(binding["reservation_id"] for binding in report["schema_bindings"])

    assert len(counts) == 10
    assert set(counts.values()) == {3}
    for reservation in report["schema_bindings"]:
        assert reservation["artifact_type"] in schema_preflight.ARTIFACT_TYPES
        assert reservation["schema_id"] == schema_preflight.schema_id(reservation["artifact_type"])


def test_schemas_and_bindings_are_inert() -> None:
    report = build_committed_report()

    for item in report["schema_specs"] + report["schema_bindings"]:
        for field in schema_preflight.PREFLIGHT_FALSE_AUTHORIZATION_FIELDS:
            assert item[field] is False
        assert schema_preflight.check_forbidden_keys(item) == []


def test_no_reserved_paths_are_created_by_schema_preflight() -> None:
    repo = Path(__file__).resolve().parents[1]
    report = build_committed_report()
    paths = [
        binding["reserved_relative_path"]
        for binding in report["schema_bindings"]
    ]

    assert len(paths) == 30
    assert len(set(paths)) == 30
    assert all(path.startswith(f"{schema_preflight.RESERVED_ROOT}/") for path in paths)
    assert all(not (repo / path).exists() for path in paths)
