from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter115_hugsim_support_core_monitor_set_ordering"
    / "analyze_support_core_monitor_set_ordering.py"
)
SPEC = importlib.util.spec_from_file_location("iter115_ordering", MODULE_PATH)
assert SPEC is not None
ordering = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ordering)


def test_ordering_labels_temporal_buckets() -> None:
    assert ordering.temporal_label(0.5) == "short_lead"
    assert ordering.temporal_label(1.5) == "medium_lead"
    assert ordering.temporal_label(1.50001) == "long_lead"


def test_ordering_labels_object_set_distance() -> None:
    assert ordering.object_set_label(3.0) == "nearest_actor_match"
    assert ordering.object_set_label(6.0) == "nearest_actor_ambiguous"
    assert ordering.object_set_label(6.00001) == "nearest_actor_mismatch"


def test_ordering_combined_labels_selection_cases() -> None:
    assert ordering.combined_label(7.0, 1, 1) == "whole_set_mismatch_selected_nearest"
    assert ordering.combined_label(7.0, 2, 1) == "whole_set_mismatch_selected_not_nearest"
    assert ordering.combined_label(5.0, 2, 1) == "nonselected_collision_candidate_available"
    assert ordering.combined_label(5.0, 1, 1) == "selected_collision_candidate"


def test_iter112_proof_builds_complete_ordering_report() -> None:
    repo = Path(__file__).resolve().parents[1]
    report = ordering.build_report(
        repo
        / "experiments"
        / "iter113_hugsim_support_core_actor_match_audit"
        / "proof-actor-match"
        / "support_core_actor_match_report.json",
        repo
        / "experiments"
        / "iter114_hugsim_support_core_mismatch_geometry_decomposition"
        / "proof-geometry"
        / "support_core_mismatch_geometry_report.json",
        repo / "experiments" / "iter112_hugsim_support_core_batch_execution" / "proof-execution",
    )

    assert report["verdict"] == ordering.COMPLETE_VERDICT
    assert not report["infra_problems"]
    assert report["summary"]["row_count"] == 8
    assert report["summary"]["problem_row_count"] == 0
    assert sum(report["summary"]["combined_label_counts"].values()) == 8
