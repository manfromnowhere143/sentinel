from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter67_trigger_target_bridge_audit"
    / "analyze_trigger_target_bridge.py"
)
SPEC = importlib.util.spec_from_file_location("iter67_trigger_target_bridge", MODULE_PATH)
assert SPEC is not None
bridge = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(bridge)


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


def _row(ts: float, objs: list[dict], *, fired: bool = False, min_cpa: float = 99.0) -> dict:
    return {
        "frame_index": int(ts * 4),
        "ts": ts,
        "fired": fired,
        "brake": fired,
        "min_ttc": 99.0,
        "min_cpa": min_cpa,
        "l2g_r_mat": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        "l2g_t": [0.0, 0.0, 0.0],
        "params": {"dt": 1.0, "min_closing": 0.1},
        "traj": [[0.0, 0.0], [0.0, 0.0]],
        "objs": objs,
    }


def _obj(object_id: int, x: float, y: float) -> dict:
    return {"id": object_id, "score": 0.8, "world": [x, y], "vel": [0.0, 0.0]}


def _write_reports(
    tmp_path: Path,
    *,
    split_trigger_matches: bool = False,
    iter66_verdict: str = "MATCHED_OBJECT_TIMELINE_MIXED_COMPLETE",
) -> tuple[Path, Path, Path, Path, Path, Path]:
    proof_root = tmp_path / "proof"
    proof_root.mkdir()
    rows61 = []
    rows64 = []
    rows65 = []
    rows66 = []
    for index, target in enumerate(bridge.EXPECTED_TARGETS):
        audit_id = target["audit_id"]
        scenario = target["scenario"]
        target_id = target["target_object_id"]
        split_row = index == 1
        trigger_id = 1 if split_row else target_id
        ep = proof_root / "episodes" / f"{audit_id}__{scenario}__on"
        ep.mkdir(parents=True)
        (ep / "eval.json").write_text(json.dumps(_eval_doc()))
        if split_row:
            trigger_late = _obj(trigger_id, 0.0, 10.0) if split_trigger_matches else _obj(trigger_id, 50.0, 50.0)
            decisions = [
                _row(0.0, [_obj(trigger_id, 1.0, 0.0), _obj(target_id, 50.0, 0.0)], fired=True, min_cpa=1.0),
                _row(1.0, [trigger_late, _obj(target_id, 0.0, 10.0)]),
            ]
        else:
            decisions = [
                _row(0.0, [_obj(trigger_id, 1.0, 0.0), _obj(99, 50.0, 0.0)], fired=True, min_cpa=1.0),
                _row(1.0, [_obj(target_id, 0.0, 10.0), _obj(99, 50.0, 0.0)]),
            ]
        (ep / "sentinel_iter48_decisions.jsonl").write_text(
            "\n".join(json.dumps(row) for row in decisions) + "\n"
        )
        rows61.append({"audit_id": audit_id, "scenario": scenario, "row_label": "no_monitor_object_support"})
        rows64.append({
            "audit_id": audit_id,
            "scenario": scenario,
            "row_label": "pre_contact_object_match",
            "best_variant": {"object_id": target_id, "decision_ts": 1.0, "foreground_timestamp": 3.0},
        })
        rows65.append({
            "audit_id": audit_id,
            "scenario": scenario,
            "row_label": "matched_object_subthreshold",
            "matched_object_id": target_id,
        })
        rows66.append({
            "audit_id": audit_id,
            "scenario": scenario,
            "row_label": "target_object_ever_active_hazard" if not split_row else "target_object_visible_never_active",
            "target_object_id": target_id,
            "first_fire": {
                "first_fire_ts": 0.0,
                "first_fire_channel": "cpa_only",
                "first_fire_object_id": trigger_id,
                "monitor_provenance_label": "unique_cpa_object",
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
    iter64_report.write_text(json.dumps({"verdict": "UNSUPPORTED_TEMPORAL_MATCH_COMPLETE", "episodes": rows64}))
    iter65_report = tmp_path / "iter65_report.json"
    iter65_report.write_text(json.dumps({"verdict": "TEMPORAL_ALIGNMENT_SUBTHRESHOLD_COMPLETE", "episodes": rows65}))
    iter66_report = tmp_path / "iter66_report.json"
    iter66_report.write_text(json.dumps({"verdict": iter66_verdict, "episodes": rows66}))
    return proof_root, iter59_report, iter61_report, iter64_report, iter65_report, iter66_report


def test_trigger_target_same_and_split_complete(tmp_path: Path) -> None:
    proof_root, iter59, iter61, iter64, iter65, iter66 = _write_reports(tmp_path)

    report = bridge.build_report(proof_root, iter59, iter61, iter64, iter65, iter66)

    assert report["verdict"] == "TRIGGER_TARGET_SAME_AND_SPLIT_COMPLETE"
    assert report["summary"]["same_object_rows"] == 1
    assert report["summary"]["split_object_rows"] == 1
    assert report["episodes"][0]["row_label"] == "same_object_target_trigger_match"
    assert report["episodes"][1]["row_label"] == "split_target_match_trigger_no_support"


def test_trigger_target_split_trigger_match_label(tmp_path: Path) -> None:
    proof_root, iter59, iter61, iter64, iter65, iter66 = _write_reports(tmp_path, split_trigger_matches=True)

    report = bridge.build_report(proof_root, iter59, iter61, iter64, iter65, iter66)

    assert report["verdict"] == "TRIGGER_TARGET_SAME_AND_SPLIT_COMPLETE"
    assert report["episodes"][1]["row_label"] == "split_target_match_trigger_match"
    assert report["summary"]["trigger_match_rows"] == 2


def test_trigger_target_blocked_when_iter66_crosscheck_fails(tmp_path: Path) -> None:
    proof_root, iter59, iter61, iter64, iter65, iter66 = _write_reports(tmp_path, iter66_verdict="WRONG")

    report = bridge.build_report(proof_root, iter59, iter61, iter64, iter65, iter66)

    assert report["verdict"] == "TRIGGER_TARGET_BRIDGE_AUDIT_BLOCKED"
    assert "iter66-verdict-not-MATCHED_OBJECT_TIMELINE_MIXED_COMPLETE" in report["infra_problems"]
