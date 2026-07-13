from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter69_hugsim_mechanism_taxonomy"
    / "analyze_mechanism_taxonomy.py"
)
SPEC = importlib.util.spec_from_file_location("iter69_mechanism_taxonomy", MODULE_PATH)
assert SPEC is not None
taxonomy = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(taxonomy)


def _write_json(path: Path, data: dict) -> Path:
    path.write_text(json.dumps(data))
    return path


def _iter59_rows() -> list[dict]:
    rows = []
    for row in taxonomy.EXPECTED_ITER59_ROWS:
        rows.append({
            **row,
            "first_fire_channel": "ttc_only",
            "first_fire_ts": 1.0,
            "monitor_object_id": 1,
        })
    return rows


def _write_reports(
    tmp_path: Path,
    *,
    iter59_verdict: str = "ACTOR_MATCH_AUDIT_COMPLETE",
    cpa_iter68_label: str = "fire_gap_best_after_fire",
) -> tuple[Path, Path, Path, Path, Path, Path, Path, Path]:
    iter59 = _write_json(
        tmp_path / "iter59.json",
        {
            "verdict": iter59_verdict,
            "infra_problems": [],
            "episodes": _iter59_rows(),
        },
    )
    iter61 = _write_json(
        tmp_path / "iter61.json",
        {
            "verdict": "OBJECT_SURFACE_NONTRIGGER_MATCH_COMPLETE",
            "infra_problems": [],
            "episodes": [
                {
                    "audit_id": "ttc_extreme_short",
                    "scenario": "scene-0038-extreme-00",
                    "row_label": "no_monitor_object_support",
                    "trigger_object_id": 2,
                },
                {
                    "audit_id": "cpa_medium_b",
                    "scenario": "scene-0166-medium-00",
                    "row_label": "no_monitor_object_support",
                    "trigger_object_id": 1,
                },
                {
                    "audit_id": "ttc_extreme_b",
                    "scenario": "scene-0383-extreme-00",
                    "row_label": "nontrigger_object_match",
                    "trigger_object_id": 1,
                    "best_nontrigger_variant": {"object_id": 16, "distance_m": 2.0},
                },
            ],
        },
    )
    iter63 = _write_json(
        tmp_path / "iter63.json",
        {
            "verdict": "TEMPORAL_VISIBLE_NEVER_HAZARD_COMPLETE",
            "infra_problems": [],
            "row_problems": [],
            "target": {
                "audit_id": "ttc_extreme_b",
                "scenario": "scene-0383-extreme-00",
                "object_id": 16,
                "trigger_object_id": 1,
            },
            "summary": {"row_label": "visible_never_hazard"},
        },
    )
    iter64 = _write_json(
        tmp_path / "iter64.json",
        {
            "verdict": "UNSUPPORTED_TEMPORAL_MATCH_COMPLETE",
            "infra_problems": [],
            "episodes": [
                {
                    "audit_id": "ttc_extreme_short",
                    "scenario": "scene-0038-extreme-00",
                    "row_label": "pre_contact_object_match",
                },
                {
                    "audit_id": "cpa_medium_b",
                    "scenario": "scene-0166-medium-00",
                    "row_label": "pre_contact_object_match",
                },
            ],
        },
    )
    iter65 = _write_json(
        tmp_path / "iter65.json",
        {
            "verdict": "TEMPORAL_ALIGNMENT_SUBTHRESHOLD_COMPLETE",
            "infra_problems": [],
            "episodes": [
                {
                    "audit_id": "ttc_extreme_short",
                    "scenario": "scene-0038-extreme-00",
                    "row_label": "matched_object_subthreshold",
                    "matched_object_id": 2,
                },
                {
                    "audit_id": "cpa_medium_b",
                    "scenario": "scene-0166-medium-00",
                    "row_label": "matched_object_subthreshold",
                    "matched_object_id": 6,
                },
            ],
        },
    )
    iter66 = _write_json(
        tmp_path / "iter66.json",
        {
            "verdict": "MATCHED_OBJECT_TIMELINE_MIXED_COMPLETE",
            "infra_problems": [],
            "episodes": [
                {
                    "audit_id": "ttc_extreme_short",
                    "scenario": "scene-0038-extreme-00",
                    "row_label": "target_object_ever_active_hazard",
                    "target_object_id": 2,
                },
                {
                    "audit_id": "cpa_medium_b",
                    "scenario": "scene-0166-medium-00",
                    "row_label": "target_object_visible_never_active",
                    "target_object_id": 6,
                },
            ],
        },
    )
    iter67 = _write_json(
        tmp_path / "iter67.json",
        {
            "verdict": "TRIGGER_TARGET_SAME_AND_SPLIT_COMPLETE",
            "infra_problems": [],
            "episodes": [
                {
                    "audit_id": "ttc_extreme_short",
                    "scenario": "scene-0038-extreme-00",
                    "row_label": "same_object_target_trigger_match",
                    "target_object_id": 2,
                    "trigger_object_id": 2,
                },
                {
                    "audit_id": "cpa_medium_b",
                    "scenario": "scene-0166-medium-00",
                    "row_label": "split_target_match_trigger_match",
                    "target_object_id": 6,
                    "trigger_object_id": 1,
                },
            ],
        },
    )
    iter68 = _write_json(
        tmp_path / "iter68.json",
        {
            "verdict": "FIRE_TIME_BRIDGE_GAP_TEMPORAL_SPLIT_COMPLETE",
            "infra_problems": [],
            "episodes": [
                {
                    "audit_id": "ttc_extreme_short",
                    "scenario": "scene-0038-extreme-00",
                    "row_label": "fire_gap_best_before_fire",
                    "trigger_object_id": 2,
                    "first_fire_ts": 1.5,
                },
                {
                    "audit_id": "cpa_medium_b",
                    "scenario": "scene-0166-medium-00",
                    "row_label": cpa_iter68_label,
                    "trigger_object_id": 1,
                    "first_fire_ts": 0.25,
                },
            ],
        },
    )
    return iter59, iter61, iter63, iter64, iter65, iter66, iter67, iter68


def test_mechanism_taxonomy_complete(tmp_path: Path) -> None:
    report = taxonomy.build_report(*_write_reports(tmp_path))
    labels = {row["audit_id"]: row["mechanism_label"] for row in report["episodes"]}

    assert report["verdict"] == "HUGSIM_MECHANISM_TAXONOMY_COMPLETE"
    assert report["summary"]["total_rows"] == 8
    assert report["summary"]["refined_classifiable_rows"] == 3
    assert labels["ttc_extreme_short"] == "same_object_late_fire_after_best_bridge"
    assert labels["cpa_medium_b"] == "split_object_visible_never_active_fire_before_best_bridge"
    assert labels["ttc_extreme_b"] == "nontrigger_visible_never_hazard"
    assert labels["mixed_extreme"] == "no_monitor_fire"
    assert labels["cpa_medium_a"] == "background_collision_only"


def test_mechanism_taxonomy_partial_when_downstream_label_unmet(tmp_path: Path) -> None:
    report = taxonomy.build_report(
        *_write_reports(tmp_path, cpa_iter68_label="fire_gap_best_before_fire")
    )
    labels = {row["audit_id"]: row["mechanism_label"] for row in report["episodes"]}
    cpa_row = next(row for row in report["episodes"] if row["audit_id"] == "cpa_medium_b")

    assert report["verdict"] == "HUGSIM_MECHANISM_TAXONOMY_PARTIAL"
    assert report["summary"]["refined_classifiable_rows"] == 2
    assert labels["cpa_medium_b"] == "classifiable_actor_mismatch_unrefined"
    assert "iter68:fire_gap_best_after_fire!=fire_gap_best_before_fire" in cpa_row[
        "unmet_refinement_evidence"
    ]


def test_mechanism_taxonomy_blocked_on_bad_source_verdict(tmp_path: Path) -> None:
    report = taxonomy.build_report(*_write_reports(tmp_path, iter59_verdict="WRONG"))

    assert report["verdict"] == "HUGSIM_MECHANISM_TAXONOMY_BLOCKED"
    assert report["episodes"] == []
    assert "iter59-verdict-not-ACTOR_MATCH_AUDIT_COMPLETE" in report["infra_problems"]
