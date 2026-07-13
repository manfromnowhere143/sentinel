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
    / "iter84_hugsim_selected_support_arbitration"
    / "analyze_selected_support_arbitration.py"
)
SPEC = importlib.util.spec_from_file_location("iter84_arbitration", MODULE_PATH)
assert SPEC is not None
arbitration = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(arbitration)


def _write_json(path: Path, data: dict) -> Path:
    path.write_text(json.dumps(data))
    return path


def _reports(
    tmp_path: Path,
    *,
    iter80_verdict: str = "HUGSIM_SELECTED_ALL_PROVENANCE_NO_SUPPORT_COMPLETE",
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
        {
            "audit_id": "both_distinct_extreme",
            "scenario": "scene-0138-extreme-00",
            "event_role": "pre",
            "event_ts": 5.0,
            "selected_object_id": 5,
            "support_object_id": 9,
            "support_band": "match",
            "selected_state": "active",
            "support_state": "subthreshold",
            "row_label": "selected_active_support_subthreshold",
            "problems": [],
        },
        {
            "audit_id": "ttc_medium_a",
            "scenario": "scene-0071-medium-01",
            "event_role": "pre",
            "event_ts": 2.5,
            "selected_object_id": 6,
            "support_object_id": 10,
            "support_band": "match",
            "selected_state": "active",
            "support_state": "subthreshold",
            "row_label": "selected_active_support_subthreshold",
            "problems": [],
        },
        {
            "audit_id": "ttc_medium_a",
            "scenario": "scene-0071-medium-01",
            "event_role": "active",
            "event_ts": 5.0,
            "selected_object_id": 24,
            "support_object_id": 10,
            "support_band": "match",
            "selected_state": "active",
            "support_state": "subthreshold",
            "row_label": "selected_active_support_subthreshold",
            "problems": [],
        },
    ]
    iter79 = _write_json(
        tmp_path / "iter79.json",
        {
            "verdict": "HUGSIM_SELECTED_ACTIVE_SUPPORT_SUBTHRESHOLD_COMPLETE",
            "infra_problems": [],
            "events": events,
        },
    )
    iter80 = _write_json(
        tmp_path / "iter80.json",
        {
            "verdict": iter80_verdict,
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
                    "row_label": "bridge_supported_borderline_ttc_only",
                    "problems": [],
                },
                {
                    "audit_id": "ttc_medium_a",
                    "scenario": "scene-0071-medium-01",
                    "support_object_id": 10,
                    "row_label": "bridge_supported_subthreshold_no_finite_ttc",
                    "problems": [],
                },
            ],
        },
    )
    return iter59, iter79, iter80, iter83


def test_selected_surface_support_bridge_split_complete(tmp_path: Path) -> None:
    report = arbitration.build_report(*_reports(tmp_path))
    labels = {(row["audit_id"], row["event_role"]): row["row_label"] for row in report["events"]}

    assert report["verdict"] == "HUGSIM_SELECTED_SURFACE_SUPPORT_BRIDGE_SPLIT_COMPLETE"
    assert set(labels.values()) == {"selected_surface_support_bridge_split"}
    assert report["summary"]["selected_bridge_supported_events"] == 0
    assert report["summary"]["support_bridge_supported_events"] == 3
    assert report["summary"]["support_better_bridge_events"] == 3
    assert report["summary"]["hazard_advantage_counts"]["selected_lower_cpa"] == 3


def test_selected_support_arbitration_blocks_bad_iter80_verdict(tmp_path: Path) -> None:
    report = arbitration.build_report(*_reports(tmp_path, iter80_verdict="WRONG"))

    assert report["verdict"] == "HUGSIM_SELECTED_SUPPORT_ARBITRATION_BLOCKED"
    assert report["events"] == []
    assert "iter80-verdict-not-HUGSIM_SELECTED_ALL_PROVENANCE_NO_SUPPORT_COMPLETE" in report["infra_problems"]
