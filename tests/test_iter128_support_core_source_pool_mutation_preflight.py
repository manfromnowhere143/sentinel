from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter128_support_core_source_pool_mutation_preflight"
    / "generate_support_core_source_pool_mutation_preflight.py"
)
SPEC = importlib.util.spec_from_file_location("iter128_preflight", MODULE_PATH)
assert SPEC is not None
preflight = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(preflight)


def test_operator_library_covers_expected_mutation_families() -> None:
    assert set(preflight.OPERATOR_LIBRARY) == {
        "unsupported_nearest_reference_pressure",
        "introduce_pre_fire_support_reference_control",
        "post_fire_support_delay_pressure",
        "shift_post_fire_evidence_to_pre_fire_control",
        "support_drift_outside_band_sweep",
        "support_band_border_continuity_control",
        "support_loss_gap_sweep",
        "same_object_visibility_continuity_control",
    }


def test_committed_inputs_build_complete_preflight() -> None:
    repo = Path(__file__).resolve().parents[1]
    report = preflight.build_report(
        repo / preflight.ITER126_REPORT_PATH,
        repo / preflight.ITER126_RESULT_PATH,
        repo / preflight.ITER126_NOTE_PATH,
        repo / preflight.ITER127_RESULT_PATH,
        repo / preflight.ITER127_NOTE_PATH,
    )

    assert report["verdict"] == preflight.COMPLETE_VERDICT
    assert not report["problems"]
    assert report["summary"]["candidate_count"] == 10
    assert report["summary"]["source_pool_count"] == 10
    assert report["summary"]["mutation_operator_count"] == 8
    assert report["summary"]["candidate_operator_binding_count"] == 10
    assert report["summary"]["candidate_without_source_pool_count"] == 0
    assert report["summary"]["candidate_without_operator_binding_count"] == 0
    assert report["summary"]["missing_source_slot_count"] == 0


def test_each_candidate_has_one_source_pool_and_one_binding() -> None:
    repo = Path(__file__).resolve().parents[1]
    report = preflight.build_report(
        repo / preflight.ITER126_REPORT_PATH,
        repo / preflight.ITER126_RESULT_PATH,
        repo / preflight.ITER126_NOTE_PATH,
        repo / preflight.ITER127_RESULT_PATH,
        repo / preflight.ITER127_NOTE_PATH,
    )
    candidate_ids = {candidate["candidate_id"] for candidate in report["source_pools"]}
    binding_ids = {binding["candidate_id"] for binding in report["candidate_operator_bindings"]}

    assert len(candidate_ids) == 10
    assert candidate_ids == binding_ids


def test_source_pools_operators_and_bindings_are_inert() -> None:
    repo = Path(__file__).resolve().parents[1]
    report = preflight.build_report(
        repo / preflight.ITER126_REPORT_PATH,
        repo / preflight.ITER126_RESULT_PATH,
        repo / preflight.ITER126_NOTE_PATH,
        repo / preflight.ITER127_RESULT_PATH,
        repo / preflight.ITER127_NOTE_PATH,
    )
    all_items = (
        report["source_pools"]
        + report["mutation_operators"]
        + report["candidate_operator_bindings"]
    )

    for item in all_items:
        for field in preflight.PREFLIGHT_FALSE_AUTHORIZATION_FIELDS:
            assert item[field] is False
        assert preflight.check_forbidden_keys(item) == []
