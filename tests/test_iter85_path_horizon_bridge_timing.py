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
    / "iter85_hugsim_path_horizon_bridge_timing"
    / "analyze_path_horizon_bridge_timing.py"
)
SPEC = importlib.util.spec_from_file_location("iter85_timing", MODULE_PATH)
assert SPEC is not None
timing = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(timing)


def _write_json(path: Path, data: dict) -> Path:
    path.write_text(json.dumps(data))
    return path


def _event(
    audit_id: str,
    scenario: str,
    role: str,
    event_ts: float,
    selected_object_id: int,
    support_object_id: int,
) -> dict:
    return {
        "audit_id": audit_id,
        "scenario": scenario,
        "event_role": role,
        "event_ts": event_ts,
        "selected_object_id": selected_object_id,
        "support_object_id": support_object_id,
        "selected_state": "active",
        "support_state": "subthreshold",
        "selected_bridge": {"distance_band": "no_support"},
        "support_bridge": {"distance_band": "match"},
        "row_label": "selected_surface_support_bridge_split",
        "problems": [],
    }


def _reports(
    tmp_path: Path,
    *,
    iter84_verdict: str = "HUGSIM_SELECTED_SURFACE_SUPPORT_BRIDGE_SPLIT_COMPLETE",
):
    h = iter76_helpers
    iter59_rows = [
        h._episode(
            tmp_path,
            "both_distinct_extreme",
            "scene-0138-extreme-00",
            [h._decision_row(5.0, [h._obj(5, [0.0, 1.0]), h._obj(9, [0.0, 9.0])])],
            [0.0, 9.0],
        ),
        h._episode(
            tmp_path,
            "ttc_medium_a",
            "scene-0071-medium-01",
            [
                h._decision_row(2.5, [h._obj(6, [0.0, 1.0]), h._obj(10, [0.0, 9.0])]),
                h._decision_row(5.0, [h._obj(24, [0.0, 1.0]), h._obj(10, [0.0, 9.0])]),
            ],
            [0.0, 9.0],
        ),
    ]
    iter59 = _write_json(
        tmp_path / "iter59.json",
        {"verdict": "ACTOR_MATCH_AUDIT_COMPLETE", "infra_problems": [], "episodes": iter59_rows},
    )
    events = [
        _event("both_distinct_extreme", "scene-0138-extreme-00", "pre", 5.0, 5, 9),
        _event("ttc_medium_a", "scene-0071-medium-01", "pre", 2.5, 6, 10),
        _event("ttc_medium_a", "scene-0071-medium-01", "active", 5.0, 24, 10),
    ]
    iter80 = _write_json(
        tmp_path / "iter80.json",
        {
            "verdict": "HUGSIM_SELECTED_ALL_PROVENANCE_NO_SUPPORT_COMPLETE",
            "infra_problems": [],
            "events": [event | {"row_label": "selected_all_provenance_no_support"} for event in events],
        },
    )
    iter83 = _write_json(
        tmp_path / "iter83.json",
        {
            "verdict": "HUGSIM_BRIDGE_SUPPORTED_SURFACE_MISS_MIXED_COMPLETE",
            "infra_problems": [],
            "objects": [
                {
                    "audit_id": "both_distinct_extreme",
                    "scenario": "scene-0138-extreme-00",
                    "support_object_id": 9,
                    "problems": [],
                },
                {
                    "audit_id": "ttc_medium_a",
                    "scenario": "scene-0071-medium-01",
                    "support_object_id": 10,
                    "problems": [],
                },
            ],
        },
    )
    iter84 = _write_json(
        tmp_path / "iter84.json",
        {"verdict": iter84_verdict, "infra_problems": [], "events": events},
    )
    return iter59, iter80, iter83, iter84


def test_path_horizon_bridge_timing_split_complete(tmp_path: Path) -> None:
    report = timing.build_report(*_reports(tmp_path))
    labels = {(row["audit_id"], row["event_role"]): row["row_label"] for row in report["events"]}

    assert report["verdict"] == "HUGSIM_PATH_HORIZON_BRIDGE_TIMING_SPLIT_COMPLETE"
    assert set(labels.values()) == {"path_horizon_support_bridge_timing_split"}
    assert report["summary"]["selected_bridge_supported_events"] == 0
    assert report["summary"]["support_bridge_supported_events"] == 3
    assert report["summary"]["timing_comparison_counts"]["selected_lower_cpa"] == 3
    assert report["summary"]["timing_comparison_counts"]["selected_better_cpa_rank"] == 3
    assert report["summary"]["timing_comparison_counts"]["support_better_bridge"] == 3

    for row in report["events"]:
        assert row["selected_metric"]["cpa_horizon_index"] == 1
        assert row["selected_metric"]["cpa_horizon_time_s"] == 0.5
        assert row["support_metric"]["cpa_horizon_index"] == 1
        assert row["support_bridge"]["provenance_timestamp"] is not None
        assert row["support_bridge"]["timing_label"] in {
            "provenance_at_event",
            "provenance_after_event",
        }


def test_path_horizon_timing_blocks_bad_iter84_verdict(tmp_path: Path) -> None:
    report = timing.build_report(*_reports(tmp_path, iter84_verdict="WRONG"))

    assert report["verdict"] == "HUGSIM_PATH_HORIZON_BRIDGE_TIMING_BLOCKED"
    assert report["events"] == []
    assert "iter84-verdict-not-HUGSIM_SELECTED_SURFACE_SUPPORT_BRIDGE_SPLIT_COMPLETE" in report["infra_problems"]
