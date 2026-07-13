from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter65_temporal_alignment_audit"
    / "analyze_temporal_alignment.py"
)
SPEC = importlib.util.spec_from_file_location("iter65_temporal_alignment", MODULE_PATH)
assert SPEC is not None
alignment = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(alignment)


def _decision_row(ts: float, matched_distance: float, *, fired: bool = False) -> dict:
    return {
        "frame_index": int(ts * 4),
        "ts": ts,
        "fired": fired,
        "brake": fired,
        "min_ttc": 99.0,
        "min_cpa": 1.0 if fired else matched_distance,
        "l2g_r_mat": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        "l2g_t": [0.0, 0.0, 0.0],
        "params": {"dt": 1.0, "min_closing": 0.1},
        "traj": [[0.0, 0.0], [0.0, 0.0]],
        "objs": [
            {"id": 1, "score": 0.9, "world": [1.0, 0.0], "vel": [0.0, 0.0]},
            {"id": 2, "score": 0.8, "world": [matched_distance, 0.0], "vel": [0.0, 0.0]},
        ],
    }


def _write_reports(
    tmp_path: Path,
    matched_distances: list[float],
    *,
    iter64_verdict: str = "UNSUPPORTED_TEMPORAL_MATCH_COMPLETE",
) -> tuple[Path, Path, Path, Path]:
    proof_root = tmp_path / "proof"
    proof_root.mkdir()
    rows61 = []
    rows64 = []
    for (audit_id, scenario), matched_distance in zip(alignment.EXPECTED_ROWS, matched_distances, strict=True):
        ep = proof_root / "episodes" / f"{audit_id}__{scenario}__on"
        ep.mkdir(parents=True)
        decisions = [
            _decision_row(0.0, 10.0, fired=True),
            _decision_row(1.0, matched_distance),
        ]
        (ep / "sentinel_iter48_decisions.jsonl").write_text(
            "\n".join(json.dumps(row) for row in decisions) + "\n"
        )
        rows61.append({"audit_id": audit_id, "scenario": scenario, "row_label": "no_monitor_object_support"})
        rows64.append({
            "audit_id": audit_id,
            "scenario": scenario,
            "row_label": "pre_contact_object_match",
            "best_variant": {
                "decision_ts": 1.0,
                "object_id": 2,
                "foreground_timestamp": 3.0,
                "distance_m": 1.0,
                "temporal_source": "frame_time",
                "axis_order": "xy",
                "forward_sign": 1,
                "lateral_sign": 1,
                "lead_time_s": 2.0,
            },
        })
    iter59_report = tmp_path / "iter59_report.json"
    iter59_report.write_text(json.dumps({"verdict": "ACTOR_MATCH_AUDIT_COMPLETE"}))
    iter61_report = tmp_path / "iter61_report.json"
    iter61_report.write_text(json.dumps({
        "verdict": "OBJECT_SURFACE_NONTRIGGER_MATCH_COMPLETE",
        "episodes": rows61,
    }))
    iter64_report = tmp_path / "iter64_report.json"
    iter64_report.write_text(json.dumps({"verdict": iter64_verdict, "episodes": rows64}))
    return proof_root, iter59_report, iter61_report, iter64_report


def test_temporal_alignment_active_hazard_complete(tmp_path: Path) -> None:
    proof_root, iter59, iter61, iter64 = _write_reports(tmp_path, [1.0, 1.2])

    report = alignment.build_report(proof_root, iter59, iter61, iter64)

    assert report["verdict"] == "TEMPORAL_ALIGNMENT_ACTIVE_HAZARD_COMPLETE"
    assert report["summary"]["row_label_counts"] == {"matched_object_active_hazard": 2}
    assert report["summary"]["matched_objects_equal_first_fire_objects"] == 0


def test_temporal_alignment_subthreshold_complete(tmp_path: Path) -> None:
    proof_root, iter59, iter61, iter64 = _write_reports(tmp_path, [8.0, 9.0])

    report = alignment.build_report(proof_root, iter59, iter61, iter64)

    assert report["verdict"] == "TEMPORAL_ALIGNMENT_SUBTHRESHOLD_COMPLETE"
    assert report["summary"]["row_label_counts"] == {"matched_object_subthreshold": 2}
    assert report["episodes"][0]["matched_object"]["cpa_cross"] is False


def test_temporal_alignment_mixed_complete(tmp_path: Path) -> None:
    proof_root, iter59, iter61, iter64 = _write_reports(tmp_path, [1.0, 9.0])

    report = alignment.build_report(proof_root, iter59, iter61, iter64)

    assert report["verdict"] == "TEMPORAL_ALIGNMENT_MIXED_COMPLETE"
    assert report["summary"]["row_label_counts"] == {
        "matched_object_active_hazard": 1,
        "matched_object_subthreshold": 1,
    }


def test_temporal_alignment_blocked_when_iter64_crosscheck_fails(tmp_path: Path) -> None:
    proof_root, iter59, iter61, iter64 = _write_reports(tmp_path, [1.0, 1.2], iter64_verdict="WRONG")

    report = alignment.build_report(proof_root, iter59, iter61, iter64)

    assert report["verdict"] == "TEMPORAL_ALIGNMENT_AUDIT_BLOCKED"
    assert "iter64-verdict-not-UNSUPPORTED_TEMPORAL_MATCH_COMPLETE" in report["infra_problems"]
