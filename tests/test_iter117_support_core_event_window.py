from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter117_hugsim_support_core_event_window_decomposition"
    / "analyze_support_core_event_window.py"
)
SPEC = importlib.util.spec_from_file_location("iter117_event_window", MODULE_PATH)
assert SPEC is not None
event_window = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(event_window)


def test_surface_state_labels_active_borderline_far() -> None:
    base = {
        "params": {"cpa_margin": 1.5, "ttc_thresh": 2.5},
        "min_cpa": 4.0,
        "min_ttc": 1_000_000_000.0,
        "fired": False,
        "brake": False,
    }
    assert event_window.surface_state({**base, "min_cpa": 1.0})["surface_state"] == "active"
    assert event_window.surface_state({**base, "min_ttc": 2.0})["surface_state"] == "active"
    assert event_window.surface_state({**base, "min_cpa": 2.5})["surface_state"] == "borderline"
    assert event_window.surface_state({**base, "min_ttc": 4.0})["surface_state"] == "borderline"
    assert event_window.surface_state(base)["surface_state"] == "far"


def test_row_label_precedence() -> None:
    assert event_window.row_label("never_before_collision", []) == "never_supported_before_collision"
    assert event_window.row_label("post_fire_pre_collision", []) == "post_fire_support_only"
    assert (
        event_window.row_label("pre_fire", [{"surface_state": "borderline"}, {"surface_state": "active"}])
        == "pre_fire_support_surface_active"
    )
    assert (
        event_window.row_label("pre_fire", [{"surface_state": "far"}, {"surface_state": "borderline"}])
        == "pre_fire_support_surface_borderline_only"
    )
    assert event_window.row_label("pre_fire", [{"surface_state": "far"}]) == "pre_fire_support_surface_far_only"


def test_event_window_verdict_blocks_row_problem() -> None:
    rows = [
        {
            "row_label": "never_supported_before_collision",
            "support_phase_counts": {},
            "support_surface_counts": {},
            "first_fire_event": {},
            "support_object_present_at_fire": None,
            "support_object_same_as_selected": None,
            "support_object_same_as_fire_nearest": None,
            "problems": [],
        }
        for _ in range(7)
    ]
    rows.append({**rows[0], "problems": ["bad"]})
    summary = {"row_count": 8, "row_label_counts": {"never_supported_before_collision": 8}}

    assert event_window.choose_verdict([], rows, summary) == event_window.INFRA_NULL_VERDICT


def test_iter112_proof_builds_complete_event_window_report() -> None:
    repo = Path(__file__).resolve().parents[1]
    report = event_window.build_report(
        repo
        / "experiments"
        / "iter115_hugsim_support_core_monitor_set_ordering"
        / "proof-ordering"
        / "support_core_monitor_set_ordering_report.json",
        repo
        / "experiments"
        / "iter116_hugsim_support_core_collision_actor_timeline"
        / "proof-timeline"
        / "support_core_collision_actor_timeline_report.json",
        repo / "experiments" / "iter112_hugsim_support_core_batch_execution" / "proof-execution",
    )

    assert report["verdict"] == event_window.COMPLETE_VERDICT
    assert not report["infra_problems"]
    assert report["summary"]["row_count"] == 8
    assert report["summary"]["problem_row_count"] == 0
    assert sum(report["summary"]["row_label_counts"].values()) == 8
