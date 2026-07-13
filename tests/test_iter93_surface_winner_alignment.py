from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter93_hugsim_surface_winner_alignment"
    / "analyze_surface_winner_alignment.py"
)
SPEC = importlib.util.spec_from_file_location("iter93_alignment", MODULE_PATH)
assert SPEC is not None
alignment = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(alignment)


def _candidate(object_id: int, state: str, band: str) -> dict:
    return {
        "object_id": object_id,
        "state": state,
        "joint_class": f"{state}_{band}",
        "min_cpa": 1.0,
        "cpa_rank": 1,
        "ttc": None,
        "ttc_rank": None,
        "bridge_geometry": {"distance_band": band, "best_distance_m": 1.0},
    }


def _event(
    audit_id: str,
    scenario: str,
    role: str,
    replay_ts: float,
    alignment_label: str,
    path: dict,
    provenance: dict,
    surface: dict,
    label: str,
) -> dict:
    return {
        "audit_id": audit_id,
        "scenario": scenario,
        "event_role": role,
        "replay_ts": replay_ts,
        "replay_alignment": alignment_label,
        "path_best": path,
        "provenance_best": provenance,
        "surface_best": surface,
        "path_provenance_same_object": False,
        "row_label": label,
        "problems": [],
    }


def _report(tmp_path: Path, *, verdict: str = "HUGSIM_PATH_PROXIMITY_ARBITRATION_SPLIT_COMPLETE") -> Path:
    path5 = _candidate(5, "subthreshold", "no_support")
    prov9 = _candidate(9, "borderline", "match")
    path19 = _candidate(19, "subthreshold", "ambiguous")
    prov3 = _candidate(3, "subthreshold", "match")
    path24 = _candidate(24, "active", "no_support")
    prov6 = _candidate(6, "subthreshold", "ambiguous")
    report = {
        "verdict": verdict,
        "infra_problems": [],
        "summary": {"path_provenance_same_object_events": 0},
        "events": [
            _event(
                "both_distinct_extreme",
                "scene-0138-extreme-00",
                "pre",
                5.5,
                "exact_bridge_ts",
                path5,
                prov9,
                prov9,
                "path_best_no_bridge_provenance_best_nonactive",
            ),
            _event(
                "ttc_medium_a",
                "scene-0071-medium-01",
                "pre",
                4.0,
                "exact_bridge_ts",
                path19,
                prov3,
                path19,
                "path_best_bridge_supported_nonactive",
            ),
            _event(
                "ttc_medium_a",
                "scene-0071-medium-01",
                "active",
                5.75,
                "nearest_before_bridge_ts",
                path24,
                prov6,
                path24,
                "path_best_active_no_bridge",
            ),
        ],
    }
    out = tmp_path / "iter92.json"
    out.write_text(json.dumps(report))
    return out


def test_surface_winner_alignment_mixed_complete(tmp_path: Path) -> None:
    report = alignment.build_report(_report(tmp_path))
    labels = {(row["audit_id"], row["event_role"]): row["row_label"] for row in report["events"]}

    assert report["verdict"] == "HUGSIM_SURFACE_WINNER_ALIGNMENT_MIXED_COMPLETE"
    assert labels[("both_distinct_extreme", "pre")] == "surface_follows_provenance_nonactive"
    assert labels[("ttc_medium_a", "pre")] == "surface_follows_path_nonactive"
    assert labels[("ttc_medium_a", "active")] == "surface_follows_path_active_no_bridge"
    assert report["summary"]["surface_matches_path_events"] == 2
    assert report["summary"]["surface_matches_provenance_events"] == 1
    assert report["summary"]["path_matches_provenance_events"] == 0


def test_surface_winner_alignment_blocks_bad_iter92_verdict(tmp_path: Path) -> None:
    report = alignment.build_report(_report(tmp_path, verdict="WRONG"))

    assert report["verdict"] == "HUGSIM_SURFACE_WINNER_ALIGNMENT_BLOCKED"
    assert report["events"] == []
    assert "iter92-verdict-not-HUGSIM_PATH_PROXIMITY_ARBITRATION_SPLIT_COMPLETE" in report["infra_problems"]
