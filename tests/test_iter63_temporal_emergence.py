from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter63_temporal_emergence_audit"
    / "analyze_temporal_emergence.py"
)
SPEC = importlib.util.spec_from_file_location("iter63_temporal_emergence", MODULE_PATH)
assert SPEC is not None
temporal = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(temporal)


def _eval_doc(first_foreground_ts: float = 3.0) -> dict:
    return {
        "collision_provenance": [
            {
                "timestamp": first_foreground_ts,
                "collision_type": "foreground",
                "obs_box": [10.0, 0.0],
            }
        ]
    }


def _decision_row(ts: float, object_y: float | None) -> dict:
    objs = []
    if object_y is not None:
        objs.append({"id": temporal.TARGET_OBJECT_ID, "score": 0.7, "world": [0.0, object_y], "vel": [0.0, 0.0]})
    return {
        "frame_index": int(ts * 4),
        "ts": ts,
        "fired": ts >= 1.0,
        "brake": ts >= 1.0,
        "l2g_r_mat": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        "l2g_t": [0.0, 0.0, 0.0],
        "params": {"dt": 1.0, "min_closing": 0.1},
        "traj": [[0.0, 10.0]],
        "objs": objs,
    }


def _proof_and_reports(tmp_path: Path, object_ys: list[float | None]) -> tuple[Path, Path, Path, Path]:
    proof_root = tmp_path / "proof"
    ep = proof_root / "episodes" / f"{temporal.TARGET_AUDIT_ID}__{temporal.TARGET_SCENARIO}__on"
    ep.mkdir(parents=True)
    (ep / "eval.json").write_text(json.dumps(_eval_doc()))
    rows = [_decision_row(float(idx), object_y) for idx, object_y in enumerate(object_ys)]
    (ep / "sentinel_iter48_decisions.jsonl").write_text("\n".join(json.dumps(row) for row in rows) + "\n")

    iter59_report = tmp_path / "iter59_report.json"
    iter59_report.write_text(json.dumps({"verdict": "ACTOR_MATCH_AUDIT_COMPLETE"}))
    iter61_report = tmp_path / "iter61_report.json"
    iter61_report.write_text(json.dumps({
        "verdict": "OBJECT_SURFACE_NONTRIGGER_MATCH_COMPLETE",
        "episodes": [
            {
                "audit_id": temporal.TARGET_AUDIT_ID,
                "scenario": temporal.TARGET_SCENARIO,
                "row_label": "nontrigger_object_match",
            }
        ],
    }))
    iter62_report = tmp_path / "iter62_report.json"
    iter62_report.write_text(json.dumps({
        "verdict": "MATCHED_OBJECT_SUBTHRESHOLD_COMPLETE",
        "target": {
            "audit_id": temporal.TARGET_AUDIT_ID,
            "scenario": temporal.TARGET_SCENARIO,
            "matched_object_id": temporal.TARGET_OBJECT_ID,
            "trigger_object_id": temporal.TRIGGER_OBJECT_ID,
        },
        "matched_object_label": "matched_object_subthreshold",
    }))
    return proof_root, iter59_report, iter61_report, iter62_report


def test_temporal_hazard_emerged_when_pre_contact_frame_crosses(tmp_path: Path) -> None:
    proof_root, iter59, iter61, iter62 = _proof_and_reports(tmp_path, [20.0, 10.5, 20.0, 10.0])

    report = temporal.build_report(proof_root, iter59, iter61, iter62)

    assert report["verdict"] == "TEMPORAL_HAZARD_EMERGED_COMPLETE"
    assert report["summary"]["row_label"] == "pre_contact_hazard_cross"
    assert report["summary"]["first_hazard_ts"] == 1.0


def test_temporal_borderline_when_close_but_not_crossing(tmp_path: Path) -> None:
    proof_root, iter59, iter61, iter62 = _proof_and_reports(tmp_path, [20.0, 12.0, 20.0, 10.0])

    report = temporal.build_report(proof_root, iter59, iter61, iter62)

    assert report["verdict"] == "TEMPORAL_BORDERLINE_NULL"
    assert report["summary"]["row_label"] == "pre_contact_borderline_only"
    assert report["summary"]["first_borderline_ts"] == 1.0


def test_temporal_visible_never_hazard_when_present_and_far(tmp_path: Path) -> None:
    proof_root, iter59, iter61, iter62 = _proof_and_reports(tmp_path, [20.0, 21.0, 22.0, 10.0])

    report = temporal.build_report(proof_root, iter59, iter61, iter62)

    assert report["verdict"] == "TEMPORAL_VISIBLE_NEVER_HAZARD_COMPLETE"
    assert report["summary"]["row_label"] == "visible_never_hazard"
    assert report["summary"]["present_frame_count"] == 3


def test_temporal_support_null_when_object_rarely_present(tmp_path: Path) -> None:
    proof_root, iter59, iter61, iter62 = _proof_and_reports(tmp_path, [None, 20.0, None, 10.0])

    report = temporal.build_report(proof_root, iter59, iter61, iter62)

    assert report["verdict"] == "TEMPORAL_SUPPORT_NULL"
    assert report["summary"]["row_label"] == "insufficient_temporal_support"


def test_temporal_infra_null_when_crosscheck_fails(tmp_path: Path) -> None:
    proof_root, iter59, iter61, iter62 = _proof_and_reports(tmp_path, [20.0, 21.0, 22.0, 10.0])
    iter62.write_text(json.dumps({"verdict": "WRONG"}))

    report = temporal.build_report(proof_root, iter59, iter61, iter62)

    assert report["verdict"] == "TEMPORAL_EMERGENCE_INFRA_NULL"
    assert "iter62-verdict-not-MATCHED_OBJECT_SUBTHRESHOLD_COMPLETE" in report["infra_problems"]
