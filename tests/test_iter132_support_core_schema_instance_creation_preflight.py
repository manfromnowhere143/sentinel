from __future__ import annotations

import importlib.util
from collections import Counter
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter132_support_core_schema_instance_creation_preflight"
    / "generate_support_core_schema_instance_creation_preflight.py"
)
SPEC = importlib.util.spec_from_file_location("iter132_instance", MODULE_PATH)
assert SPEC is not None
instance_preflight = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(instance_preflight)


def build_committed_report() -> dict:
    repo = Path(__file__).resolve().parents[1]
    return instance_preflight.build_report(
        repo,
        repo / instance_preflight.ITER130_REPORT_PATH,
        repo / instance_preflight.ITER130_RESULT_PATH,
        repo / instance_preflight.ITER130_NOTE_PATH,
    )


def test_instance_templates_cover_three_artifact_types() -> None:
    repo = Path(__file__).resolve().parents[1]
    iter130_report, problems = instance_preflight.load_json(
        repo / instance_preflight.ITER130_REPORT_PATH,
        "iter130-report",
    )
    assert not problems
    templates = instance_preflight.build_instance_templates(iter130_report["schema_specs"])

    assert [template["artifact_type"] for template in templates] == list(
        instance_preflight.ARTIFACT_TYPES
    )
    assert {template["template_id"] for template in templates} == {
        "scinst_template_scenario_spec_v1",
        "scinst_template_provenance_receipt_v1",
        "scinst_template_validation_manifest_v1",
    }
    assert all(template["template_only"] is True for template in templates)


def test_committed_inputs_build_complete_preflight() -> None:
    report = build_committed_report()

    assert report["verdict"] == instance_preflight.COMPLETE_VERDICT
    assert not report["problems"]
    assert report["summary"]["schema_spec_count"] == 3
    assert report["summary"]["schema_binding_count"] == 30
    assert report["summary"]["instance_template_count"] == 3
    assert report["summary"]["validator_contract_count"] == 1
    assert report["summary"]["instance_binding_count"] == 30
    assert report["summary"]["true_authorization_count"] == 0
    assert report["summary"]["forbidden_key_count"] == 0
    assert report["summary"]["existing_instance_bound_path_count"] == 0


def test_validator_contract_is_inert_and_complete() -> None:
    report = build_committed_report()
    validator = report["validator_contract"]

    assert validator["validation_does_not_create_paths"] is True
    assert validator["reserved_path_nonexistence_required"] is True
    assert tuple(validator["required_checks"]) == instance_preflight.VALIDATOR_CHECKS
    for field in instance_preflight.PREFLIGHT_FALSE_AUTHORIZATION_FIELDS:
        assert validator[field] is False
    assert instance_preflight.check_forbidden_keys(validator) == []


def test_each_reservation_has_three_instance_template_bindings() -> None:
    report = build_committed_report()
    counts = Counter(
        binding["reservation_id"] for binding in report["instance_template_bindings"]
    )

    assert len(counts) == 10
    assert set(counts.values()) == {3}
    for binding in report["instance_template_bindings"]:
        assert binding["artifact_type"] in instance_preflight.ARTIFACT_TYPES
        assert binding["template_id"] == instance_preflight.template_id(binding["artifact_type"])
        assert binding["creation_status"] == "not_created"


def test_templates_and_bindings_are_inert() -> None:
    report = build_committed_report()
    items = (
        report["schema_instance_templates"]
        + [report["validator_contract"]]
        + report["instance_template_bindings"]
    )

    for item in items:
        for field in instance_preflight.PREFLIGHT_FALSE_AUTHORIZATION_FIELDS:
            assert item[field] is False
        assert instance_preflight.check_forbidden_keys(item) == []


def test_no_reserved_paths_are_created_by_instance_preflight() -> None:
    repo = Path(__file__).resolve().parents[1]
    report = build_committed_report()
    paths = [
        binding["reserved_relative_path"]
        for binding in report["instance_template_bindings"]
    ]

    assert len(paths) == 30
    assert len(set(paths)) == 30
    assert all(path.startswith(f"{instance_preflight.RESERVED_ROOT}/") for path in paths)
    assert all(not (repo / path).exists() for path in paths)
