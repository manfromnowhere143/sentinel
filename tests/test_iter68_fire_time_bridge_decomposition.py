from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter68_fire_time_bridge_decomposition"
    / "analyze_fire_time_bridge_decomposition.py"
)
SPEC = importlib.util.spec_from_file_location("iter68_fire_time_bridge_decomposition", MODULE_PATH)
assert SPEC is not None
fire_gap = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(fire_gap)


def _variant(decision_ts: float, foreground_ts: float, distance: float) -> dict:
    return {
        "decision_ts": decision_ts,
        "foreground_timestamp": foreground_ts,
        "distance_m": distance,
        "temporal_source": "frame_time",
        "lead_time_s": foreground_ts - decision_ts,
        "monitor_forward_lateral": [10.0, 1.0],
        "hugsim_forward_lateral": [9.0, 0.0],
    }


def _surface(object_id: int, decision_ts: float, distance: float) -> dict:
    return {
        "object_id": object_id,
        "best_distance_m": distance,
        "distance_label": fire_gap.distance_label(distance),
        "best_variant": _variant(decision_ts, 3.0, distance),
    }


def _write_reports(
    tmp_path: Path,
    best_decisions: list[float],
    full_distances: list[float],
    *,
    iter67_verdict: str = "TRIGGER_TARGET_SAME_AND_SPLIT_COMPLETE",
) -> tuple[Path, Path, Path, Path, Path, Path]:
    rows = []
    for target, best_decision, full_distance in zip(
        fire_gap.EXPECTED_TARGETS,
        best_decisions,
        full_distances,
        strict=True,
    ):
        rows.append({
            "audit_id": target["audit_id"],
            "scenario": target["scenario"],
            "trigger_object_id": target["trigger_object_id"],
            "first_fire_ts": 1.0,
            "trigger_surface": _surface(target["trigger_object_id"], best_decision, full_distance),
            "first_fire_trigger_surface": _surface(target["trigger_object_id"], 1.0, 10.0),
        })

    iter59 = tmp_path / "iter59.json"
    iter59.write_text(json.dumps({"verdict": "ACTOR_MATCH_AUDIT_COMPLETE"}))
    iter61 = tmp_path / "iter61.json"
    iter61.write_text(json.dumps({
        "verdict": "OBJECT_SURFACE_NONTRIGGER_MATCH_COMPLETE",
        "episodes": [
            {"audit_id": target["audit_id"], "scenario": target["scenario"], "row_label": "no_monitor_object_support"}
            for target in fire_gap.EXPECTED_TARGETS
        ],
    }))
    iter64 = tmp_path / "iter64.json"
    iter64.write_text(json.dumps({
        "verdict": "UNSUPPORTED_TEMPORAL_MATCH_COMPLETE",
        "episodes": [{"audit_id": target["audit_id"], "scenario": target["scenario"]} for target in fire_gap.EXPECTED_TARGETS],
    }))
    iter65 = tmp_path / "iter65.json"
    iter65.write_text(json.dumps({
        "verdict": "TEMPORAL_ALIGNMENT_SUBTHRESHOLD_COMPLETE",
        "episodes": [{"audit_id": target["audit_id"], "scenario": target["scenario"]} for target in fire_gap.EXPECTED_TARGETS],
    }))
    iter66 = tmp_path / "iter66.json"
    iter66.write_text(json.dumps({
        "verdict": "MATCHED_OBJECT_TIMELINE_MIXED_COMPLETE",
        "episodes": [{"audit_id": target["audit_id"], "scenario": target["scenario"]} for target in fire_gap.EXPECTED_TARGETS],
    }))
    iter67 = tmp_path / "iter67.json"
    iter67.write_text(json.dumps({"verdict": iter67_verdict, "episodes": rows}))
    return iter59, iter61, iter64, iter65, iter66, iter67


def test_fire_time_bridge_gap_temporal_split_complete(tmp_path: Path) -> None:
    reports = _write_reports(tmp_path, [0.5, 2.0], [2.0, 2.5])

    report = fire_gap.build_report(*reports)

    assert report["verdict"] == "FIRE_TIME_BRIDGE_GAP_TEMPORAL_SPLIT_COMPLETE"
    assert report["summary"]["row_label_counts"] == {
        "fire_gap_best_after_fire": 1,
        "fire_gap_best_before_fire": 1,
    }


def test_fire_time_bridge_gap_all_before_complete(tmp_path: Path) -> None:
    reports = _write_reports(tmp_path, [0.25, 0.5], [2.0, 2.5])

    report = fire_gap.build_report(*reports)

    assert report["verdict"] == "FIRE_TIME_BRIDGE_GAP_ALL_BEFORE_COMPLETE"
    assert report["summary"]["before_fire_rows"] == 2


def test_fire_time_bridge_gap_no_match_complete(tmp_path: Path) -> None:
    reports = _write_reports(tmp_path, [0.25, 2.0], [9.0, 10.0])

    report = fire_gap.build_report(*reports)

    assert report["verdict"] == "FIRE_TIME_BRIDGE_GAP_NO_MATCH_COMPLETE"
    assert report["summary"]["row_label_counts"] == {"fire_gap_no_full_window_match": 2}


def test_fire_time_bridge_decomposition_blocked_when_iter67_crosscheck_fails(tmp_path: Path) -> None:
    reports = _write_reports(tmp_path, [0.5, 2.0], [2.0, 2.5], iter67_verdict="WRONG")

    report = fire_gap.build_report(*reports)

    assert report["verdict"] == "FIRE_TIME_BRIDGE_DECOMPOSITION_BLOCKED"
    assert "iter67-verdict-not-TRIGGER_TARGET_SAME_AND_SPLIT_COMPLETE" in report["infra_problems"]
