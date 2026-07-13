from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter94_hugsim_active_row_surface_margin_arbitration"
    / "analyze_active_row_surface_margin_arbitration.py"
)
SPEC = importlib.util.spec_from_file_location("iter94_active_margin", MODULE_PATH)
assert SPEC is not None
active_margin = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(active_margin)


def _candidate(
    object_id: int,
    state: str,
    band: str,
    min_cpa: float,
    cpa_rank: int,
    active_margin: float,
    *,
    ttc: float | None = None,
) -> dict:
    return {
        "object_id": object_id,
        "state": state,
        "joint_class": f"{state}_{band}",
        "bridge_geometry": {"distance_band": band, "best_distance_m": 4.0},
        "min_cpa": min_cpa,
        "cpa_rank": cpa_rank,
        "ttc": ttc,
        "ttc_rank": None,
        "active_cpa_margin_m": active_margin,
        "active_ttc_margin_s": None,
    }


def _row_base(label: str) -> dict:
    return {
        "audit_id": "ttc_medium_a",
        "scenario": "scene-0071-medium-01",
        "event_role": "active",
        "replay_alignment": "nearest_before_bridge_ts",
        "replay_ts": 5.75,
        "row_label": label,
        "problems": [],
    }


def _reports(tmp_path: Path, *, iter93_verdict: str = active_margin.ITER93_VERDICT, bridge_ttc: float | None = None) -> tuple[Path, Path, Path]:
    active = _candidate(24, "active", "no_support", 1.0, 1, -0.5)
    bridge6 = _candidate(6, "subthreshold", "ambiguous", 19.4, 5, 17.9, ttc=bridge_ttc)
    bridge10 = _candidate(10, "subthreshold", "ambiguous", 12.1, 3, 10.6)

    row91 = _row_base("path_active_provenance_far_with_bridge_nonactive")
    row91.update(
        {
            "active_object_count": 1,
            "bridge_supported_count": 2,
            "active_candidates": [active],
            "bridge_supported_candidates": [bridge6, bridge10],
        }
    )
    row92 = _row_base("path_best_active_no_bridge")
    row92.update(
        {
            "path_best": active,
            "provenance_best": bridge6,
            "surface_best": active,
        }
    )
    row93 = _row_base("surface_follows_path_active_no_bridge")
    row93.update(
        {
            "path_best": active_margin.compact_candidate(active),
            "provenance_best": active_margin.compact_candidate(bridge6),
            "surface_best": active_margin.compact_candidate(active),
            "surface_matches_path": True,
            "surface_matches_provenance": False,
        }
    )

    iter91_path = tmp_path / "iter91.json"
    iter92_path = tmp_path / "iter92.json"
    iter93_path = tmp_path / "iter93.json"
    iter91_path.write_text(json.dumps({"verdict": active_margin.ITER91_VERDICT, "infra_problems": [], "events": [row91]}))
    iter92_path.write_text(json.dumps({"verdict": active_margin.ITER92_VERDICT, "infra_problems": [], "events": [row92]}))
    iter93_path.write_text(json.dumps({"verdict": iter93_verdict, "infra_problems": [], "events": [row93]}))
    return iter91_path, iter92_path, iter93_path


def test_active_row_surface_margin_arbitration_complete(tmp_path: Path) -> None:
    report = active_margin.build_report(*_reports(tmp_path))
    row = report["events"][0]

    assert report["verdict"] == "HUGSIM_ACTIVE_ROW_SURFACE_MARGIN_ARBITRATION_COMPLETE"
    assert row["row_label"] == "active_row_cpa_margin_overrides_provenance"
    assert report["summary"]["active_object_id"] == 24
    assert report["summary"]["min_bridge_active_cpa_margin_m"] == 10.6
    assert report["summary"]["active_lower_cpa_than_all_bridge"] is True
    assert report["summary"]["active_better_cpa_rank_than_all_bridge"] is True


def test_active_row_surface_margin_detects_near_bridge_candidate(tmp_path: Path) -> None:
    report = active_margin.build_report(*_reports(tmp_path, bridge_ttc=2.0))

    assert report["verdict"] == "HUGSIM_ACTIVE_ROW_BRIDGE_CANDIDATE_SURFACE_NEAR_COMPLETE"
    assert report["events"][0]["row_label"] == "active_row_bridge_candidate_surface_near"
    assert report["summary"]["bridge_finite_ttc_count"] == 1


def test_active_row_surface_margin_blocks_bad_iter93_verdict(tmp_path: Path) -> None:
    report = active_margin.build_report(*_reports(tmp_path, iter93_verdict="WRONG"))

    assert report["verdict"] == "HUGSIM_ACTIVE_ROW_SURFACE_MARGIN_BLOCKED"
    assert report["events"] == []
    assert "iter93-verdict-not-HUGSIM_SURFACE_WINNER_ALIGNMENT_MIXED_COMPLETE" in report["infra_problems"]
