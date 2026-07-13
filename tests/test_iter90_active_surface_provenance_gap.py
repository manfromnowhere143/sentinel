from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ITER76_TEST_PATH = Path(__file__).resolve().parents[0] / "test_iter76_switch_foreground_bridge.py"
ITER76_SPEC = importlib.util.spec_from_file_location("iter76_test_helpers", ITER76_TEST_PATH)
assert ITER76_SPEC is not None
iter76_helpers = importlib.util.module_from_spec(ITER76_SPEC)
assert ITER76_SPEC.loader is not None
ITER76_SPEC.loader.exec_module(iter76_helpers)

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter90_hugsim_active_surface_provenance_gap"
    / "analyze_active_surface_provenance_gap.py"
)
SPEC = importlib.util.spec_from_file_location("iter90_gap", MODULE_PATH)
assert SPEC is not None
gap = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(gap)


def _write_json(path: Path, data: dict) -> Path:
    path.write_text(json.dumps(data))
    return path


def _event87(
    audit_id: str,
    scenario: str,
    role: str,
    support_object_id: int,
    replay_ts: float,
    alignment: str,
) -> dict:
    return {
        "audit_id": audit_id,
        "scenario": scenario,
        "event_role": role,
        "support_object_id": support_object_id,
        "selection": {"replay_ts": replay_ts, "alignment": alignment},
        "row_label": "interval_support_surface_miss",
        "problems": [],
    }


def _event89(
    audit_id: str,
    scenario: str,
    role: str,
    support_object_id: int,
    replay_ts: float,
    alignment: str,
) -> dict:
    return {
        "audit_id": audit_id,
        "scenario": scenario,
        "event_role": role,
        "support_object_id": support_object_id,
        "replay_ts": replay_ts,
        "replay_alignment": alignment,
        "active_bridge_supported_count": 0,
        "row_label": "no_active_bridge_candidate_support_subthreshold",
        "problems": [],
    }


def _reports(
    tmp_path: Path,
    *,
    iter89_verdict: str = "HUGSIM_JOINT_BRIDGE_SURFACE_NO_ACTIVE_CANDIDATE_SPLIT_COMPLETE",
) -> tuple[Path, Path, Path]:
    h = iter76_helpers
    iter59_rows = [
        h._episode(
            tmp_path,
            "both_distinct_extreme",
            "scene-0138-extreme-00",
            [
                h._decision_row(5.5, [h._obj(9, [0.0, 9.0])]),
            ],
            [0.0, 9.0],
        ),
        h._episode(
            tmp_path,
            "ttc_medium_a",
            "scene-0071-medium-01",
            [
                h._decision_row(4.0, [h._obj(10, [0.0, 9.0])]),
                h._decision_row(5.75, [h._obj(10, [0.0, 9.0]), h._obj(24, [0.0, 1.0])]),
            ],
            [0.0, 9.0],
        ),
    ]
    iter59 = _write_json(
        tmp_path / "iter59.json",
        {"verdict": "ACTOR_MATCH_AUDIT_COMPLETE", "infra_problems": [], "episodes": iter59_rows},
    )
    iter87 = _write_json(
        tmp_path / "iter87.json",
        {
            "verdict": "HUGSIM_INTERVAL_BRIDGE_TIME_SURFACE_REPLAY_MIXED_COMPLETE",
            "infra_problems": [],
            "events": [
                _event87("both_distinct_extreme", "scene-0138-extreme-00", "pre", 9, 5.5, "exact_bridge_ts"),
                _event87("ttc_medium_a", "scene-0071-medium-01", "pre", 10, 4.0, "exact_bridge_ts"),
                _event87("ttc_medium_a", "scene-0071-medium-01", "active", 10, 5.75, "nearest_before_bridge_ts"),
            ],
        },
    )
    iter89 = _write_json(
        tmp_path / "iter89.json",
        {
            "verdict": iter89_verdict,
            "infra_problems": [],
            "summary": {"active_bridge_candidate_events": 0},
            "events": [
                _event89("both_distinct_extreme", "scene-0138-extreme-00", "pre", 9, 5.5, "exact_bridge_ts"),
                _event89("ttc_medium_a", "scene-0071-medium-01", "pre", 10, 4.0, "exact_bridge_ts"),
                _event89("ttc_medium_a", "scene-0071-medium-01", "active", 10, 5.75, "nearest_before_bridge_ts"),
            ],
        },
    )
    return iter59, iter87, iter89


def test_active_surface_provenance_gap_complete(tmp_path: Path) -> None:
    report = gap.build_report(*_reports(tmp_path))
    labels = {(row["audit_id"], row["event_role"]): row["row_label"] for row in report["events"]}

    assert report["verdict"] == "HUGSIM_ACTIVE_SURFACE_PROVENANCE_GAP_COMPLETE"
    assert labels[("both_distinct_extreme", "pre")] == "active_surface_absent_bridge_supported_nonactive"
    assert labels[("ttc_medium_a", "pre")] == "active_surface_absent_bridge_supported_nonactive"
    assert labels[("ttc_medium_a", "active")] == "active_surface_present_no_bridge_supported"
    assert report["summary"]["active_object_events"] == 1
    assert report["summary"]["active_bridge_supported_total"] == 0
    assert report["summary"]["active_no_bridge_total"] == 1
    assert report["summary"]["bridge_supported_nonactive_total"] == 3


def test_active_surface_provenance_gap_blocks_bad_iter89_verdict(tmp_path: Path) -> None:
    report = gap.build_report(*_reports(tmp_path, iter89_verdict="WRONG"))

    assert report["verdict"] == "HUGSIM_ACTIVE_SURFACE_PROVENANCE_GAP_BLOCKED"
    assert report["events"] == []
    assert (
        "iter89-verdict-not-HUGSIM_JOINT_BRIDGE_SURFACE_NO_ACTIVE_CANDIDATE_SPLIT_COMPLETE"
        in report["infra_problems"]
    )
