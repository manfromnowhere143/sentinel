from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter99_hugsim_structural_bridge_coverage_audit"
    / "analyze_structural_bridge_coverage.py"
)
SPEC = importlib.util.spec_from_file_location("iter99_coverage", MODULE_PATH)
assert SPEC is not None
coverage = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(coverage)


FIXED_ROWS = [
    ("mixed_extreme", "scene-0062-extreme-00", "foreground_present_surface_silent", "no_monitor_fire"),
    ("both_distinct_extreme", "scene-0138-extreme-00", "foreground_present_late_fire", "post_collision_fire"),
    ("nofire_hard_control", "scene-0041-hard-00", "foreground_present_surface_silent", "no_monitor_fire"),
    ("cpa_medium_a", "scene-0071-medium-00", "foreground_absent_background_only", "background_collision_only"),
    ("ttc_medium_a", "scene-0071-medium-01", "foreground_present_late_fire", "post_collision_fire"),
]


def _row70(audit_id: str, scenario: str, structural_label: str, support_label: str) -> dict:
    return {
        "audit_id": audit_id,
        "scenario": scenario,
        "structural_label": structural_label,
        "iter59_support_label": support_label,
        "report": {
            "first_foreground_ts": None if structural_label == "foreground_absent_background_only" else 1.0,
            "first_fire_ts": 3.5 if structural_label != "foreground_present_surface_silent" else None,
        },
        "decision_log": {"first_fire_channel": "ttc_only" if structural_label != "foreground_present_surface_silent" else None},
        "problems": [],
    }


def _event(audit_id: str, scenario: str, row_label: str) -> dict:
    return {"audit_id": audit_id, "scenario": scenario, "row_label": row_label, "problems": []}


def _reports(tmp_path: Path, *, iter96_verdict: str = coverage.ITER96_VERDICT) -> tuple[Path, Path, Path, Path]:
    iter70_path = tmp_path / "iter70.json"
    iter96_path = tmp_path / "iter96.json"
    iter97_path = tmp_path / "iter97.json"
    iter98_path = tmp_path / "iter98.json"
    iter70_path.write_text(
        json.dumps(
            {
                "verdict": coverage.ITER70_VERDICT,
                "infra_problems": [],
                "episodes": [_row70(*row) for row in FIXED_ROWS],
            }
        )
    )
    iter96_path.write_text(
        json.dumps(
            {
                "verdict": iter96_verdict,
                "infra_problems": [],
                "events": [
                    _event("both_distinct_extreme", "scene-0138-extreme-00", "late_fire_with_provenance_ttc_branch"),
                    _event("ttc_medium_a", "scene-0071-medium-01", "late_fire_with_path_cpa_branch"),
                ],
            }
        )
    )
    iter97_path.write_text(
        json.dumps(
            {
                "verdict": coverage.ITER97_VERDICT,
                "infra_problems": [],
                "events": [
                    _event(
                        "mixed_extreme",
                        "scene-0062-extreme-00",
                        "surface_silent_far_never_active_post_foreground_near",
                    ),
                    _event(
                        "nofire_hard_control",
                        "scene-0041-hard-00",
                        "surface_silent_far_never_active_post_foreground_near",
                    ),
                ],
            }
        )
    )
    iter98_path.write_text(
        json.dumps(
            {
                "verdict": coverage.ITER98_VERDICT,
                "infra_problems": [],
                "events": [
                    _event(
                        "cpa_medium_a",
                        "scene-0071-medium-00",
                        "background_only_ttc_fire_foreground_absent",
                    )
                ],
            }
        )
    )
    return iter70_path, iter96_path, iter97_path, iter98_path


def test_structural_bridge_coverage_complete(tmp_path: Path) -> None:
    report = coverage.build_report(*_reports(tmp_path))

    assert report["verdict"] == "HUGSIM_STRUCTURAL_BRIDGE_COVERAGE_COMPLETE"
    assert report["summary"]["covered_rows"] == 5
    assert report["summary"]["compatible_rows"] == 5
    assert report["summary"]["uncovered_rows"] == 0
    assert report["summary"]["duplicate_or_incompatible_rows"] == 0
    assert report["summary"]["row_label_counts"] == {
        "structural_background_only_bridge_covered": 1,
        "structural_late_fire_bridge_covered": 2,
        "structural_surface_silent_bridge_covered": 2,
    }


def test_structural_bridge_coverage_blocks_bad_iter96_verdict(tmp_path: Path) -> None:
    report = coverage.build_report(*_reports(tmp_path, iter96_verdict="WRONG"))

    assert report["verdict"] == "HUGSIM_STRUCTURAL_BRIDGE_COVERAGE_BLOCKED"
    assert report["events"] == []
    assert "iter96-verdict-not-HUGSIM_BRANCH_TAXONOMY_LATE_FIRE_OUTCOME_BRIDGE_COMPLETE" in report["infra_problems"]


def test_structural_bridge_coverage_blocks_missing_iter97_event(tmp_path: Path) -> None:
    iter70_path, iter96_path, iter97_path, iter98_path = _reports(tmp_path)
    iter97 = json.loads(iter97_path.read_text())
    iter97["events"] = iter97["events"][:1]
    iter97_path.write_text(json.dumps(iter97))

    report = coverage.build_report(iter70_path, iter96_path, iter97_path, iter98_path)

    assert report["verdict"] == "HUGSIM_STRUCTURAL_BRIDGE_COVERAGE_BLOCKED"
    assert report["events"] == []
    assert any(problem.startswith("iter97_surface_silent-coverage-keys-mismatch:") for problem in report["infra_problems"])
