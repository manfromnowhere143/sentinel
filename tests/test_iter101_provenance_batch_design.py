from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter101_hugsim_provenance_batch_candidate_design"
    / "analyze_provenance_batch_design.py"
)
SPEC = importlib.util.spec_from_file_location("iter101_design", MODULE_PATH)
assert SPEC is not None
design = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(design)


def _pair(dataset: str, label: str, idx: int, *, existing: bool = False) -> dict:
    prefix = "scene-existing" if existing else "scene-new"
    return {
        "dataset": dataset,
        "scenario": f"{prefix}-{dataset}-{label}-{idx:02d}",
        "run": idx,
        "tier": "easy" if dataset == "iter48_easy_medium" else "hard",
        "attackplanner": dataset == "iter49_hard_extreme",
        "monitor_provenance_label": label,
        "first_fire_channel": "no_fire" if label == "no_fire" else "ttc_only",
        "fire_timing_label": "no_fire" if label == "no_fire" else "post_collision_fire",
        "first_on_nc_time": 1.0,
        "first_fire_ts": None if label == "no_fire" else 2.0,
        "first_fire_lead_time": None if label == "no_fire" else -1.0,
        "monitor_frames": 10,
        "fired_frames": 0 if label == "no_fire" else 2,
        "brake_frames": 0 if label == "no_fire" else 4,
        "on_collision": True,
    }


def _iter54_report() -> dict:
    pairs = []
    for dataset, label in design.NON_SINGLETON_STRATA:
        pairs.append(_pair(dataset, label, 0, existing=True))
        pairs.extend(_pair(dataset, label, idx) for idx in range(1, 4))
    pairs.append(_pair(*design.SINGLETON_STRATUM, 1, existing=True))
    return {
        "verdict": design.ITER54_VERDICT,
        "infrastructure_problems": [],
        "summaries": {
            "combined": {
                "pairs": 104,
                "on_collision_pairs": 92,
                "monitor_provenance_counts": {
                    "unique_ttc_object": 40,
                    "unique_cpa_object": 36,
                    "both_distinct_objects": 1,
                    "no_fire": 27,
                },
                "collision_actor_support_counts": {"collision_actor_supported": 0},
            }
        },
        "pairs": pairs,
    }


def _iter59_report() -> dict:
    return {
        "verdict": design.ITER59_VERDICT,
        "infra_problems": [],
        "episodes": [{"scenario": f"scene-existing-{dataset}-{label}-00"} for dataset, label in design.NON_SINGLETON_STRATA]
        + [{"scenario": "scene-existing-iter49_hard_extreme-both_distinct_objects-01"}]
        + [{"scenario": f"scene-extra-{idx}"} for idx in range(1, 2)],
    }


def _iter100_report() -> dict:
    return {
        "verdict": design.ITER100_VERDICT,
        "infra_problems": [],
        "summary": {
            "larger_committed_pool_exists": True,
            "can_expand_from_committed_reports": False,
            "new_instrumentation_required_for_larger_structural_bridge": True,
        },
    }


def _reports(tmp_path: Path, *, iter100_verdict: str = design.ITER100_VERDICT) -> tuple[Path, Path, Path]:
    iter54_path = tmp_path / "iter54.json"
    iter59_path = tmp_path / "iter59.json"
    iter100_path = tmp_path / "iter100.json"
    iter54_path.write_text(json.dumps(_iter54_report()))
    iter59_path.write_text(json.dumps(_iter59_report()))
    iter100 = _iter100_report()
    iter100["verdict"] = iter100_verdict
    iter100_path.write_text(json.dumps(iter100))
    return iter54_path, iter59_path, iter100_path


def test_provenance_batch_design_complete(tmp_path: Path) -> None:
    report = design.build_report(*_reports(tmp_path))

    assert report["verdict"] == "HUGSIM_PROVENANCE_BATCH_CANDIDATE_DESIGN_COMPLETE"
    assert report["summary"]["selected_total_count"] == 13
    assert report["summary"]["selected_new_count"] == 12
    assert report["summary"]["carried_singleton_count"] == 1
    assert report["summary"]["all_strata_covered"] is True


def test_provenance_batch_design_blocks_bad_iter100_verdict(tmp_path: Path) -> None:
    report = design.build_report(*_reports(tmp_path, iter100_verdict="WRONG"))

    assert report["verdict"] == "HUGSIM_PROVENANCE_BATCH_CANDIDATE_DESIGN_BLOCKED"
    assert "iter100-verdict-not-HUGSIM_STRUCTURAL_EXPANSION_SUPPORT_BOUNDARY_NULL" in report["infra_problems"]


def test_provenance_batch_design_partial_when_stratum_underfilled(tmp_path: Path) -> None:
    iter54_path, iter59_path, iter100_path = _reports(tmp_path)
    iter54 = json.loads(iter54_path.read_text())
    iter54["pairs"] = [
        row
        for row in iter54["pairs"]
        if not (
            row["dataset"] == "iter48_easy_medium"
            and row["monitor_provenance_label"] == "no_fire"
            and row["scenario"].startswith("scene-new")
        )
    ]
    iter54_path.write_text(json.dumps(iter54))

    report = design.build_report(iter54_path, iter59_path, iter100_path)

    assert report["verdict"] == "HUGSIM_PROVENANCE_BATCH_CANDIDATE_DESIGN_PARTIAL_COMPLETE"
    stratum = report["event"]["measurements"]["strata"]["iter48_easy_medium / no_fire"]
    assert stratum["selected_count"] == 0
