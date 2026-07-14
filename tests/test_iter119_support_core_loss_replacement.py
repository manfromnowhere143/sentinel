from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter119_hugsim_support_core_loss_replacement_audit"
    / "analyze_support_core_loss_replacement.py"
)
SPEC = importlib.util.spec_from_file_location("iter119_replacement", MODULE_PATH)
assert SPEC is not None
replacement = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(replacement)


def test_replacement_label_pre_fire_absent_and_drifted() -> None:
    assert (
        replacement.replacement_label("pre_fire", False, True)
        == "pre_fire_lost_absent_selected_nearest"
    )
    assert (
        replacement.replacement_label("pre_fire", False, False)
        == "pre_fire_lost_absent_selected_not_nearest"
    )
    assert (
        replacement.replacement_label("pre_fire", True, True)
        == "pre_fire_drifted_selected_nearest"
    )
    assert (
        replacement.replacement_label("pre_fire", True, False)
        == "pre_fire_drifted_selected_not_nearest"
    )


def test_replacement_label_reference_and_post_fire() -> None:
    assert (
        replacement.replacement_label("never_before_collision", None, True)
        == "never_supported_reference_selected_nearest"
    )
    assert (
        replacement.replacement_label("post_fire_pre_collision", False, True)
        == "post_fire_support_selected_nearest"
    )
    assert (
        replacement.replacement_label("post_fire_pre_collision", False, False)
        == "post_fire_support_selected_not_nearest"
    )


def test_replacement_verdict_blocks_missing_fields() -> None:
    rows = [
        {
            "replacement_label": "pre_fire_lost_absent_selected_nearest",
            "selected_rank_by_collision_distance": 1,
            "fire_nearest_object_id": 1,
            "fire_nearest_distance_m": 8.0,
            "fire_minus_last_support_s": 1.0,
            "fire_minus_last_presence_s": 0.5,
            "problems": [],
        }
        for _ in range(8)
    ]
    bad_rows = [dict(row) for row in rows]
    del bad_rows[-1]["fire_nearest_distance_m"]
    summary = {"row_count": 8, "replacement_label_counts": {"pre_fire_lost_absent_selected_nearest": 8}}

    assert replacement.choose_verdict([], bad_rows, summary) == replacement.INFRA_NULL_VERDICT


def test_iter112_proof_builds_complete_replacement_report() -> None:
    repo = Path(__file__).resolve().parents[1]
    report = replacement.build_report(
        repo
        / "experiments"
        / "iter117_hugsim_support_core_event_window_decomposition"
        / "proof-event-window"
        / "support_core_event_window_report.json",
        repo
        / "experiments"
        / "iter118_hugsim_support_core_object_lifecycle"
        / "proof-lifecycle"
        / "support_core_object_lifecycle_report.json",
        repo / "experiments" / "iter112_hugsim_support_core_batch_execution" / "proof-execution",
    )

    assert report["verdict"] == replacement.COMPLETE_VERDICT
    assert not report["infra_problems"]
    assert report["summary"]["row_count"] == 8
    assert report["summary"]["problem_row_count"] == 0
    assert sum(report["summary"]["replacement_label_counts"].values()) == 8
