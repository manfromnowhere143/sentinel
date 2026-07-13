from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ITER77_TEST_PATH = Path(__file__).resolve().parents[0] / "test_iter77_event_object_set_bridge.py"
ITER77_SPEC = importlib.util.spec_from_file_location("iter77_test_helpers", ITER77_TEST_PATH)
assert ITER77_SPEC is not None
iter77_helpers = importlib.util.module_from_spec(ITER77_SPEC)
assert ITER77_SPEC.loader is not None
ITER77_SPEC.loader.exec_module(iter77_helpers)

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter78_hugsim_support_object_ranking"
    / "analyze_support_object_ranking.py"
)
SPEC = importlib.util.spec_from_file_location("iter78_support_object_ranking", MODULE_PATH)
assert SPEC is not None
support_ranking = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(support_ranking)


def _write_json(path: Path, data: dict) -> Path:
    path.write_text(json.dumps(data))
    return path


def _reports(tmp_path: Path, *, iter77_verdict: str = "HUGSIM_EVENT_SET_FOREGROUND_SUPPORT_MIXED_COMPLETE"):
    h = iter77_helpers.iter76_helpers
    iter59_rows = [
        h._episode(
            tmp_path,
            "both_distinct_extreme",
            "scene-0138-extreme-00",
            [
                h._decision_row(5.0, [h._obj(5, [0.0, 9.0]), h._obj(9, [0.0, 2.5])]),
                h._decision_row(7.0, [h._obj(5, [0.0, 9.0]), h._obj(9, [0.0, 9.0])]),
            ],
            [0.0, 2.5],
        ),
        h._episode(
            tmp_path,
            "ttc_medium_a",
            "scene-0071-medium-01",
            [
                h._decision_row(2.5, [h._obj(6, [0.0, 9.0]), h._obj(10, [0.0, 2.5])]),
                h._decision_row(5.0, [h._obj(24, [0.0, 9.0]), h._obj(10, [0.0, 2.5])]),
            ],
            [0.0, 2.5],
        ),
    ]
    iter59 = _write_json(
        tmp_path / "iter59.json",
        {"verdict": "ACTOR_MATCH_AUDIT_COMPLETE", "infra_problems": [], "episodes": iter59_rows},
    )
    iter70 = _write_json(
        tmp_path / "iter70.json",
        {
            "verdict": "HUGSIM_STRUCTURAL_TIMING_TAXONOMY_COMPLETE",
            "infra_problems": [],
            "episodes": [
                {
                    "audit_id": "both_distinct_extreme",
                    "scenario": "scene-0138-extreme-00",
                    "structural_label": "foreground_present_late_fire",
                },
                {
                    "audit_id": "ttc_medium_a",
                    "scenario": "scene-0071-medium-01",
                    "structural_label": "foreground_present_late_fire",
                },
            ],
        },
    )
    iter72 = _write_json(
        tmp_path / "iter72.json",
        {
            "verdict": "HUGSIM_LATE_FIRE_PREFIRE_MARGIN_COMPLETE",
            "infra_problems": [],
            "episodes": [
                {
                    "audit_id": "both_distinct_extreme",
                    "scenario": "scene-0138-extreme-00",
                    "row_label": "late_fire_prefire_near_cpa_margin",
                },
                {
                    "audit_id": "ttc_medium_a",
                    "scenario": "scene-0071-medium-01",
                    "row_label": "late_fire_prefire_near_ttc_margin",
                },
            ],
        },
    )
    iter73 = _write_json(
        tmp_path / "iter73.json",
        {
            "verdict": "HUGSIM_MARGIN_TRANSITION_SPLIT_COMPLETE",
            "infra_problems": [],
            "episodes": [
                {
                    "audit_id": "both_distinct_extreme",
                    "scenario": "scene-0138-extreme-00",
                    "row_label": "late_prefire_near_postcontact_active",
                },
                {
                    "audit_id": "ttc_medium_a",
                    "scenario": "scene-0071-medium-01",
                    "row_label": "late_prefire_near_postcontact_active",
                },
            ],
        },
    )
    iter74 = _write_json(
        tmp_path / "iter74.json",
        {
            "verdict": "HUGSIM_LATE_FIRE_CROSS_CHANNEL_DELAY_COMPLETE",
            "infra_problems": [],
            "episodes": [
                {
                    "audit_id": "both_distinct_extreme",
                    "scenario": "scene-0138-extreme-00",
                    "row_label": "cross_channel_late_activation",
                },
                {
                    "audit_id": "ttc_medium_a",
                    "scenario": "scene-0071-medium-01",
                    "row_label": "cross_channel_late_activation",
                },
            ],
        },
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
    iter76 = _write_json(
        tmp_path / "iter76.json",
        {
            "verdict": "HUGSIM_SWITCH_FOREGROUND_BOTH_OR_AMBIGUOUS_COMPLETE",
            "infra_problems": [],
            "episodes": [
                {
                    "audit_id": "both_distinct_extreme",
                    "scenario": "scene-0138-extreme-00",
                    "row_label": "no_foreground_bridge_support",
                },
                {
                    "audit_id": "ttc_medium_a",
                    "scenario": "scene-0071-medium-01",
                    "row_label": "no_foreground_bridge_support",
                },
            ],
        },
    )
    iter77 = _write_json(
        tmp_path / "iter77.json",
        {
            "verdict": iter77_verdict,
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
    return iter59, iter70, iter72, iter73, iter74, iter75, iter76, iter77


def test_support_object_nonselected_borderline_complete(tmp_path: Path) -> None:
    report = support_ranking.build_report(*_reports(tmp_path))
    labels = {(row["audit_id"], row["event_role"]): row["row_label"] for row in report["events"]}

    assert report["verdict"] == "HUGSIM_SUPPORT_OBJECT_NONSELECTED_BORDERLINE_COMPLETE"
    assert labels[("both_distinct_extreme", "pre")] == "support_object_nonselected_borderline"
    assert labels[("ttc_medium_a", "pre")] == "support_object_nonselected_borderline"
    assert labels[("ttc_medium_a", "active")] == "support_object_nonselected_borderline"


def test_support_object_ranking_blocks_bad_source_verdict(tmp_path: Path) -> None:
    report = support_ranking.build_report(*_reports(tmp_path, iter77_verdict="WRONG"))

    assert report["verdict"] == "HUGSIM_SUPPORT_OBJECT_RANKING_BLOCKED"
    assert report["events"] == []
    assert "iter77-verdict-not-HUGSIM_EVENT_SET_FOREGROUND_SUPPORT_MIXED_COMPLETE" in report["infra_problems"]
