from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter120_hugsim_support_core_selected_fire_object_lifecycle"
    / "analyze_selected_fire_object_lifecycle.py"
)
SPEC = importlib.util.spec_from_file_location("iter120_selected", MODULE_PATH)
assert SPEC is not None
selected = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(selected)


def test_selected_lifecycle_label_precedence() -> None:
    assert selected.selected_lifecycle_label(0, True, 0) == "selected_supported_at_fire"
    assert selected.selected_lifecycle_label(2, False, 0) == "selected_pre_fire_supported_then_lost_by_fire"
    assert selected.selected_lifecycle_label(0, False, 1) == "selected_post_fire_support_only"
    assert selected.selected_lifecycle_label(0, False, 0) == "selected_never_supported_before_collision"


def test_surface_state_labels() -> None:
    base = {
        "params": {"cpa_margin": 1.5, "ttc_thresh": 2.5},
        "min_cpa": 8.0,
        "min_ttc": 1_000_000_000.0,
    }
    assert selected.surface_state({**base, "min_cpa": 1.0}) == "active"
    assert selected.surface_state({**base, "min_ttc": 2.0}) == "active"
    assert selected.surface_state({**base, "min_cpa": 2.5}) == "borderline"
    assert selected.surface_state({**base, "min_ttc": 4.5}) == "borderline"
    assert selected.surface_state(base) == "far"


def test_selected_verdict_blocks_missing_fields() -> None:
    rows = [
        {
            "selected_lifecycle_label": "selected_never_supported_before_collision",
            "selected_support_phase_counts": {},
            "selected_surface_counts_by_phase": {},
            "selected_pre_fire_closest_distance_m": 9.0,
            "selected_at_fire_distance_m": 10.0,
            "selected_before_collision_closest_distance_m": 8.0,
            "problems": [],
        }
        for _ in range(8)
    ]
    bad_rows = [dict(row) for row in rows]
    del bad_rows[-1]["selected_before_collision_closest_distance_m"]
    summary = {"row_count": 8, "selected_lifecycle_label_counts": {"selected_never_supported_before_collision": 8}}

    assert selected.choose_verdict([], bad_rows, summary) == selected.INFRA_NULL_VERDICT


def test_iter112_proof_builds_complete_selected_report() -> None:
    repo = Path(__file__).resolve().parents[1]
    report = selected.build_report(
        repo
        / "experiments"
        / "iter119_hugsim_support_core_loss_replacement_audit"
        / "proof-replacement"
        / "support_core_loss_replacement_report.json",
        repo / "experiments" / "iter112_hugsim_support_core_batch_execution" / "proof-execution",
    )

    assert report["verdict"] == selected.COMPLETE_VERDICT
    assert not report["infra_problems"]
    assert report["summary"]["row_count"] == 8
    assert report["summary"]["problem_row_count"] == 0
    assert sum(report["summary"]["selected_lifecycle_label_counts"].values()) == 8
