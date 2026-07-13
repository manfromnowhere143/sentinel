from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter75_hugsim_cross_channel_object_handoff"
    / "analyze_cross_channel_object_handoff.py"
)
SPEC = importlib.util.spec_from_file_location("iter75_cross_channel_object_handoff", MODULE_PATH)
assert SPEC is not None
object_handoff = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(object_handoff)


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


def _cpa_near_row(ts: float, object_id: int) -> dict:
    row = _decision_row(ts, [_obj(object_id, [0.0, 2.0]), _obj(99, [0.0, 8.0])])
    row["min_cpa"] = 2.0
    return row


def _cpa_active_row(ts: float, object_id: int) -> dict:
    row = _decision_row(ts, [_obj(object_id, [0.0, 1.0]), _obj(99, [0.0, 8.0])])
    row["min_cpa"] = 1.0
    return row


def _ttc_near_row(ts: float, object_id: int) -> dict:
    row = _decision_row(ts, [_obj(object_id, [12.0, 0.0], [-4.0, 0.0]), _obj(99, [0.0, 8.0])])
    row["min_ttc"] = 3.0
    return row


def _ttc_active_row(ts: float, object_id: int) -> dict:
    row = _decision_row(ts, [_obj(object_id, [8.0, 0.0], [-4.0, 0.0]), _obj(99, [0.0, 8.0])])
    row["min_ttc"] = 2.0
    return row


def _episode(tmp_path: Path, audit_id: str, scenario: str, rows: list[dict]) -> dict:
    episode_dir = tmp_path / f"{audit_id}__{scenario}__on"
    episode_dir.mkdir(parents=True, exist_ok=True)
    (episode_dir / "sentinel_iter48_decisions.jsonl").write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n"
    )
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
        "foreground_count": 2,
        "monitor_frames": len(rows),
    }


def _reports(
    tmp_path: Path,
    *,
    iter74_verdict: str = "HUGSIM_LATE_FIRE_CROSS_CHANNEL_DELAY_COMPLETE",
    same_object: bool = False,
) -> tuple[Path, Path, Path, Path, Path]:
    both_pre_id = 1
    both_active_id = 1 if same_object else 2
    ttc_pre_id = 3
    ttc_active_id = 3 if same_object else 4
    iter59_rows = [
        _episode(
            tmp_path,
            "both_distinct_extreme",
            "scene-0138-extreme-00",
            [_decision_row(0.0, [_obj(99, [0.0, 9.0])]), _cpa_near_row(5.0, both_pre_id), _ttc_active_row(7.0, both_active_id)],
        ),
        _episode(
            tmp_path,
            "ttc_medium_a",
            "scene-0071-medium-01",
            [_decision_row(0.0, [_obj(99, [0.0, 9.0])]), _ttc_near_row(3.0, ttc_pre_id), _cpa_active_row(5.0, ttc_active_id)],
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
            "verdict": iter74_verdict,
            "infra_problems": [],
            "episodes": [
                {
                    "audit_id": "both_distinct_extreme",
                    "scenario": "scene-0138-extreme-00",
                    "row_label": "cross_channel_late_activation",
                    "timeline": {
                        "pre_foreground_near_channels": ["cpa"],
                        "closest_pre_cpa_ts": 5.0,
                        "first_active_channels": ["ttc"],
                        "first_active_ttc_ts": 7.0,
                    },
                },
                {
                    "audit_id": "ttc_medium_a",
                    "scenario": "scene-0071-medium-01",
                    "row_label": "cross_channel_late_activation",
                    "timeline": {
                        "pre_foreground_near_channels": ["ttc"],
                        "closest_pre_ttc_ts": 3.0,
                        "first_active_channels": ["cpa"],
                        "first_active_cpa_ts": 5.0,
                    },
                },
            ],
        },
    )
    return iter59, iter70, iter72, iter73, iter74


def test_cross_channel_object_switch_complete(tmp_path: Path) -> None:
    report = object_handoff.build_report(*_reports(tmp_path))
    labels = {row["audit_id"]: row["row_label"] for row in report["episodes"]}

    assert report["verdict"] == "HUGSIM_CROSS_CHANNEL_OBJECT_SWITCH_COMPLETE"
    assert labels["both_distinct_extreme"] == "object_switch_cross_channel_handoff"
    assert labels["ttc_medium_a"] == "object_switch_cross_channel_handoff"


def test_cross_channel_same_object_complete(tmp_path: Path) -> None:
    report = object_handoff.build_report(*_reports(tmp_path, same_object=True))
    labels = {row["audit_id"]: row["row_label"] for row in report["episodes"]}

    assert report["verdict"] == "HUGSIM_CROSS_CHANNEL_SAME_OBJECT_COMPLETE"
    assert labels["both_distinct_extreme"] == "same_object_cross_channel_handoff"
    assert labels["ttc_medium_a"] == "same_object_cross_channel_handoff"


def test_cross_channel_object_handoff_blocks_bad_source_verdict(tmp_path: Path) -> None:
    report = object_handoff.build_report(*_reports(tmp_path, iter74_verdict="WRONG"))

    assert report["verdict"] == "HUGSIM_CROSS_CHANNEL_OBJECT_HANDOFF_BLOCKED"
    assert report["episodes"] == []
    assert "iter74-verdict-not-HUGSIM_LATE_FIRE_CROSS_CHANNEL_DELAY_COMPLETE" in report["infra_problems"]
