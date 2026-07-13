from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter66_matched_object_timeline_audit"
    / "analyze_matched_object_timeline.py"
)
SPEC = importlib.util.spec_from_file_location("iter66_matched_object_timeline", MODULE_PATH)
assert SPEC is not None
timeline = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(timeline)


def _eval_doc() -> dict:
    return {
        "collision_provenance": [
            {
                "timestamp": 3.0,
                "collision_type": "foreground",
                "obs_index": 0,
                "obs_name": "car",
                "obs_box": [10.0, 0.0],
            }
        ]
    }


def _decision_row(ts: float, target_id: int, target_distance: float, *, fired: bool = False) -> dict:
    return {
        "frame_index": int(ts * 4),
        "ts": ts,
        "fired": fired,
        "brake": fired,
        "min_ttc": 99.0,
        "min_cpa": 1.0 if fired else target_distance,
        "l2g_r_mat": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        "l2g_t": [0.0, 0.0, 0.0],
        "params": {"dt": 1.0, "min_closing": 0.1},
        "traj": [[0.0, 0.0], [0.0, 0.0]],
        "objs": [
            {"id": 1, "score": 0.9, "world": [1.0, 0.0], "vel": [0.0, 0.0]},
            {"id": target_id, "score": 0.8, "world": [target_distance, 0.0], "vel": [0.0, 0.0]},
        ],
    }


def _write_reports(
    tmp_path: Path,
    timelines: list[list[float]],
    *,
    iter65_verdict: str = "TEMPORAL_ALIGNMENT_SUBTHRESHOLD_COMPLETE",
) -> tuple[Path, Path, Path, Path, Path]:
    proof_root = tmp_path / "proof"
    proof_root.mkdir()
    rows61 = []
    rows64 = []
    rows65 = []
    for target, distances in zip(timeline.EXPECTED_TARGETS, timelines, strict=True):
        audit_id = target["audit_id"]
        scenario = target["scenario"]
        object_id = target["object_id"]
        ep = proof_root / "episodes" / f"{audit_id}__{scenario}__on"
        ep.mkdir(parents=True)
        (ep / "eval.json").write_text(json.dumps(_eval_doc()))
        decision_rows = [
            _decision_row(float(idx), object_id, distance, fired=idx == 0)
            for idx, distance in enumerate(distances)
        ]
        (ep / "sentinel_iter48_decisions.jsonl").write_text(
            "\n".join(json.dumps(row) for row in decision_rows) + "\n"
        )
        rows61.append({"audit_id": audit_id, "scenario": scenario, "row_label": "no_monitor_object_support"})
        rows64.append({
            "audit_id": audit_id,
            "scenario": scenario,
            "row_label": "pre_contact_object_match",
            "best_variant": {
                "decision_ts": 1.0,
                "object_id": object_id,
                "foreground_timestamp": 3.0,
                "distance_m": 1.0,
            },
        })
        rows65.append({
            "audit_id": audit_id,
            "scenario": scenario,
            "row_label": "matched_object_subthreshold",
            "matched_object_id": object_id,
            "matched_decision_ts": 1.0,
        })
    iter59_report = tmp_path / "iter59_report.json"
    iter59_report.write_text(json.dumps({"verdict": "ACTOR_MATCH_AUDIT_COMPLETE"}))
    iter61_report = tmp_path / "iter61_report.json"
    iter61_report.write_text(json.dumps({
        "verdict": "OBJECT_SURFACE_NONTRIGGER_MATCH_COMPLETE",
        "episodes": rows61,
    }))
    iter64_report = tmp_path / "iter64_report.json"
    iter64_report.write_text(json.dumps({"verdict": "UNSUPPORTED_TEMPORAL_MATCH_COMPLETE", "episodes": rows64}))
    iter65_report = tmp_path / "iter65_report.json"
    iter65_report.write_text(json.dumps({"verdict": iter65_verdict, "episodes": rows65}))
    return proof_root, iter59_report, iter61_report, iter64_report, iter65_report


def test_matched_object_timeline_ever_hazard_complete(tmp_path: Path) -> None:
    proof_root, iter59, iter61, iter64, iter65 = _write_reports(tmp_path, [[8.0, 1.0, 8.0], [9.0, 1.2, 9.0]])

    report = timeline.build_report(proof_root, iter59, iter61, iter64, iter65)

    assert report["verdict"] == "MATCHED_OBJECT_TIMELINE_EVER_HAZARD_COMPLETE"
    assert report["summary"]["row_label_counts"] == {"target_object_ever_active_hazard": 2}
    assert report["summary"]["total_hazard_frames"] == 2


def test_matched_object_timeline_never_hazard_complete(tmp_path: Path) -> None:
    proof_root, iter59, iter61, iter64, iter65 = _write_reports(tmp_path, [[8.0, 7.0, 8.0], [9.0, 8.0, 9.0]])

    report = timeline.build_report(proof_root, iter59, iter61, iter64, iter65)

    assert report["verdict"] == "MATCHED_OBJECT_TIMELINE_NEVER_HAZARD_COMPLETE"
    assert report["summary"]["row_label_counts"] == {"target_object_visible_never_active": 2}
    assert report["summary"]["total_hazard_frames"] == 0


def test_matched_object_timeline_mixed_complete(tmp_path: Path) -> None:
    proof_root, iter59, iter61, iter64, iter65 = _write_reports(tmp_path, [[8.0, 1.0, 8.0], [9.0, 8.0, 9.0]])

    report = timeline.build_report(proof_root, iter59, iter61, iter64, iter65)

    assert report["verdict"] == "MATCHED_OBJECT_TIMELINE_MIXED_COMPLETE"
    assert report["summary"]["row_label_counts"] == {
        "target_object_ever_active_hazard": 1,
        "target_object_visible_never_active": 1,
    }


def test_matched_object_timeline_blocked_when_iter65_crosscheck_fails(tmp_path: Path) -> None:
    proof_root, iter59, iter61, iter64, iter65 = _write_reports(
        tmp_path,
        [[8.0, 1.0, 8.0], [9.0, 1.2, 9.0]],
        iter65_verdict="WRONG",
    )

    report = timeline.build_report(proof_root, iter59, iter61, iter64, iter65)

    assert report["verdict"] == "MATCHED_OBJECT_TIMELINE_AUDIT_BLOCKED"
    assert "iter65-verdict-not-TEMPORAL_ALIGNMENT_SUBTHRESHOLD_COMPLETE" in report["infra_problems"]
