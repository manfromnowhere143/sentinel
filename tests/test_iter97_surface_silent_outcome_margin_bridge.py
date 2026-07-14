from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter97_hugsim_surface_silent_outcome_margin_bridge"
    / "analyze_surface_silent_outcome_margin_bridge.py"
)
SPEC = importlib.util.spec_from_file_location("iter97_silent_bridge", MODULE_PATH)
assert SPEC is not None
silent_bridge = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(silent_bridge)


def _row70(audit_id: str, scenario: str) -> dict:
    return {
        "audit_id": audit_id,
        "scenario": scenario,
        "structural_label": "foreground_present_surface_silent",
        "iter59_support_label": "no_monitor_fire",
        "pre_or_at_foreground_fire": False,
        "report": {
            "first_foreground_ts": 4.75,
            "foreground_count": 2,
            "first_fire_ts": None,
        },
        "decision_log": {"fired_frames": 0},
        "problems": [],
    }


def _row71(audit_id: str, scenario: str) -> dict:
    return {
        "audit_id": audit_id,
        "scenario": scenario,
        "row_label": "surface_silent_far_margin",
        "summary": {
            "closest_cpa_margin_m": 2.0,
            "closest_ttc_margin_s": None,
            "active_cpa_frames": 0,
            "active_ttc_frames": 0,
            "pre_foreground_fired_frames": 0,
        },
        "problems": [],
    }


def _row73(audit_id: str, scenario: str, near_offset: float | None) -> dict:
    return {
        "audit_id": audit_id,
        "scenario": scenario,
        "row_label": "silent_far_never_active",
        "timeline": {
            "first_near_offset_s": near_offset,
            "first_active_offset_s": None,
            "first_active_relation_to_foreground": "never",
            "pre_foreground_near_any": False,
            "pre_foreground_near_cpa": False,
            "pre_foreground_near_ttc": False,
        },
        "problems": [],
    }


def _reports(
    tmp_path: Path,
    *,
    iter71_verdict: str = silent_bridge.ITER71_VERDICT,
    near_offsets: tuple[float | None, float | None] = (0.25, 3.5),
) -> tuple[Path, Path, Path]:
    row_a = ("mixed_extreme", "scene-0062-extreme-00")
    row_b = ("nofire_hard_control", "scene-0041-hard-00")
    iter70_path = tmp_path / "iter70.json"
    iter71_path = tmp_path / "iter71.json"
    iter73_path = tmp_path / "iter73.json"
    iter70_path.write_text(
        json.dumps(
            {
                "verdict": silent_bridge.ITER70_VERDICT,
                "infra_problems": [],
                "episodes": [_row70(*row_a), _row70(*row_b)],
            }
        )
    )
    iter71_path.write_text(
        json.dumps(
            {
                "verdict": iter71_verdict,
                "infra_problems": [],
                "episodes": [_row71(*row_a), _row71(*row_b)],
            }
        )
    )
    iter73_path.write_text(
        json.dumps(
            {
                "verdict": silent_bridge.ITER73_VERDICT,
                "infra_problems": [],
                "episodes": [_row73(*row_a, near_offsets[0]), _row73(*row_b, near_offsets[1])],
            }
        )
    )
    return iter70_path, iter71_path, iter73_path


def test_surface_silent_outcome_margin_bridge_complete(tmp_path: Path) -> None:
    report = silent_bridge.build_report(*_reports(tmp_path))

    assert report["verdict"] == "HUGSIM_SURFACE_SILENT_OUTCOME_MARGIN_BRIDGE_COMPLETE"
    assert report["summary"]["surface_silent_rows"] == 2
    assert report["summary"]["zero_fire_rows"] == 2
    assert report["summary"]["far_margin_rows"] == 2
    assert report["summary"]["never_active_rows"] == 2
    assert report["summary"]["post_foreground_near_rows"] == 2


def test_surface_silent_outcome_margin_no_near_complete(tmp_path: Path) -> None:
    report = silent_bridge.build_report(*_reports(tmp_path, near_offsets=(None, None)))

    assert report["verdict"] == "HUGSIM_SURFACE_SILENT_OUTCOME_MARGIN_NO_NEAR_COMPLETE"
    assert report["summary"]["row_label_counts"] == {"surface_silent_far_never_active_no_near": 2}


def test_surface_silent_outcome_margin_blocks_bad_iter71_verdict(tmp_path: Path) -> None:
    report = silent_bridge.build_report(*_reports(tmp_path, iter71_verdict="WRONG"))

    assert report["verdict"] == "HUGSIM_SURFACE_SILENT_OUTCOME_MARGIN_BLOCKED"
    assert report["events"] == []
    assert "iter71-verdict-not-HUGSIM_SURFACE_SILENT_MARGIN_COMPLETE" in report["infra_problems"]
