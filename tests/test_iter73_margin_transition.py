from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter73_hugsim_margin_transition_audit"
    / "analyze_margin_transition.py"
)
SPEC = importlib.util.spec_from_file_location("iter73_margin_transition", MODULE_PATH)
assert SPEC is not None
transition = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(transition)


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
    support_label: str,
    first_foreground_ts: float,
    first_fire_ts: float | None,
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
        "support_label": support_label,
        "episode_dir": str(episode_dir),
        "first_fire_ts": first_fire_ts,
        "first_fire_channel": "no_fire" if first_fire_ts is None else "ttc_only",
        "fired_frames": 0 if first_fire_ts is None else 1,
        "brake_frames": 0 if first_fire_ts is None else 1,
        "first_foreground_ts": first_foreground_ts,
        "foreground_count": 2,
        "monitor_frames": len(rows),
    }


def _reports(
    tmp_path: Path,
    *,
    iter59_verdict: str = "ACTOR_MATCH_AUDIT_COMPLETE",
    mixed: bool = False,
) -> tuple[Path, Path, Path, Path]:
    silent_active_row = [_decision_row(0.0, 10.0), _decision_row(5.0, 1.0)] if mixed else [
        _decision_row(0.0, 10.0),
        _decision_row(5.0, 8.0),
    ]
    iter59_rows = [
        _episode(
            tmp_path,
            "mixed_extreme",
            "scene-0062-extreme-00",
            "no_monitor_fire",
            4.75,
            None,
            silent_active_row,
        ),
        _episode(
            tmp_path,
            "nofire_hard_control",
            "scene-0041-hard-00",
            "no_monitor_fire",
            2.5,
            None,
            [_decision_row(0.0, 10.0), _decision_row(3.0, 8.0)],
        ),
        _episode(
            tmp_path,
            "both_distinct_extreme",
            "scene-0138-extreme-00",
            "post_collision_fire",
            5.25,
            7.0,
            [_decision_row(0.0, 10.0), _decision_row(5.0, 2.0), _decision_row(7.0, 1.0, fired=True)],
        ),
        _episode(
            tmp_path,
            "ttc_medium_a",
            "scene-0071-medium-01",
            "post_collision_fire",
            3.25,
            5.0,
            [_decision_row(0.0, 10.0), _decision_row(3.0, 5.0, 3.0), _decision_row(5.0, 1.0, fired=True)],
        ),
    ]
    iter59 = _write_json(
        tmp_path / "iter59.json",
        {"verdict": iter59_verdict, "infra_problems": [], "episodes": iter59_rows},
    )
    iter70 = _write_json(
        tmp_path / "iter70.json",
        {
            "verdict": "HUGSIM_STRUCTURAL_TIMING_TAXONOMY_COMPLETE",
            "infra_problems": [],
            "episodes": [
                {
                    "audit_id": "mixed_extreme",
                    "scenario": "scene-0062-extreme-00",
                    "structural_label": "foreground_present_surface_silent",
                    "problems": [],
                },
                {
                    "audit_id": "nofire_hard_control",
                    "scenario": "scene-0041-hard-00",
                    "structural_label": "foreground_present_surface_silent",
                    "problems": [],
                },
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
    iter71 = _write_json(
        tmp_path / "iter71.json",
        {
            "verdict": "HUGSIM_SURFACE_SILENT_MARGIN_COMPLETE",
            "infra_problems": [],
            "episodes": [
                {"audit_id": "mixed_extreme", "scenario": "scene-0062-extreme-00", "row_label": "surface_silent_far_margin"},
                {
                    "audit_id": "nofire_hard_control",
                    "scenario": "scene-0041-hard-00",
                    "row_label": "surface_silent_far_margin",
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
    return iter59, iter70, iter71, iter72


def test_margin_transition_split_complete(tmp_path: Path) -> None:
    report = transition.build_report(*_reports(tmp_path))
    labels = {row["audit_id"]: row["row_label"] for row in report["episodes"]}

    assert report["verdict"] == "HUGSIM_MARGIN_TRANSITION_SPLIT_COMPLETE"
    assert labels["mixed_extreme"] == "silent_far_never_active"
    assert labels["nofire_hard_control"] == "silent_far_never_active"
    assert labels["both_distinct_extreme"] == "late_prefire_near_postcontact_active"
    assert labels["ttc_medium_a"] == "late_prefire_near_postcontact_active"


def test_margin_transition_mixed_complete_when_silent_activates_after_contact(tmp_path: Path) -> None:
    report = transition.build_report(*_reports(tmp_path, mixed=True))
    labels = {row["audit_id"]: row["row_label"] for row in report["episodes"]}

    assert report["verdict"] == "HUGSIM_MARGIN_TRANSITION_MIXED_COMPLETE"
    assert labels["mixed_extreme"] == "silent_active_after_contact_inconsistent"


def test_margin_transition_blocks_bad_source_verdict(tmp_path: Path) -> None:
    report = transition.build_report(*_reports(tmp_path, iter59_verdict="WRONG"))

    assert report["verdict"] == "HUGSIM_MARGIN_TRANSITION_BLOCKED"
    assert report["episodes"] == []
    assert "iter59-verdict-not-ACTOR_MATCH_AUDIT_COMPLETE" in report["infra_problems"]
