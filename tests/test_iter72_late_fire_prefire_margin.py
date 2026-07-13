from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter72_hugsim_late_fire_prefire_margin_audit"
    / "analyze_late_fire_prefire_margin.py"
)
SPEC = importlib.util.spec_from_file_location("iter72_late_fire_prefire_margin", MODULE_PATH)
assert SPEC is not None
prefire = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(prefire)


def _write_json(path: Path, data: dict) -> Path:
    path.write_text(json.dumps(data))
    return path


def _decision_row(ts: float, min_cpa: float, min_ttc: float = 1_000_000_000.0, *, fired: bool = False) -> dict:
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
    iter59_verdict: str = "ACTOR_MATCH_AUDIT_COMPLETE",
    active_crossing: bool = False,
) -> tuple[Path, Path]:
    cpa = 1.0 if active_crossing else 2.0
    iter59_rows = [
        _episode(
            tmp_path,
            "both_distinct_extreme",
            "scene-0138-extreme-00",
            5.25,
            7.0,
            [_decision_row(0.0, 10.0), _decision_row(5.0, cpa), _decision_row(7.0, 0.5, fired=True)],
        ),
        _episode(
            tmp_path,
            "ttc_medium_a",
            "scene-0071-medium-01",
            3.25,
            5.0,
            [_decision_row(0.0, 10.0), _decision_row(3.0, 7.0), _decision_row(5.0, 0.5, fired=True)],
        ),
    ]
    iter59 = _write_json(
        tmp_path / "iter59.json",
        {
            "verdict": iter59_verdict,
            "infra_problems": [],
            "episodes": iter59_rows,
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
                    "report": {"first_foreground_ts": 5.25, "first_fire_ts": 7.0},
                    "problems": [],
                },
                {
                    "audit_id": "ttc_medium_a",
                    "scenario": "scene-0071-medium-01",
                    "structural_label": "foreground_present_late_fire",
                    "report": {"first_foreground_ts": 3.25, "first_fire_ts": 5.0},
                    "problems": [],
                },
            ],
        },
    )
    return iter59, iter70


def test_late_fire_prefire_margin_complete(tmp_path: Path) -> None:
    report = prefire.build_report(*_reports(tmp_path))
    labels = {row["audit_id"]: row["row_label"] for row in report["episodes"]}

    assert report["verdict"] == "HUGSIM_LATE_FIRE_PREFIRE_MARGIN_COMPLETE"
    assert labels["both_distinct_extreme"] == "late_fire_prefire_near_cpa_margin"
    assert labels["ttc_medium_a"] == "late_fire_prefire_far_margin"


def test_late_fire_prefire_active_crossing_blocks(tmp_path: Path) -> None:
    report = prefire.build_report(*_reports(tmp_path, active_crossing=True))
    labels = {row["audit_id"]: row["row_label"] for row in report["episodes"]}

    assert report["verdict"] == "HUGSIM_LATE_FIRE_PREFIRE_ACTIVE_INCONSISTENT_BLOCKED"
    assert labels["both_distinct_extreme"] == "late_fire_prefire_active_crossing_inconsistent"


def test_late_fire_prefire_blocks_bad_source_verdict(tmp_path: Path) -> None:
    report = prefire.build_report(*_reports(tmp_path, iter59_verdict="WRONG"))

    assert report["verdict"] == "HUGSIM_LATE_FIRE_PREFIRE_MARGIN_BLOCKED"
    assert report["episodes"] == []
    assert "iter59-verdict-not-ACTOR_MATCH_AUDIT_COMPLETE" in report["infra_problems"]
