from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter118_hugsim_support_core_object_lifecycle"
    / "analyze_support_core_object_lifecycle.py"
)
SPEC = importlib.util.spec_from_file_location("iter118_lifecycle", MODULE_PATH)
assert SPEC is not None
lifecycle = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(lifecycle)


def test_lifecycle_label_pre_fire_absent_drift_supported() -> None:
    assert (
        lifecycle.lifecycle_label("pre_fire", False, False, 0, 0)
        == "pre_fire_object_absent_at_fire"
    )
    assert (
        lifecycle.lifecycle_label("pre_fire", True, False, 0, 0)
        == "pre_fire_object_drifted_outside_support_at_fire"
    )
    assert (
        lifecycle.lifecycle_label("pre_fire", True, True, 0, 0)
        == "pre_fire_object_still_supported_at_fire"
    )


def test_lifecycle_label_post_fire_active_identity() -> None:
    assert lifecycle.lifecycle_label("never_before_collision", None, None, 0, 0) == "never_supported_reference"
    assert (
        lifecycle.lifecycle_label("post_fire_pre_collision", False, False, 1, 0)
        == "post_fire_support_only_same_object_active_support"
    )
    assert (
        lifecycle.lifecycle_label("post_fire_pre_collision", False, False, 0, 1)
        == "post_fire_support_only_different_object_active_support"
    )
    assert (
        lifecycle.lifecycle_label("post_fire_pre_collision", False, False, 0, 0)
        == "post_fire_support_only_far_support"
    )


def test_lifecycle_verdict_blocks_row_problem() -> None:
    rows = [
        {
            "lifecycle_label": "never_supported_reference",
            "active_support_same_object_count": 0,
            "active_support_different_object_count": 0,
            "problems": [],
        }
        for _ in range(7)
    ]
    rows.append({**rows[0], "problems": ["bad"]})
    summary = {"row_count": 8, "lifecycle_label_counts": {"never_supported_reference": 8}}

    assert lifecycle.choose_verdict([], rows, summary) == lifecycle.INFRA_NULL_VERDICT


def test_iter112_proof_builds_complete_lifecycle_report() -> None:
    repo = Path(__file__).resolve().parents[1]
    report = lifecycle.build_report(
        repo
        / "experiments"
        / "iter117_hugsim_support_core_event_window_decomposition"
        / "proof-event-window"
        / "support_core_event_window_report.json",
        repo / "experiments" / "iter112_hugsim_support_core_batch_execution" / "proof-execution",
    )

    assert report["verdict"] == lifecycle.COMPLETE_VERDICT
    assert not report["infra_problems"]
    assert report["summary"]["row_count"] == 8
    assert report["summary"]["problem_row_count"] == 0
    assert sum(report["summary"]["lifecycle_label_counts"].values()) == 8
