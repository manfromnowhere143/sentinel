from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter98_hugsim_background_only_outcome_bridge"
    / "analyze_background_only_outcome_bridge.py"
)
SPEC = importlib.util.spec_from_file_location("iter98_background_bridge", MODULE_PATH)
assert SPEC is not None
background_bridge = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(background_bridge)


def _row59() -> dict:
    return {
        "audit_id": "cpa_medium_a",
        "scenario": "scene-0071-medium-00",
        "support_label": "background_collision_only",
        "foreground_count": 0,
        "first_foreground_ts": None,
        "monitor_object_id": 11,
        "monitor_provenance_label": "unique_ttc_object",
        "first_fire_ts": 3.5,
        "first_fire_channel": "ttc_only",
        "fired_frames": 4,
        "brake_frames": 11,
        "problems": [],
        "detail_problems": [],
    }


def _row69() -> dict:
    return {
        "audit_id": "cpa_medium_a",
        "scenario": "scene-0071-medium-00",
        "mechanism_label": "background_collision_only",
        "iter59_support_label": "background_collision_only",
        "first_fire_ts": 3.5,
        "first_fire_channel": "ttc_only",
        "monitor_object_id": 11,
        "problems": [],
    }


def _row70(*, structural_label: str = "foreground_absent_background_only") -> dict:
    return {
        "audit_id": "cpa_medium_a",
        "scenario": "scene-0071-medium-00",
        "structural_label": structural_label,
        "iter59_support_label": "background_collision_only",
        "report": {
            "foreground_count": 0,
            "first_foreground_ts": None,
            "first_fire_ts": 3.5,
            "monitor_object_id": 11,
            "monitor_provenance_label": "unique_ttc_object",
        },
        "decision_log": {
            "first_fire_ts": 3.5,
            "first_fire_channel": "ttc_only",
            "fired_frames": 4,
            "brake_frames": 11,
        },
        "pre_or_at_foreground_fire": False,
        "problems": [],
    }


def _reports(
    tmp_path: Path,
    *,
    iter59_verdict: str = background_bridge.ITER59_VERDICT,
    structural_label: str = "foreground_absent_background_only",
) -> tuple[Path, Path, Path]:
    iter59_path = tmp_path / "iter59.json"
    iter69_path = tmp_path / "iter69.json"
    iter70_path = tmp_path / "iter70.json"
    iter59_path.write_text(
        json.dumps({"verdict": iter59_verdict, "infra_problems": [], "episodes": [_row59()]})
    )
    iter69_path.write_text(
        json.dumps({"verdict": background_bridge.ITER69_VERDICT, "infra_problems": [], "episodes": [_row69()]})
    )
    iter70_path.write_text(
        json.dumps(
            {
                "verdict": background_bridge.ITER70_VERDICT,
                "infra_problems": [],
                "episodes": [_row70(structural_label=structural_label)],
            }
        )
    )
    return iter59_path, iter69_path, iter70_path


def test_background_only_outcome_bridge_complete(tmp_path: Path) -> None:
    report = background_bridge.build_report(*_reports(tmp_path))

    assert report["verdict"] == "HUGSIM_BACKGROUND_ONLY_OUTCOME_BRIDGE_COMPLETE"
    assert report["summary"]["background_only_rows"] == 1
    assert report["summary"]["foreground_absent_rows"] == 1
    assert report["summary"]["monitor_fire_rows"] == 1
    assert report["summary"]["ttc_only_fire_rows"] == 1
    assert report["summary"]["preserved_monitor_object_rows"] == 1


def test_background_only_outcome_blocks_bad_iter59_verdict(tmp_path: Path) -> None:
    report = background_bridge.build_report(*_reports(tmp_path, iter59_verdict="WRONG"))

    assert report["verdict"] == "HUGSIM_BACKGROUND_ONLY_OUTCOME_BRIDGE_BLOCKED"
    assert report["events"] == []
    assert "iter59-verdict-not-ACTOR_MATCH_AUDIT_COMPLETE" in report["infra_problems"]


def test_background_only_outcome_blocks_structural_label_mismatch(tmp_path: Path) -> None:
    report = background_bridge.build_report(*_reports(tmp_path, structural_label="foreground_present_late_fire"))

    assert report["verdict"] == "HUGSIM_BACKGROUND_ONLY_OUTCOME_BRIDGE_BLOCKED"
    assert report["events"] == []
    assert any(problem.startswith("iter70-structural_label-mismatch:") for problem in report["infra_problems"])
