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
    / "iter79_hugsim_selected_surface_decomposition"
    / "analyze_selected_surface_decomposition.py"
)
SPEC = importlib.util.spec_from_file_location("iter79_selected_surface", MODULE_PATH)
assert SPEC is not None
selected_surface = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(selected_surface)


def _write_json(path: Path, data: dict) -> Path:
    path.write_text(json.dumps(data))
    return path


def _reports(tmp_path: Path, *, iter78_verdict: str = "HUGSIM_SUPPORT_OBJECT_RANKING_MIXED_COMPLETE"):
    h = iter76_helpers
    iter59_rows = [
        h._episode(
            tmp_path,
            "both_distinct_extreme",
            "scene-0138-extreme-00",
            [
                h._decision_row(5.0, [h._obj(5, [0.0, 1.0]), h._obj(9, [0.0, 9.0])]),
                h._decision_row(7.0, [h._obj(5, [0.0, 9.0]), h._obj(9, [0.0, 1.0])]),
            ],
            [0.0, 1.0],
        ),
        h._episode(
            tmp_path,
            "ttc_medium_a",
            "scene-0071-medium-01",
            [
                h._decision_row(2.5, [h._obj(6, [0.0, 1.0]), h._obj(10, [0.0, 9.0])]),
                h._decision_row(5.0, [h._obj(24, [0.0, 1.0]), h._obj(10, [0.0, 9.0])]),
            ],
            [0.0, 1.0],
        ),
    ]
    iter59 = _write_json(
        tmp_path / "iter59.json",
        {"verdict": "ACTOR_MATCH_AUDIT_COMPLETE", "infra_problems": [], "episodes": iter59_rows},
    )
    iter75 = _write_json(
        tmp_path / "iter75.json",
        {
            "verdict": "HUGSIM_CROSS_CHANNEL_OBJECT_SWITCH_COMPLETE",
            "infra_problems": [],
            "episodes": [
                {
                    "audit_id": "both_distinct_extreme",
                    "scenario": "scene-0138-extreme-00",
                    "row_label": "object_switch_cross_channel_handoff",
                    "pre_objects": {"object_ids": [5]},
                    "active_objects": {"object_ids": [9]},
                },
                {
                    "audit_id": "ttc_medium_a",
                    "scenario": "scene-0071-medium-01",
                    "row_label": "object_switch_cross_channel_handoff",
                    "pre_objects": {"object_ids": [6]},
                    "active_objects": {"object_ids": [24]},
                },
            ],
        },
    )
    iter77 = _write_json(
        tmp_path / "iter77.json",
        {
            "verdict": "HUGSIM_EVENT_SET_FOREGROUND_SUPPORT_MIXED_COMPLETE",
            "infra_problems": [],
            "episodes": [
                {
                    "audit_id": "both_distinct_extreme",
                    "scenario": "scene-0138-extreme-00",
                    "row_label": "pre_set_foreground_ambiguous",
                    "pre_event_set": {
                        "event_ts": 5.0,
                        "distance_band": "ambiguous",
                        "best_variant": {"object_id": 9},
                    },
                    "active_event_set": {
                        "event_ts": 7.0,
                        "distance_band": "no_support",
                        "best_variant": {"object_id": 9},
                    },
                },
                {
                    "audit_id": "ttc_medium_a",
                    "scenario": "scene-0071-medium-01",
                    "row_label": "both_sets_foreground_match",
                    "pre_event_set": {
                        "event_ts": 2.5,
                        "distance_band": "match",
                        "best_variant": {"object_id": 10},
                    },
                    "active_event_set": {
                        "event_ts": 5.0,
                        "distance_band": "match",
                        "best_variant": {"object_id": 10},
                    },
                },
            ],
        },
    )
    iter78 = _write_json(
        tmp_path / "iter78.json",
        {
            "verdict": iter78_verdict,
            "infra_problems": [],
            "events": [
                {
                    "audit_id": "both_distinct_extreme",
                    "scenario": "scene-0138-extreme-00",
                    "event_role": "pre",
                    "event_ts": 5.0,
                    "row_label": "support_object_nonselected_subthreshold",
                    "selected_object_id": 5,
                    "support_object_id": 9,
                    "support_band": "ambiguous",
                    "problems": [],
                },
                {
                    "audit_id": "ttc_medium_a",
                    "scenario": "scene-0071-medium-01",
                    "event_role": "pre",
                    "event_ts": 2.5,
                    "row_label": "support_object_nonselected_subthreshold",
                    "selected_object_id": 6,
                    "support_object_id": 10,
                    "support_band": "match",
                    "problems": [],
                },
                {
                    "audit_id": "ttc_medium_a",
                    "scenario": "scene-0071-medium-01",
                    "event_role": "active",
                    "event_ts": 5.0,
                    "row_label": "support_object_nonselected_subthreshold",
                    "selected_object_id": 24,
                    "support_object_id": 10,
                    "support_band": "match",
                    "problems": [],
                },
            ],
        },
    )
    return iter59, iter75, iter77, iter78


def test_selected_active_support_subthreshold_complete(tmp_path: Path) -> None:
    report = selected_surface.build_report(*_reports(tmp_path))
    labels = {(row["audit_id"], row["event_role"]): row["row_label"] for row in report["events"]}

    assert report["verdict"] == "HUGSIM_SELECTED_ACTIVE_SUPPORT_SUBTHRESHOLD_COMPLETE"
    assert labels[("both_distinct_extreme", "pre")] == "selected_active_support_subthreshold"
    assert labels[("ttc_medium_a", "pre")] == "selected_active_support_subthreshold"
    assert labels[("ttc_medium_a", "active")] == "selected_active_support_subthreshold"


def test_selected_surface_blocks_bad_iter78_verdict(tmp_path: Path) -> None:
    report = selected_surface.build_report(*_reports(tmp_path, iter78_verdict="WRONG"))

    assert report["verdict"] == "HUGSIM_SELECTED_SURFACE_DECOMPOSITION_BLOCKED"
    assert report["events"] == []
    assert "iter78-verdict-not-HUGSIM_SUPPORT_OBJECT_RANKING_MIXED_COMPLETE" in report["infra_problems"]
