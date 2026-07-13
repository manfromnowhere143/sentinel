from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter62_nontrigger_ranking_audit"
    / "analyze_nontrigger_ranking.py"
)
SPEC = importlib.util.spec_from_file_location("iter62_nontrigger_ranking", MODULE_PATH)
assert SPEC is not None
ranking = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ranking)


def _decision_row(matched_y: float) -> dict:
    return {
        "frame_index": 0,
        "ts": 0.0,
        "fired": True,
        "brake": True,
        "min_ttc": 1_000_000_000.0,
        "min_cpa": 0.0,
        "l2g_r_mat": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        "l2g_t": [0.0, 0.0, 0.0],
        "params": {"dt": 1.0, "min_closing": 0.1},
        "traj": [[0.0, 10.0]],
        "objs": [
            {"id": 1, "score": 0.9, "world": [0.0, 10.0], "vel": [0.0, 0.0]},
            {"id": 16, "score": 0.8, "world": [0.0, matched_y], "vel": [0.0, 0.0]},
            {"id": 3, "score": 0.7, "world": [20.0, 20.0], "vel": [0.0, 0.0]},
        ],
    }


def _proof_and_reports(tmp_path: Path, matched_y: float) -> tuple[Path, Path, Path]:
    proof_root = tmp_path / "proof"
    ep = proof_root / "episodes" / f"{ranking.TARGET_AUDIT_ID}__{ranking.TARGET_SCENARIO}__on"
    ep.mkdir(parents=True)
    (ep / "sentinel_iter48_decisions.jsonl").write_text(json.dumps(_decision_row(matched_y)) + "\n")
    iter59_report = tmp_path / "iter59_report.json"
    iter59_report.write_text(json.dumps({"verdict": "ACTOR_MATCH_AUDIT_COMPLETE", "episodes": []}))
    iter61_report = tmp_path / "iter61_report.json"
    iter61_report.write_text(json.dumps({
        "verdict": "OBJECT_SURFACE_NONTRIGGER_MATCH_COMPLETE",
        "episodes": [
            {
                "audit_id": ranking.TARGET_AUDIT_ID,
                "scenario": ranking.TARGET_SCENARIO,
                "row_label": "nontrigger_object_match",
                "best_nontrigger_variant": {"object_id": ranking.TARGET_MATCHED_OBJECT_ID},
            }
        ],
    }))
    return proof_root, iter59_report, iter61_report


def test_nontrigger_ranking_hazard_present_when_cpa_crosses(tmp_path: Path) -> None:
    proof_root, iter59_report, iter61_report = _proof_and_reports(tmp_path, matched_y=10.5)

    report = ranking.build_report(proof_root, iter59_report, iter61_report)

    assert report["verdict"] == "MATCHED_OBJECT_HAZARD_PRESENT_COMPLETE"
    assert report["matched_object_label"] == "matched_object_hazard_present"
    assert report["matched_object"]["min_cpa"] == 0.5
    assert report["matched_object"]["cpa_rank"] == 2


def test_nontrigger_ranking_borderline_when_inside_borderline_band(tmp_path: Path) -> None:
    proof_root, iter59_report, iter61_report = _proof_and_reports(tmp_path, matched_y=12.0)

    report = ranking.build_report(proof_root, iter59_report, iter61_report)

    assert report["verdict"] == "MATCHED_OBJECT_BORDERLINE_NULL"
    assert report["matched_object_label"] == "matched_object_borderline"
    assert report["matched_object"]["min_cpa"] == 2.0


def test_nontrigger_ranking_subthreshold_when_far_from_thresholds(tmp_path: Path) -> None:
    proof_root, iter59_report, iter61_report = _proof_and_reports(tmp_path, matched_y=20.0)

    report = ranking.build_report(proof_root, iter59_report, iter61_report)

    assert report["verdict"] == "MATCHED_OBJECT_SUBTHRESHOLD_COMPLETE"
    assert report["matched_object_label"] == "matched_object_subthreshold"
    assert report["matched_object"]["ttc"] is None


def test_nontrigger_ranking_infra_null_when_iter61_crosscheck_fails(tmp_path: Path) -> None:
    proof_root, iter59_report, iter61_report = _proof_and_reports(tmp_path, matched_y=20.0)
    iter61_report.write_text(json.dumps({"verdict": "WRONG", "episodes": []}))

    report = ranking.build_report(proof_root, iter59_report, iter61_report)

    assert report["verdict"] == "NONTRIGGER_RANKING_INFRA_NULL"
    assert "iter61-verdict-not-OBJECT_SURFACE_NONTRIGGER_MATCH_COMPLETE" in report["infra_problems"]
