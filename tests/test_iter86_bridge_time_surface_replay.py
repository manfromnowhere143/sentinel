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
    / "iter86_hugsim_bridge_time_surface_replay"
    / "analyze_bridge_time_surface_replay.py"
)
SPEC = importlib.util.spec_from_file_location("iter86_bridge_time", MODULE_PATH)
assert SPEC is not None
bridge_time = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(bridge_time)


def _write_json(path: Path, data: dict) -> Path:
    path.write_text(json.dumps(data))
    return path


def _event(
    audit_id: str,
    scenario: str,
    role: str,
    event_ts: float,
    support_object_id: int,
    support_bridge_band: str,
    bridge_ts: float,
) -> dict:
    return {
        "audit_id": audit_id,
        "scenario": scenario,
        "event_role": role,
        "event_ts": event_ts,
        "support_object_id": support_object_id,
        "support_state": "subthreshold",
        "selected_bridge": {"distance_band": "no_support"},
        "support_bridge": {
            "distance_band": support_bridge_band,
            "provenance_timestamp": bridge_ts,
            "timing_label": "provenance_after_event",
        },
        "row_label": "path_horizon_support_bridge_timing_split",
        "problems": [],
    }


def _reports(
    tmp_path: Path,
    *,
    iter85_verdict: str = "HUGSIM_PATH_HORIZON_BRIDGE_TIMING_SPLIT_COMPLETE",
):
    h = iter76_helpers
    iter59_rows = [
        h._episode(
            tmp_path,
            "both_distinct_extreme",
            "scene-0138-extreme-00",
            [
                h._decision_row(5.0, [h._obj(5, [0.0, 1.0]), h._obj(9, [0.0, 9.0])]),
                h._decision_row(5.5, [h._obj(9, [0.0, 2.0])]),
            ],
            [0.0, 2.0],
        ),
        h._episode(
            tmp_path,
            "ttc_medium_a",
            "scene-0071-medium-01",
            [
                h._decision_row(2.5, [h._obj(10, [0.0, 9.0])]),
                h._decision_row(4.0, [h._obj(10, [0.0, 9.0])]),
                h._decision_row(5.0, [h._obj(10, [0.0, 9.0])]),
                h._decision_row(6.0, [h._obj(10, [0.0, 9.0])]),
            ],
            [0.0, 9.0],
        ),
    ]
    iter59 = _write_json(
        tmp_path / "iter59.json",
        {"verdict": "ACTOR_MATCH_AUDIT_COMPLETE", "infra_problems": [], "episodes": iter59_rows},
    )
    objects = [
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
    ]
    iter81 = _write_json(
        tmp_path / "iter81.json",
        {
            "verdict": "HUGSIM_SUPPORT_OBJECT_EVER_ACTIVE_COMPLETE",
            "infra_problems": [],
            "objects": objects,
        },
    )
    iter83 = _write_json(
        tmp_path / "iter83.json",
        {
            "verdict": "HUGSIM_BRIDGE_SUPPORTED_SURFACE_MISS_MIXED_COMPLETE",
            "infra_problems": [],
            "objects": objects,
        },
    )
    iter85 = _write_json(
        tmp_path / "iter85.json",
        {
            "verdict": iter85_verdict,
            "infra_problems": [],
            "events": [
                _event("both_distinct_extreme", "scene-0138-extreme-00", "pre", 5.0, 9, "ambiguous", 5.5),
                _event("ttc_medium_a", "scene-0071-medium-01", "pre", 2.5, 10, "match", 4.0),
                _event("ttc_medium_a", "scene-0071-medium-01", "active", 5.0, 10, "match", 6.0),
            ],
        },
    )
    return iter59, iter81, iter83, iter85


def test_bridge_time_surface_replay_mixed_complete(tmp_path: Path) -> None:
    report = bridge_time.build_report(*_reports(tmp_path))
    labels = {(row["audit_id"], row["event_role"]): row["row_label"] for row in report["events"]}

    assert report["verdict"] == "HUGSIM_BRIDGE_TIME_SURFACE_REPLAY_MIXED_COMPLETE"
    assert labels[("both_distinct_extreme", "pre")] == "support_bridge_time_surface_arrival"
    assert labels[("ttc_medium_a", "pre")] == "support_bridge_time_surface_miss"
    assert labels[("ttc_medium_a", "active")] == "support_bridge_time_surface_miss"
    assert report["summary"]["row_label_counts"]["support_bridge_time_surface_arrival"] == 1
    assert report["summary"]["row_label_counts"]["support_bridge_time_surface_miss"] == 2
    assert report["summary"]["state_transition_counts"]["subthreshold->borderline"] == 1
    assert report["summary"]["state_transition_counts"]["subthreshold->subthreshold"] == 2


def test_bridge_time_surface_replay_blocks_bad_iter85_verdict(tmp_path: Path) -> None:
    report = bridge_time.build_report(*_reports(tmp_path, iter85_verdict="WRONG"))

    assert report["verdict"] == "HUGSIM_BRIDGE_TIME_SURFACE_REPLAY_BLOCKED"
    assert report["events"] == []
    assert "iter85-verdict-not-HUGSIM_PATH_HORIZON_BRIDGE_TIMING_SPLIT_COMPLETE" in report["infra_problems"]
