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
    / "iter89_hugsim_joint_bridge_surface_candidate_audit"
    / "analyze_joint_bridge_surface_candidate.py"
)
SPEC = importlib.util.spec_from_file_location("iter89_joint", MODULE_PATH)
assert SPEC is not None
joint = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(joint)


def _write_json(path: Path, data: dict) -> Path:
    path.write_text(json.dumps(data))
    return path


def _event85(audit_id: str, scenario: str, role: str, support_object_id: int, band: str) -> dict:
    return {
        "audit_id": audit_id,
        "scenario": scenario,
        "event_role": role,
        "support_object_id": support_object_id,
        "selected_bridge": {"distance_band": "no_support"},
        "support_bridge": {"distance_band": band},
        "row_label": "path_horizon_support_bridge_timing_split",
        "problems": [],
    }


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


def _event88(audit_id: str, scenario: str, role: str, support_object_id: int, label: str) -> dict:
    return {
        "audit_id": audit_id,
        "scenario": scenario,
        "event_role": role,
        "support_object_id": support_object_id,
        "row_label": label,
        "problems": [],
    }


def _reports(tmp_path: Path, *, iter88_verdict: str = "HUGSIM_BRIDGE_SURFACE_MARGIN_RESIDUAL_SPLIT_COMPLETE"):
    h = iter76_helpers
    iter59_rows = [
        h._episode(
            tmp_path,
            "both_distinct_extreme",
            "scene-0138-extreme-00",
            [
                h._decision_row(5.5, [h._obj(9, [0.0, 2.0])]),
            ],
            [0.0, 2.0],
        ),
        h._episode(
            tmp_path,
            "ttc_medium_a",
            "scene-0071-medium-01",
            [
                h._decision_row(4.0, [h._obj(10, [0.0, 9.0])]),
                h._decision_row(5.75, [h._obj(10, [0.0, 9.0])]),
            ],
            [0.0, 9.0],
        ),
    ]
    iter59 = _write_json(
        tmp_path / "iter59.json",
        {"verdict": "ACTOR_MATCH_AUDIT_COMPLETE", "infra_problems": [], "episodes": iter59_rows},
    )
    iter85 = _write_json(
        tmp_path / "iter85.json",
        {
            "verdict": "HUGSIM_PATH_HORIZON_BRIDGE_TIMING_SPLIT_COMPLETE",
            "infra_problems": [],
            "events": [
                _event85("both_distinct_extreme", "scene-0138-extreme-00", "pre", 9, "ambiguous"),
                _event85("ttc_medium_a", "scene-0071-medium-01", "pre", 10, "match"),
                _event85("ttc_medium_a", "scene-0071-medium-01", "active", 10, "match"),
            ],
        },
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
    iter88 = _write_json(
        tmp_path / "iter88.json",
        {
            "verdict": iter88_verdict,
            "infra_problems": [],
            "events": [
                _event88(
                    "both_distinct_extreme",
                    "scene-0138-extreme-00",
                    "pre",
                    9,
                    "bridge_surface_ttc_borderline_cpa_far",
                ),
                _event88(
                    "ttc_medium_a",
                    "scene-0071-medium-01",
                    "pre",
                    10,
                    "bridge_surface_no_finite_ttc_cpa_far",
                ),
                _event88(
                    "ttc_medium_a",
                    "scene-0071-medium-01",
                    "active",
                    10,
                    "bridge_surface_no_finite_ttc_cpa_far",
                ),
            ],
        },
    )
    return iter59, iter85, iter87, iter88


def test_joint_bridge_surface_no_active_candidate_split_complete(tmp_path: Path) -> None:
    report = joint.build_report(*_reports(tmp_path))
    labels = {(row["audit_id"], row["event_role"]): row["row_label"] for row in report["events"]}

    assert report["verdict"] == "HUGSIM_JOINT_BRIDGE_SURFACE_NO_ACTIVE_CANDIDATE_SPLIT_COMPLETE"
    assert labels[("both_distinct_extreme", "pre")] == "no_active_bridge_candidate_support_borderline"
    assert labels[("ttc_medium_a", "pre")] == "no_active_bridge_candidate_support_subthreshold"
    assert labels[("ttc_medium_a", "active")] == "no_active_bridge_candidate_support_subthreshold"
    assert report["summary"]["active_bridge_candidate_events"] == 0
    assert report["summary"]["bridge_supported_object_total"] == 3


def test_joint_bridge_surface_candidate_blocks_bad_iter88_verdict(tmp_path: Path) -> None:
    report = joint.build_report(*_reports(tmp_path, iter88_verdict="WRONG"))

    assert report["verdict"] == "HUGSIM_JOINT_BRIDGE_SURFACE_CANDIDATE_BLOCKED"
    assert report["events"] == []
    assert "iter88-verdict-not-HUGSIM_BRIDGE_SURFACE_MARGIN_RESIDUAL_SPLIT_COMPLETE" in report["infra_problems"]
