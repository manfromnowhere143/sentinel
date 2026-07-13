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
    / "iter80_hugsim_selected_all_provenance_bridge"
    / "analyze_selected_all_provenance_bridge.py"
)
SPEC = importlib.util.spec_from_file_location("iter80_selected_all_provenance", MODULE_PATH)
assert SPEC is not None
selected_all_provenance = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(selected_all_provenance)


def _write_json(path: Path, data: dict) -> Path:
    path.write_text(json.dumps(data))
    return path


def _episode(
    tmp_path: Path,
    audit_id: str,
    scenario: str,
    rows: list[dict],
    provenance_rows: list[dict],
) -> dict:
    episode_dir = tmp_path / f"{audit_id}__{scenario}__on"
    episode_dir.mkdir(parents=True, exist_ok=True)
    (episode_dir / "sentinel_iter48_decisions.jsonl").write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n"
    )
    (episode_dir / "eval.json").write_text(json.dumps({"collision_provenance": provenance_rows}))
    return {
        "audit_id": audit_id,
        "scenario": scenario,
        "support_label": "post_collision_fire",
        "episode_dir": str(episode_dir),
        "first_fire_ts": rows[-1]["ts"],
        "first_fire_channel": "cross_channel",
        "fired_frames": 1,
        "brake_frames": 1,
        "first_foreground_ts": rows[-1]["ts"] - 1.75,
        "foreground_count": 1,
        "monitor_frames": len(rows),
    }


def _provenance(timestamp: float, collision_type: str = "background") -> dict:
    return {
        "source": "fixture",
        "timestamp": timestamp,
        "trajectory_index": 0,
        "collision_type": collision_type,
        "obs_index": 0,
        "obs_name": "fixture",
        "obs_box": [0.0, 1.0, 0.0, 1.5, 3.0, 1.5, 0.0],
    }


def _reports(tmp_path: Path, *, iter79_verdict: str = "HUGSIM_SELECTED_ACTIVE_SUPPORT_SUBTHRESHOLD_COMPLETE"):
    h = iter76_helpers
    iter59_rows = [
        _episode(
            tmp_path,
            "both_distinct_extreme",
            "scene-0138-extreme-00",
            [
                h._decision_row(5.0, [h._obj(5, [0.0, 1.0]), h._obj(9, [0.0, 9.0])]),
                h._decision_row(7.0, [h._obj(5, [0.0, 9.0]), h._obj(9, [0.0, 1.0])]),
            ],
            [_provenance(5.0), _provenance(7.0, "foreground")],
        ),
        _episode(
            tmp_path,
            "ttc_medium_a",
            "scene-0071-medium-01",
            [
                h._decision_row(2.5, [h._obj(6, [0.0, 1.0]), h._obj(10, [0.0, 9.0])]),
                h._decision_row(5.0, [h._obj(24, [0.0, 1.0]), h._obj(10, [0.0, 9.0])]),
            ],
            [_provenance(2.5), _provenance(5.0, "foreground")],
        ),
    ]
    iter59 = _write_json(
        tmp_path / "iter59.json",
        {"verdict": "ACTOR_MATCH_AUDIT_COMPLETE", "infra_problems": [], "episodes": iter59_rows},
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
    iter79 = _write_json(
        tmp_path / "iter79.json",
        {
            "verdict": iter79_verdict,
            "infra_problems": [],
            "events": [
                {
                    "audit_id": "both_distinct_extreme",
                    "scenario": "scene-0138-extreme-00",
                    "event_role": "pre",
                    "event_ts": 5.0,
                    "selected_object_id": 5,
                    "selected_state": "borderline",
                    "support_object_id": 9,
                    "support_band": "ambiguous",
                    "support_state": "subthreshold",
                    "problems": [],
                },
                {
                    "audit_id": "ttc_medium_a",
                    "scenario": "scene-0071-medium-01",
                    "event_role": "pre",
                    "event_ts": 2.5,
                    "selected_object_id": 6,
                    "selected_state": "borderline",
                    "support_object_id": 10,
                    "support_band": "match",
                    "support_state": "subthreshold",
                    "problems": [],
                },
                {
                    "audit_id": "ttc_medium_a",
                    "scenario": "scene-0071-medium-01",
                    "event_role": "active",
                    "event_ts": 5.0,
                    "selected_object_id": 24,
                    "selected_state": "active",
                    "support_object_id": 10,
                    "support_band": "match",
                    "support_state": "subthreshold",
                    "problems": [],
                },
            ],
        },
    )
    return iter59, iter77, iter79


def test_selected_all_provenance_match_complete(tmp_path: Path) -> None:
    report = selected_all_provenance.build_report(*_reports(tmp_path))
    labels = {(row["audit_id"], row["event_role"]): row["row_label"] for row in report["events"]}

    assert report["verdict"] == "HUGSIM_SELECTED_ALL_PROVENANCE_MATCH_COMPLETE"
    assert labels[("both_distinct_extreme", "pre")] == "selected_all_provenance_match"
    assert labels[("ttc_medium_a", "pre")] == "selected_all_provenance_match"
    assert labels[("ttc_medium_a", "active")] == "selected_all_provenance_match"
    assert report["summary"]["provenance_type_counts"]["background"] == 3


def test_selected_all_provenance_blocks_bad_iter79_verdict(tmp_path: Path) -> None:
    report = selected_all_provenance.build_report(*_reports(tmp_path, iter79_verdict="WRONG"))

    assert report["verdict"] == "HUGSIM_SELECTED_ALL_PROVENANCE_BLOCKED"
    assert report["events"] == []
    assert "iter79-verdict-not-HUGSIM_SELECTED_ACTIVE_SUPPORT_SUBTHRESHOLD_COMPLETE" in report["infra_problems"]
