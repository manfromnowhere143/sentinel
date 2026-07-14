from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter96_hugsim_branch_outcome_bridge"
    / "analyze_branch_outcome_bridge.py"
)
SPEC = importlib.util.spec_from_file_location("iter96_branch_outcome", MODULE_PATH)
assert SPEC is not None
bridge = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(bridge)


def _structural_row(audit_id: str, scenario: str, channel: str) -> dict:
    first_foreground = 5.25 if audit_id == "both_distinct_extreme" else 3.25
    first_fire = first_foreground + 1.75
    return {
        "audit_id": audit_id,
        "scenario": scenario,
        "structural_label": "foreground_present_late_fire",
        "iter59_support_label": "post_collision_fire",
        "pre_or_at_foreground_fire": False,
        "fire_minus_foreground_s": 1.75,
        "report": {
            "first_foreground_ts": first_foreground,
            "first_fire_ts": first_fire,
            "first_fire_channel": channel,
        },
        "decision_log": {"pre_or_at_foreground_fire_frames": 0},
        "problems": [],
    }


def _branch_row(audit_id: str, scenario: str, label: str) -> dict:
    return {
        "audit_id": audit_id,
        "scenario": scenario,
        "event_role": "pre",
        "row_label": label,
        "problems": [],
    }


def _reports(
    tmp_path: Path,
    *,
    iter94_verdict: str = bridge.ITER94_VERDICT,
    both_label: str = bridge.PROVENANCE_TTC_LABEL,
) -> tuple[Path, Path, Path]:
    iter70_path = tmp_path / "iter70.json"
    iter94_path = tmp_path / "iter94.json"
    iter95_path = tmp_path / "iter95.json"
    iter70_path.write_text(
        json.dumps(
            {
                "verdict": bridge.ITER70_VERDICT,
                "infra_problems": [],
                "episodes": [
                    _structural_row("both_distinct_extreme", "scene-0138-extreme-00", "ttc_only"),
                    _structural_row("ttc_medium_a", "scene-0071-medium-01", "cpa_only"),
                ],
            }
        )
    )
    iter94_path.write_text(
        json.dumps(
            {
                "verdict": iter94_verdict,
                "infra_problems": [],
                "events": [
                    _branch_row("ttc_medium_a", "scene-0071-medium-01", bridge.ACTIVE_CPA_LABEL),
                ],
            }
        )
    )
    iter95_path.write_text(
        json.dumps(
            {
                "verdict": bridge.ITER95_VERDICT,
                "infra_problems": [],
                "events": [
                    _branch_row("both_distinct_extreme", "scene-0138-extreme-00", both_label),
                    _branch_row("ttc_medium_a", "scene-0071-medium-01", bridge.PATH_CPA_LABEL),
                ],
            }
        )
    )
    return iter70_path, iter94_path, iter95_path


def test_branch_taxonomy_late_fire_outcome_bridge_complete(tmp_path: Path) -> None:
    report = bridge.build_report(*_reports(tmp_path))
    labels = {row["audit_id"]: row["row_label"] for row in report["events"]}

    assert report["verdict"] == "HUGSIM_BRANCH_TAXONOMY_LATE_FIRE_OUTCOME_BRIDGE_COMPLETE"
    assert labels["both_distinct_extreme"] == "late_fire_with_provenance_ttc_branch"
    assert labels["ttc_medium_a"] == "late_fire_with_path_cpa_branch"
    assert report["summary"]["late_fire_rows"] == 2
    assert report["summary"]["no_pre_foreground_fire_rows"] == 2
    assert report["summary"]["provenance_ttc_branch_rows"] == 1
    assert report["summary"]["path_cpa_branch_rows"] == 1


def test_branch_taxonomy_outcome_bridge_blocks_bad_iter94_verdict(tmp_path: Path) -> None:
    report = bridge.build_report(*_reports(tmp_path, iter94_verdict="WRONG"))

    assert report["verdict"] == "HUGSIM_BRANCH_TAXONOMY_OUTCOME_BRIDGE_BLOCKED"
    assert report["events"] == []
    assert "iter94-verdict-not-HUGSIM_ACTIVE_ROW_SURFACE_MARGIN_ARBITRATION_COMPLETE" in report["infra_problems"]


def test_branch_taxonomy_outcome_bridge_mixed_other(tmp_path: Path) -> None:
    report = bridge.build_report(*_reports(tmp_path, both_label="unexpected_branch"))

    assert report["verdict"] == "HUGSIM_BRANCH_TAXONOMY_OUTCOME_BRIDGE_BLOCKED"
    assert "iter95-labels-mismatch:('both_distinct_extreme', 'scene-0138-extreme-00'):['unexpected_branch']" in report[
        "infra_problems"
    ]
