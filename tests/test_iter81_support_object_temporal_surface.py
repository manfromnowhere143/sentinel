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
    / "iter81_hugsim_support_object_temporal_surface"
    / "analyze_support_object_temporal_surface.py"
)
SPEC = importlib.util.spec_from_file_location("iter81_support_temporal", MODULE_PATH)
assert SPEC is not None
support_temporal = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(support_temporal)


def _write_json(path: Path, data: dict) -> Path:
    path.write_text(json.dumps(data))
    return path


def _reports(tmp_path: Path, *, iter80_verdict: str = "HUGSIM_SELECTED_ALL_PROVENANCE_NO_SUPPORT_COMPLETE"):
    h = iter76_helpers
    iter59_rows = [
        h._episode(
            tmp_path,
            "both_distinct_extreme",
            "scene-0138-extreme-00",
            [
                h._decision_row(4.0, [h._obj(9, [0.0, 1.0])]),
                h._decision_row(5.0, [h._obj(5, [0.0, 1.0]), h._obj(9, [0.0, 9.0])]),
                h._decision_row(7.0, [h._obj(5, [0.0, 9.0]), h._obj(9, [0.0, 9.0])]),
            ],
            [0.0, 1.0],
        ),
        h._episode(
            tmp_path,
            "ttc_medium_a",
            "scene-0071-medium-01",
            [
                h._decision_row(1.0, [h._obj(10, [0.0, 2.5])]),
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
    iter78 = _write_json(
        tmp_path / "iter78.json",
        {
            "verdict": "HUGSIM_SUPPORT_OBJECT_RANKING_MIXED_COMPLETE",
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
    iter79 = _write_json(
        tmp_path / "iter79.json",
        {
            "verdict": "HUGSIM_SELECTED_ACTIVE_SUPPORT_SUBTHRESHOLD_COMPLETE",
            "infra_problems": [],
            "events": [
                {
                    "audit_id": "both_distinct_extreme",
                    "scenario": "scene-0138-extreme-00",
                    "event_role": "pre",
                    "event_ts": 5.0,
                    "selected_object_id": 5,
                    "support_object_id": 9,
                    "support_state": "subthreshold",
                    "problems": [],
                },
                {
                    "audit_id": "ttc_medium_a",
                    "scenario": "scene-0071-medium-01",
                    "event_role": "pre",
                    "event_ts": 2.5,
                    "selected_object_id": 6,
                    "support_object_id": 10,
                    "support_state": "subthreshold",
                    "problems": [],
                },
                {
                    "audit_id": "ttc_medium_a",
                    "scenario": "scene-0071-medium-01",
                    "event_role": "active",
                    "event_ts": 5.0,
                    "selected_object_id": 24,
                    "support_object_id": 10,
                    "support_state": "subthreshold",
                    "problems": [],
                },
            ],
        },
    )
    iter80 = _write_json(
        tmp_path / "iter80.json",
        {
            "verdict": iter80_verdict,
            "infra_problems": [],
            "events": [
                {
                    "audit_id": "both_distinct_extreme",
                    "scenario": "scene-0138-extreme-00",
                    "event_role": "pre",
                    "event_ts": 5.0,
                    "row_label": "selected_all_provenance_no_support",
                    "selected_object_id": 5,
                    "support_object_id": 9,
                    "problems": [],
                },
                {
                    "audit_id": "ttc_medium_a",
                    "scenario": "scene-0071-medium-01",
                    "event_role": "pre",
                    "event_ts": 2.5,
                    "row_label": "selected_all_provenance_no_support",
                    "selected_object_id": 6,
                    "support_object_id": 10,
                    "problems": [],
                },
                {
                    "audit_id": "ttc_medium_a",
                    "scenario": "scene-0071-medium-01",
                    "event_role": "active",
                    "event_ts": 5.0,
                    "row_label": "selected_all_provenance_no_support",
                    "selected_object_id": 24,
                    "support_object_id": 10,
                    "problems": [],
                },
            ],
        },
    )
    return iter59, iter78, iter79, iter80


def test_support_object_ever_active_complete(tmp_path: Path) -> None:
    report = support_temporal.build_report(*_reports(tmp_path))
    labels = {row["audit_id"]: row["row_label"] for row in report["objects"]}

    assert report["verdict"] == "HUGSIM_SUPPORT_OBJECT_EVER_ACTIVE_COMPLETE"
    assert labels["both_distinct_extreme"] == "support_object_ever_active"
    assert labels["ttc_medium_a"] == "support_object_borderline_only"


def test_support_object_temporal_blocks_bad_iter80_verdict(tmp_path: Path) -> None:
    report = support_temporal.build_report(*_reports(tmp_path, iter80_verdict="WRONG"))

    assert report["verdict"] == "HUGSIM_SUPPORT_OBJECT_TEMPORAL_BLOCKED"
    assert report["objects"] == []
    assert "iter80-verdict-not-HUGSIM_SELECTED_ALL_PROVENANCE_NO_SUPPORT_COMPLETE" in report["infra_problems"]
