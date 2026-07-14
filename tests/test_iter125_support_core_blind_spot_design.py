from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter125_support_core_blind_spot_scenario_design"
    / "generate_support_core_blind_spot_design.py"
)
SPEC = importlib.util.spec_from_file_location("iter125_design", MODULE_PATH)
assert SPEC is not None
design = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(design)


def test_rank_condition_labels_nearest_and_not_nearest() -> None:
    assert design.selected_rank_condition([{"selected_is_fire_nearest": True}]) == "selected_nearest"
    assert design.selected_rank_condition([{"selected_is_fire_nearest": False}]) == "selected_not_nearest"
    assert (
        design.selected_rank_condition(
            [{"selected_is_fire_nearest": True}, {"selected_is_fire_nearest": False}]
        )
        == "selected_rank_mixed"
    )


def test_timing_gap_class_branches() -> None:
    assert (
        design.timing_gap_class(
            [{"support_lifecycle_label": "pre_fire_object_absent_at_fire", "fire_minus_last_support_s": 4.0}]
        )
        == "measured_support_gap"
    )
    assert (
        design.timing_gap_class(
            [{"support_lifecycle_label": "post_fire_support_only_far_support", "fire_minus_last_support_s": None}]
        )
        == "post_fire_support"
    )
    assert design.timing_gap_class([{"support_lifecycle_label": "never_supported_reference"}]) == "no_pre_fire_support"


def test_committed_inputs_build_complete_design() -> None:
    repo = Path(__file__).resolve().parents[1]
    report = design.build_report(
        repo / design.ITER121_REPORT_PATH,
        repo / design.ITER122_RESULT_PATH,
        repo / design.ITER123_RESULT_PATH,
        repo / design.ITER124_RESULT_PATH,
        repo / design.SUPPORT_CORE_NOTE_PATH,
    )

    assert report["verdict"] == design.COMPLETE_VERDICT
    assert not report["problems"]
    assert report["summary"]["row_count"] == 8
    assert report["summary"]["covered_row_count"] == 8
    assert report["summary"]["archetype_count"] == 5
    assert report["summary"]["duplicate_covered_slot_count"] == 0
    assert report["summary"]["missing_covered_slot_count"] == 0
    assert all(archetype["candidate_generation_knobs"] for archetype in report["archetypes"])
    assert all(archetype["future_validation_gates"] for archetype in report["archetypes"])
