from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter114_hugsim_support_core_mismatch_geometry_decomposition"
    / "analyze_support_core_mismatch_geometry.py"
)
SPEC = importlib.util.spec_from_file_location("iter114_geometry", MODULE_PATH)
assert SPEC is not None
geometry = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(geometry)


def test_geometry_classifies_far_behind_lateral_near() -> None:
    row = geometry.classify_row(
        {
            "support_label": "classifiable_foreground",
            "bridge_label": "actor_mismatch",
            "bridge_distance_m": 10.0,
            "monitor_forward_lateral": [0.0, 1.0],
            "hugsim_forward_lateral": [10.0, 2.0],
        }
    )

    assert row["forward_relation"] == "monitor_far_behind"
    assert row["lateral_relation"] == "monitor_lateral_near"
    assert row["dominant_component"] == "forward_dominant"
    assert row["geometry_label"] == "far_behind_lateral_near"


def test_geometry_classifies_far_ahead_lateral_far() -> None:
    row = geometry.classify_row(
        {
            "support_label": "classifiable_foreground",
            "bridge_label": "actor_mismatch",
            "bridge_distance_m": 15.0,
            "monitor_forward_lateral": [20.0, -9.0],
            "hugsim_forward_lateral": [8.0, 0.0],
        }
    )

    assert row["forward_relation"] == "monitor_far_ahead"
    assert row["lateral_relation"] == "monitor_far_right"
    assert row["geometry_label"] == "far_ahead_lateral_far"


def test_geometry_blocks_missing_coordinates() -> None:
    row = geometry.classify_row(
        {
            "support_label": "classifiable_foreground",
            "bridge_label": "actor_mismatch",
            "bridge_distance_m": 10.0,
            "monitor_forward_lateral": [0.0],
            "hugsim_forward_lateral": [8.0, 0.0],
        }
    )

    assert row["problems"] == ["monitor_forward_lateral-not-vec2"]


def test_iter113_report_builds_complete_geometry_report() -> None:
    repo = Path(__file__).resolve().parents[1]
    report = geometry.build_report(
        repo
        / "experiments"
        / "iter113_hugsim_support_core_actor_match_audit"
        / "proof-actor-match"
        / "support_core_actor_match_report.json"
    )

    assert report["verdict"] == geometry.COMPLETE_VERDICT
    assert not report["infra_problems"]
    assert report["summary"]["row_count"] == 8
    assert report["summary"]["problem_row_count"] == 0
    assert sum(report["summary"]["geometry_label_counts"].values()) == 8
