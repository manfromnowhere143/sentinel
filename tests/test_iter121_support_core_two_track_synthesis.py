from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter121_hugsim_support_core_two_track_synthesis"
    / "analyze_support_core_two_track_synthesis.py"
)
SPEC = importlib.util.spec_from_file_location("iter121_synthesis", MODULE_PATH)
assert SPEC is not None
synthesis = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(synthesis)


def test_synthesis_label_known_branches() -> None:
    assert (
        synthesis.synthesis_label(
            "pre_fire_object_absent_at_fire",
            "pre_fire_lost_absent_selected_nearest",
            "selected_never_supported_before_collision",
        )
        == "two_track_pre_support_lost_absent_selected_nearest"
    )
    assert (
        synthesis.synthesis_label(
            "pre_fire_object_drifted_outside_support_at_fire",
            "pre_fire_drifted_selected_not_nearest",
            "selected_never_supported_before_collision",
        )
        == "two_track_pre_support_drifted_selected_not_nearest"
    )
    assert (
        synthesis.synthesis_label(
            "post_fire_support_only_far_support",
            "post_fire_support_selected_nearest",
            "selected_never_supported_before_collision",
        )
        == "two_track_post_fire_support_selected_nearest"
    )


def test_synthesis_label_other_when_selected_supported() -> None:
    assert (
        synthesis.synthesis_label(
            "pre_fire_object_absent_at_fire",
            "pre_fire_lost_absent_selected_nearest",
            "selected_supported_at_fire",
        )
        == "two_track_other"
    )


def test_synthesis_verdict_blocks_problem_row() -> None:
    rows = [
        {
            "synthesis_label": "two_track_never_supported_selected_nearest",
            "two_track_split": True,
            "problems": [],
        }
        for _ in range(7)
    ]
    rows.append({**rows[0], "problems": ["bad"]})
    summary = {"row_count": 8, "synthesis_label_counts": {"two_track_never_supported_selected_nearest": 8}}

    assert synthesis.choose_verdict([], rows, summary) == synthesis.INFRA_NULL_VERDICT


def test_committed_reports_build_complete_synthesis() -> None:
    repo = Path(__file__).resolve().parents[1]
    report = synthesis.build_report(
        repo
        / "experiments"
        / "iter118_hugsim_support_core_object_lifecycle"
        / "proof-lifecycle"
        / "support_core_object_lifecycle_report.json",
        repo
        / "experiments"
        / "iter119_hugsim_support_core_loss_replacement_audit"
        / "proof-replacement"
        / "support_core_loss_replacement_report.json",
        repo
        / "experiments"
        / "iter120_hugsim_support_core_selected_fire_object_lifecycle"
        / "proof-selected"
        / "selected_fire_object_lifecycle_report.json",
    )

    assert report["verdict"] == synthesis.COMPLETE_VERDICT
    assert not report["infra_problems"]
    assert report["summary"]["row_count"] == 8
    assert report["summary"]["problem_row_count"] == 0
    assert sum(report["summary"]["synthesis_label_counts"].values()) == 8
