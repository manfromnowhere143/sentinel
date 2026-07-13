from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter70_hugsim_structural_timing_audit"
    / "analyze_structural_timing.py"
)
SPEC = importlib.util.spec_from_file_location("iter70_structural_timing", MODULE_PATH)
assert SPEC is not None
structural = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(structural)


def _write_json(path: Path, data: dict) -> Path:
    path.write_text(json.dumps(data))
    return path


def _decision_row(ts: float, *, fired: bool = False, brake: bool = False, channel: str = "no_fire") -> dict:
    params = {
        "ttc_thresh": 2.5,
        "cpa_margin": 1.5,
        "dt": 0.5,
        "max_gap": 30.0,
        "min_closing": 3.0,
        "min_score": 0.3,
        "release_k": 4,
    }
    min_ttc = 1.0 if channel == "ttc_only" else 1_000_000_000.0
    min_cpa = 1.0 if channel == "cpa_only" else 10.0
    if channel == "both":
        min_ttc = 1.0
        min_cpa = 1.0
    return {
        "frame_index": int(ts * 4),
        "ts": ts,
        "fired": fired,
        "brake": brake,
        "release": False,
        "min_ttc": min_ttc,
        "min_cpa": min_cpa,
        "params": params,
        "objs": [{"id": 1}] if ts > 0 else [],
    }


def _write_decisions(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n")


def _episode(
    tmp_path: Path,
    audit_id: str,
    scenario: str,
    support_label: str,
    *,
    first_foreground_ts: float | None,
    first_fire_ts: float | None,
    first_fire_channel: str,
    fired_frames: int,
    brake_frames: int,
    foreground_count: int,
    rows: list[dict],
) -> dict:
    episode_dir = tmp_path / f"{audit_id}__{scenario}__on"
    _write_decisions(episode_dir / "sentinel_iter48_decisions.jsonl", rows)
    return {
        "audit_id": audit_id,
        "scenario": scenario,
        "support_label": support_label,
        "episode_dir": str(episode_dir),
        "first_fire_ts": first_fire_ts,
        "first_fire_channel": first_fire_channel,
        "fired_frames": fired_frames,
        "brake_frames": brake_frames,
        "first_foreground_ts": first_foreground_ts,
        "foreground_count": foreground_count,
        "monitor_frames": len(rows),
        "monitor_object_id": None if first_fire_ts is None else 1,
        "monitor_provenance_label": "no_fire" if first_fire_ts is None else "unique_ttc_object",
    }


def _reports(tmp_path: Path, *, iter59_verdict: str = "ACTOR_MATCH_AUDIT_COMPLETE", mismatch: bool = False) -> tuple[Path, Path]:
    episodes = [
        _episode(
            tmp_path,
            "mixed_extreme",
            "scene-0062-extreme-00",
            "no_monitor_fire",
            first_foreground_ts=4.75,
            first_fire_ts=None,
            first_fire_channel="no_fire",
            fired_frames=0,
            brake_frames=0,
            foreground_count=2,
            rows=[_decision_row(0.0), _decision_row(0.25), _decision_row(0.5)],
        ),
        _episode(
            tmp_path,
            "both_distinct_extreme",
            "scene-0138-extreme-00",
            "post_collision_fire",
            first_foreground_ts=5.25,
            first_fire_ts=7.0,
            first_fire_channel="ttc_only",
            fired_frames=1 if mismatch else 2,
            brake_frames=2,
            foreground_count=10,
            rows=[
                _decision_row(0.0),
                _decision_row(5.0),
                _decision_row(7.0, fired=True, brake=True, channel="ttc_only"),
                _decision_row(7.25, fired=True, brake=True, channel="ttc_only"),
            ],
        ),
        _episode(
            tmp_path,
            "nofire_hard_control",
            "scene-0041-hard-00",
            "no_monitor_fire",
            first_foreground_ts=2.5,
            first_fire_ts=None,
            first_fire_channel="no_fire",
            fired_frames=0,
            brake_frames=0,
            foreground_count=9,
            rows=[_decision_row(0.0), _decision_row(1.0), _decision_row(2.0)],
        ),
        _episode(
            tmp_path,
            "cpa_medium_a",
            "scene-0071-medium-00",
            "background_collision_only",
            first_foreground_ts=None,
            first_fire_ts=3.5,
            first_fire_channel="ttc_only",
            fired_frames=1,
            brake_frames=1,
            foreground_count=0,
            rows=[_decision_row(0.0), _decision_row(3.5, fired=True, brake=True, channel="ttc_only")],
        ),
        _episode(
            tmp_path,
            "ttc_medium_a",
            "scene-0071-medium-01",
            "post_collision_fire",
            first_foreground_ts=3.25,
            first_fire_ts=5.0,
            first_fire_channel="cpa_only",
            fired_frames=1,
            brake_frames=1,
            foreground_count=10,
            rows=[_decision_row(0.0), _decision_row(3.0), _decision_row(5.0, fired=True, brake=True, channel="cpa_only")],
        ),
    ]
    iter59 = _write_json(
        tmp_path / "iter59.json",
        {
            "verdict": iter59_verdict,
            "infra_problems": [],
            "episodes": episodes,
        },
    )
    iter69_rows = [
        {
            "audit_id": audit_id,
            "scenario": scenario,
            "iter59_support_label": label,
            "mechanism_label": label,
        }
        for audit_id, scenario, label in structural.FIXED_STRUCTURAL_ROWS
    ]
    iter69 = _write_json(
        tmp_path / "iter69.json",
        {
            "verdict": "HUGSIM_MECHANISM_TAXONOMY_COMPLETE",
            "infra_problems": [],
            "episodes": iter69_rows,
        },
    )
    return iter59, iter69


def test_structural_timing_taxonomy_complete(tmp_path: Path) -> None:
    report = structural.build_report(*_reports(tmp_path))
    labels = {row["audit_id"]: row["structural_label"] for row in report["episodes"]}

    assert report["verdict"] == "HUGSIM_STRUCTURAL_TIMING_TAXONOMY_COMPLETE"
    assert report["summary"]["target_rows"] == 5
    assert report["summary"]["evaluated_rows"] == 5
    assert report["summary"]["structural_label_counts"] == {
        "foreground_absent_background_only": 1,
        "foreground_present_late_fire": 2,
        "foreground_present_surface_silent": 2,
    }
    assert labels["mixed_extreme"] == "foreground_present_surface_silent"
    assert labels["both_distinct_extreme"] == "foreground_present_late_fire"
    assert labels["cpa_medium_a"] == "foreground_absent_background_only"


def test_structural_timing_blocks_on_bad_source_verdict(tmp_path: Path) -> None:
    report = structural.build_report(*_reports(tmp_path, iter59_verdict="WRONG"))

    assert report["verdict"] == "HUGSIM_STRUCTURAL_TIMING_TAXONOMY_BLOCKED"
    assert report["episodes"] == []
    assert "iter59-verdict-not-ACTOR_MATCH_AUDIT_COMPLETE" in report["infra_problems"]


def test_structural_timing_blocks_on_report_log_mismatch(tmp_path: Path) -> None:
    report = structural.build_report(*_reports(tmp_path, mismatch=True))
    row = next(row for row in report["episodes"] if row["audit_id"] == "both_distinct_extreme")

    assert report["verdict"] == "HUGSIM_STRUCTURAL_TIMING_TAXONOMY_BLOCKED"
    assert "fired_frames-mismatch:1!=2" in row["problems"]
