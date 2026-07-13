from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter76_hugsim_switch_foreground_bridge"
    / "analyze_switch_foreground_bridge.py"
)
SPEC = importlib.util.spec_from_file_location("iter76_switch_foreground_bridge", MODULE_PATH)
assert SPEC is not None
switch_bridge = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(switch_bridge)


def _write_json(path: Path, data: dict) -> Path:
    path.write_text(json.dumps(data))
    return path


def _obj(object_id: int, world: list[float], vel: list[float] | None = None) -> dict:
    return {"id": object_id, "score": 0.9, "world": world, "vel": vel or [0.0, 0.0]}


def _decision_row(ts: float, objs: list[dict]) -> dict:
    return {
        "ts": ts,
        "frame_index": int(ts * 4),
        "fired": False,
        "brake": False,
        "release": False,
        "min_ttc": 1_000_000_000.0,
        "min_cpa": 10.0,
        "l2g_r_mat": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        "l2g_t": [0.0, 0.0, 0.0],
        "traj": [[0.0, 0.0], [0.0, 0.0]],
        "params": {
            "ttc_thresh": 2.5,
            "cpa_margin": 1.5,
            "dt": 0.5,
            "max_gap": 30.0,
            "min_closing": 3.0,
            "min_score": 0.3,
            "release_k": 4,
        },
        "objs": objs,
    }


def _episode(tmp_path: Path, audit_id: str, scenario: str, rows: list[dict], foreground_xy: list[float]) -> dict:
    episode_dir = tmp_path / f"{audit_id}__{scenario}__on"
    episode_dir.mkdir(parents=True, exist_ok=True)
    (episode_dir / "sentinel_iter48_decisions.jsonl").write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n"
    )
    (episode_dir / "eval.json").write_text(json.dumps({
        "collision_provenance": [
            {
                "collision_type": "foreground",
                "timestamp": rows[-1]["ts"],
                "obs_box": foreground_xy,
                "obs_index": 0,
                "obs_name": "fixture",
            }
        ]
    }))
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


def _reports(
    tmp_path: Path,
    *,
    iter75_verdict: str = "HUGSIM_CROSS_CHANNEL_OBJECT_SWITCH_COMPLETE",
    active_match: bool = True,
) -> tuple[Path, Path, Path, Path, Path, Path]:
    if active_match:
        foreground_a = [0.0, 1.0]
        foreground_b = [0.0, 1.0]
        pre_a = [0.0, 9.0]
        pre_b = [0.0, 9.0]
    else:
        foreground_a = [0.0, 2.0]
        foreground_b = [0.0, 2.0]
        pre_a = [0.0, 2.0]
        pre_b = [0.0, 2.0]
    iter59_rows = [
        _episode(
            tmp_path,
            "both_distinct_extreme",
            "scene-0138-extreme-00",
            [
                _decision_row(5.0, [_obj(5, pre_a), _obj(9, [0.0, 9.0])]),
                _decision_row(7.0, [_obj(5, [0.0, 9.0]), _obj(9, [0.0, 1.0])]),
            ],
            foreground_a,
        ),
        _episode(
            tmp_path,
            "ttc_medium_a",
            "scene-0071-medium-01",
            [
                _decision_row(2.5, [_obj(6, pre_b), _obj(24, [0.0, 9.0])]),
                _decision_row(5.0, [_obj(6, [0.0, 9.0]), _obj(24, [0.0, 1.0])]),
            ],
            foreground_b,
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
            "verdict": iter75_verdict,
            "infra_problems": [],
            "episodes": [
                {
                    "audit_id": "both_distinct_extreme",
                    "scenario": "scene-0138-extreme-00",
                    "row_label": "object_switch_cross_channel_handoff",
                    "pre_ts": 5.0,
                    "active_ts": 7.0,
                    "pre_objects": {"object_ids": [5]},
                    "active_objects": {"object_ids": [9]},
                },
                {
                    "audit_id": "ttc_medium_a",
                    "scenario": "scene-0071-medium-01",
                    "row_label": "object_switch_cross_channel_handoff",
                    "pre_ts": 2.5,
                    "active_ts": 5.0,
                    "pre_objects": {"object_ids": [6]},
                    "active_objects": {"object_ids": [24]},
                },
            ],
        },
    )
    return iter59, iter70, iter72, iter73, iter74, iter75


def test_switch_foreground_active_match_complete(tmp_path: Path) -> None:
    report = switch_bridge.build_report(*_reports(tmp_path, active_match=True))
    labels = {row["audit_id"]: row["row_label"] for row in report["episodes"]}

    assert report["verdict"] == "HUGSIM_SWITCH_FOREGROUND_ACTIVE_MATCH_COMPLETE"
    assert labels["both_distinct_extreme"] == "active_object_foreground_match"
    assert labels["ttc_medium_a"] == "active_object_foreground_match"


def test_switch_foreground_both_match_complete(tmp_path: Path) -> None:
    report = switch_bridge.build_report(*_reports(tmp_path, active_match=False))
    labels = {row["audit_id"]: row["row_label"] for row in report["episodes"]}

    assert report["verdict"] == "HUGSIM_SWITCH_FOREGROUND_BOTH_OR_AMBIGUOUS_COMPLETE"
    assert labels["both_distinct_extreme"] == "both_objects_foreground_match"
    assert labels["ttc_medium_a"] == "both_objects_foreground_match"


def test_switch_foreground_bridge_blocks_bad_source_verdict(tmp_path: Path) -> None:
    report = switch_bridge.build_report(*_reports(tmp_path, iter75_verdict="WRONG"))

    assert report["verdict"] == "HUGSIM_SWITCH_FOREGROUND_BRIDGE_BLOCKED"
    assert report["episodes"] == []
    assert "iter75-verdict-not-HUGSIM_CROSS_CHANNEL_OBJECT_SWITCH_COMPLETE" in report["infra_problems"]
