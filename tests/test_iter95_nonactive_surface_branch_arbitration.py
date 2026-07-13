from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter95_hugsim_nonactive_surface_branch_arbitration"
    / "analyze_nonactive_surface_branch_arbitration.py"
)
SPEC = importlib.util.spec_from_file_location("iter95_nonactive_branch", MODULE_PATH)
assert SPEC is not None
branch = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(branch)


def _candidate(
    object_id: int,
    state: str,
    band: str,
    bridge_distance: float,
    min_cpa: float,
    cpa_rank: int,
    active_margin: float,
    *,
    ttc: float | None = None,
    active_ttc_margin: float | None = None,
) -> dict:
    return {
        "object_id": object_id,
        "state": state,
        "joint_class": f"{state}_{band}",
        "bridge_geometry": {"distance_band": band, "best_distance_m": bridge_distance},
        "min_cpa": min_cpa,
        "cpa_rank": cpa_rank,
        "ttc": ttc,
        "ttc_rank": 1 if ttc is not None else None,
        "active_cpa_margin_m": active_margin,
        "active_ttc_margin_s": active_ttc_margin,
    }


def _row_base(target: dict, label: str) -> dict:
    return {
        "audit_id": target["audit_id"],
        "scenario": target["scenario"],
        "event_role": target["event_role"],
        "replay_alignment": target["replay_alignment"],
        "replay_ts": target["replay_ts"],
        "row_label": label,
        "problems": [],
    }


def _reports(
    tmp_path: Path,
    *,
    iter94_verdict: str = branch.ITER94_VERDICT,
    remove_provenance_ttc: bool = False,
) -> tuple[Path, Path, Path]:
    target0, target1 = branch.FIXED_ROWS
    path5 = _candidate(5, "subthreshold", "no_support", 9.0, 6.4, 1, 4.9)
    prov9 = _candidate(
        9,
        "borderline",
        "match",
        1.0,
        21.5,
        2,
        20.0,
        ttc=None if remove_provenance_ttc else 4.7,
        active_ttc_margin=None if remove_provenance_ttc else 2.2,
    )
    path19 = _candidate(19, "subthreshold", "ambiguous", 3.2, 6.3, 1, 4.8)
    prov3 = _candidate(3, "subthreshold", "match", 0.7, 17.4, 5, 15.9)

    row92_a = _row_base(target0, target0["iter92_label"])
    row92_a.update({"path_best": path5, "provenance_best": prov9, "surface_best": prov9})
    row92_b = _row_base(target1, target1["iter92_label"])
    row92_b.update({"path_best": path19, "provenance_best": prov3, "surface_best": path19})

    row93_a = _row_base(target0, target0["iter93_label"])
    row93_a.update(
        {
            "path_best": branch.compact_candidate(path5),
            "provenance_best": branch.compact_candidate(prov9),
            "surface_best": branch.compact_candidate(prov9),
            "surface_matches_path": False,
            "surface_matches_provenance": True,
        }
    )
    row93_b = _row_base(target1, target1["iter93_label"])
    row93_b.update(
        {
            "path_best": branch.compact_candidate(path19),
            "provenance_best": branch.compact_candidate(prov3),
            "surface_best": branch.compact_candidate(path19),
            "surface_matches_path": True,
            "surface_matches_provenance": False,
        }
    )

    iter92_path = tmp_path / "iter92.json"
    iter93_path = tmp_path / "iter93.json"
    iter94_path = tmp_path / "iter94.json"
    iter92_path.write_text(
        json.dumps({"verdict": branch.ITER92_VERDICT, "infra_problems": [], "events": [row92_a, row92_b]})
    )
    iter93_path.write_text(
        json.dumps({"verdict": branch.ITER93_VERDICT, "infra_problems": [], "events": [row93_a, row93_b]})
    )
    iter94_path.write_text(json.dumps({"verdict": iter94_verdict, "infra_problems": [], "events": []}))
    return iter92_path, iter93_path, iter94_path


def test_nonactive_surface_branch_split_complete(tmp_path: Path) -> None:
    report = branch.build_report(*_reports(tmp_path))
    labels = {(row["audit_id"], row["event_role"]): row["row_label"] for row in report["events"]}

    assert report["verdict"] == "HUGSIM_NONACTIVE_SURFACE_BRANCH_ARBITRATION_SPLIT_COMPLETE"
    assert labels[("both_distinct_extreme", "pre")] == "nonactive_surface_provenance_ttc_borderline_over_path_cpa"
    assert labels[("ttc_medium_a", "pre")] == "nonactive_surface_path_cpa_over_provenance_bridge"
    assert report["summary"]["surface_matches_path_events"] == 1
    assert report["summary"]["surface_matches_provenance_events"] == 1
    assert report["summary"]["provenance_finite_ttc_events"] == 1


def test_nonactive_surface_branch_mixed_other_when_ttc_removed(tmp_path: Path) -> None:
    report = branch.build_report(*_reports(tmp_path, remove_provenance_ttc=True))

    assert report["verdict"] == "HUGSIM_NONACTIVE_SURFACE_BRANCH_MIXED_OTHER_COMPLETE"
    assert report["summary"]["row_label_counts"]["nonactive_surface_branch_mixed_other"] == 1
    assert report["summary"]["row_label_counts"]["nonactive_surface_path_cpa_over_provenance_bridge"] == 1


def test_nonactive_surface_branch_blocks_bad_iter94_verdict(tmp_path: Path) -> None:
    report = branch.build_report(*_reports(tmp_path, iter94_verdict="WRONG"))

    assert report["verdict"] == "HUGSIM_NONACTIVE_SURFACE_BRANCH_BLOCKED"
    assert report["events"] == []
    assert "iter94-verdict-not-HUGSIM_ACTIVE_ROW_SURFACE_MARGIN_ARBITRATION_COMPLETE" in report["infra_problems"]
