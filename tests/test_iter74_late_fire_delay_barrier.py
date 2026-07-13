from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter74_hugsim_late_fire_delay_barrier"
    / "analyze_late_fire_delay_barrier.py"
)
SPEC = importlib.util.spec_from_file_location("iter74_late_fire_delay_barrier", MODULE_PATH)
assert SPEC is not None
delay_barrier = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(delay_barrier)


def _write_json(path: Path, data: dict) -> Path:
    path.write_text(json.dumps(data))
    return path


def _decision_row(
    ts: float,
    *,
    min_cpa: float = 10.0,
    min_ttc: float = 1_000_000_000.0,
    fired: bool = False,
) -> dict:
    return {
        "ts": ts,
        "frame_index": int(ts * 4),
        "fired": fired,
        "brake": fired,
        "release": False,
        "min_ttc": min_ttc,
        "min_cpa": min_cpa,
        "params": {
            "ttc_thresh": 2.5,
            "cpa_margin": 1.5,
            "dt": 0.5,
            "max_gap": 30.0,
            "min_closing": 3.0,
            "min_score": 0.3,
            "release_k": 4,
        },
        "objs": [{"id": 1}],
    }


def _episode(
    tmp_path: Path,
    audit_id: str,
    scenario: str,
    first_foreground_ts: float,
    first_fire_ts: float,
    rows: list[dict],
) -> dict:
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
        "first_fire_ts": first_fire_ts,
        "first_fire_channel": "ttc_only",
        "fired_frames": 1,
        "brake_frames": 1,
        "first_foreground_ts": first_foreground_ts,
        "foreground_count": 2,
        "monitor_frames": len(rows),
    }


def _reports(
    tmp_path: Path,
    *,
    iter73_verdict: str = "HUGSIM_MARGIN_TRANSITION_SPLIT_COMPLETE",
    same_channel: bool = False,
    preforeground_active: bool = False,
) -> tuple[Path, Path, Path, Path]:
    both_rows = [
        _decision_row(0.0),
        _decision_row(5.0, min_cpa=1.0 if preforeground_active else 2.0),
        _decision_row(7.0, min_cpa=1.0 if same_channel else 3.0, min_ttc=4.0 if same_channel else 2.0, fired=True),
    ]
    ttc_rows = [
        _decision_row(0.0),
        _decision_row(3.0, min_cpa=5.0, min_ttc=3.0),
        _decision_row(5.0, min_cpa=3.0 if same_channel else 1.0, min_ttc=2.0 if same_channel else 4.0, fired=True),
    ]
    iter59 = _write_json(
        tmp_path / "iter59.json",
        {
            "verdict": "ACTOR_MATCH_AUDIT_COMPLETE",
            "infra_problems": [],
            "episodes": [
                _episode(
                    tmp_path,
                    "both_distinct_extreme",
                    "scene-0138-extreme-00",
                    5.25,
                    7.0,
                    both_rows,
                ),
                _episode(tmp_path, "ttc_medium_a", "scene-0071-medium-01", 3.25, 5.0, ttc_rows),
            ],
        },
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
                    "problems": [],
                },
                {
                    "audit_id": "ttc_medium_a",
                    "scenario": "scene-0071-medium-01",
                    "structural_label": "foreground_present_late_fire",
                    "problems": [],
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
            "verdict": iter73_verdict,
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
    return iter59, iter70, iter72, iter73


def test_late_fire_cross_channel_delay_complete(tmp_path: Path) -> None:
    report = delay_barrier.build_report(*_reports(tmp_path))
    labels = {row["audit_id"]: row["row_label"] for row in report["episodes"]}
    timelines = {row["audit_id"]: row["timeline"] for row in report["episodes"]}

    assert report["verdict"] == "HUGSIM_LATE_FIRE_CROSS_CHANNEL_DELAY_COMPLETE"
    assert labels["both_distinct_extreme"] == "cross_channel_late_activation"
    assert labels["ttc_medium_a"] == "cross_channel_late_activation"
    assert timelines["both_distinct_extreme"]["pre_foreground_near_channels"] == ["cpa"]
    assert timelines["both_distinct_extreme"]["first_active_channels"] == ["ttc"]
    assert timelines["ttc_medium_a"]["pre_foreground_near_channels"] == ["ttc"]
    assert timelines["ttc_medium_a"]["first_active_channels"] == ["cpa"]


def test_late_fire_delay_mixed_when_same_channel(tmp_path: Path) -> None:
    report = delay_barrier.build_report(*_reports(tmp_path, same_channel=True))
    labels = {row["audit_id"]: row["row_label"] for row in report["episodes"]}

    assert report["verdict"] == "HUGSIM_LATE_FIRE_DELAY_MIXED_COMPLETE"
    assert labels["both_distinct_extreme"] == "same_channel_late_activation"
    assert labels["ttc_medium_a"] == "same_channel_late_activation"


def test_late_fire_delay_blocks_bad_source_verdict(tmp_path: Path) -> None:
    report = delay_barrier.build_report(*_reports(tmp_path, iter73_verdict="WRONG"))

    assert report["verdict"] == "HUGSIM_LATE_FIRE_DELAY_BLOCKED"
    assert report["episodes"] == []
    assert "iter73-verdict-not-HUGSIM_MARGIN_TRANSITION_SPLIT_COMPLETE" in report["infra_problems"]


def test_late_fire_delay_blocks_preforeground_active(tmp_path: Path) -> None:
    report = delay_barrier.build_report(*_reports(tmp_path, preforeground_active=True))
    labels = {row["audit_id"]: row["row_label"] for row in report["episodes"]}

    assert report["verdict"] == "HUGSIM_LATE_FIRE_DELAY_BLOCKED"
    assert labels["both_distinct_extreme"] == "preforeground_active_inconsistent"
