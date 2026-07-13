from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter61_monitor_object_surface_audit"
    / "analyze_object_surface.py"
)
SPEC = importlib.util.spec_from_file_location("iter61_object_surface", MODULE_PATH)
assert SPEC is not None
object_surface = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(object_surface)


def _eval_doc(obs_values: list[tuple[float, float]]) -> dict:
    provenance = []
    details = {}
    for idx, (obs_forward, obs_lateral) in enumerate(obs_values):
        timestamp = float(idx + 1)
        details[str(timestamp)] = {"nc": 0.0, "dac": 1.0, "ttc": 0.0, "c": 1.0, "pdms": 0.0}
        provenance.append({
            "source": "nc",
            "timestamp": timestamp,
            "trajectory_index": idx,
            "collision_type": "foreground",
            "obs_index": idx,
            "obs_name": "car",
            "obs_box": [obs_forward, obs_lateral, 0.0, 1.7, 3.8, 1.4, 0.0],
            "planned_ego_pose": [obs_forward, obs_lateral, 0.0],
        })
    return {
        "nc": 0.0,
        "dac": 1.0,
        "ttc": 0.0,
        "c": 1.0,
        "pdms": 0.0,
        "rc": 0.2,
        "hdscore": 0.0,
        "details": details,
        "collision_provenance": provenance,
    }


def _decision_row() -> dict:
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
            {"id": 1, "world": [0.0, 10.0], "vel": [0.0, 0.0]},
            {"id": 2, "world": [0.0, 20.0], "vel": [0.0, 0.0]},
        ],
    }


def _write_episode(root: Path, audit_id: str, scenario: str, obs_values: list[tuple[float, float]]) -> None:
    ep = root / "episodes" / f"{audit_id}__{scenario}__on"
    ep.mkdir(parents=True)
    (ep / "eval.json").write_text(json.dumps(_eval_doc(obs_values)))
    (ep / "sentinel_iter48_decisions.jsonl").write_text(json.dumps(_decision_row()) + "\n")
    (ep / "episode_meta.json").write_text(json.dumps({"audit_id": audit_id, "scenario": scenario}))
    (ep / "output.txt").write_text("SENTINEL_I48_DECISION frame=0\n")


def _proof_and_reports(
    tmp_path: Path,
    obs_by_row: list[list[tuple[float, float]]],
) -> tuple[Path, Path, Path]:
    proof_root = tmp_path / "proof"
    proof_root.mkdir()
    rows59 = []
    rows60 = []
    for (audit_id, scenario), obs_values in zip(object_surface.EXPECTED_ROWS, obs_by_row, strict=True):
        _write_episode(proof_root, audit_id, scenario, obs_values)
        row = {
            "audit_id": audit_id,
            "scenario": scenario,
            "support_label": "classifiable_foreground",
            "bridge_distance_m": 99.0,
            "bridge_label": "actor_mismatch",
        }
        rows59.append(row)
        rows60.append({
            "audit_id": audit_id,
            "scenario": scenario,
            "iter59_bridge_distance_m": 99.0,
            "iter59_bridge_label": "actor_mismatch",
        })
    iter59_report = tmp_path / "iter59_report.json"
    iter59_report.write_text(json.dumps({"verdict": "ACTOR_MATCH_AUDIT_COMPLETE", "episodes": rows59}))
    iter60_report = tmp_path / "iter60_report.json"
    iter60_report.write_text(json.dumps({
        "verdict": "BRIDGE_AMBIGUOUS_NULL",
        "classifiable_rows": rows60,
    }))
    return proof_root, iter59_report, iter60_report


def test_object_surface_trigger_match_takes_priority(tmp_path: Path) -> None:
    proof_root, iter59_report, iter60_report = _proof_and_reports(
        tmp_path,
        [[(10.0, 0.0)], [(100.0, 100.0)], [(90.0, 90.0)]],
    )

    report = object_surface.build_report(proof_root, iter59_report, iter60_report)

    assert report["verdict"] == "OBJECT_SURFACE_TRIGGER_MATCH_COMPLETE"
    assert report["episodes"][0]["row_label"] == "trigger_object_match"
    assert report["episodes"][0]["trigger_min_distance_m"] == 0.0


def test_object_surface_nontrigger_match_uses_all_foreground_rows(tmp_path: Path) -> None:
    proof_root, iter59_report, iter60_report = _proof_and_reports(
        tmp_path,
        [[(100.0, 100.0), (20.0, 0.0)], [(100.0, 100.0)], [(90.0, 90.0)]],
    )

    report = object_surface.build_report(proof_root, iter59_report, iter60_report)

    assert report["verdict"] == "OBJECT_SURFACE_NONTRIGGER_MATCH_COMPLETE"
    assert report["episodes"][0]["row_label"] == "nontrigger_object_match"
    assert report["episodes"][0]["best_nontrigger_variant"]["foreground_timestamp"] == 2.0
    assert report["episodes"][0]["nontrigger_min_distance_m"] == 0.0


def test_object_surface_ambiguous_null_without_matches(tmp_path: Path) -> None:
    proof_root, iter59_report, iter60_report = _proof_and_reports(
        tmp_path,
        [[(14.0, 0.0)], [(100.0, 100.0)], [(90.0, 90.0)]],
    )

    report = object_surface.build_report(proof_root, iter59_report, iter60_report)

    assert report["verdict"] == "OBJECT_SURFACE_AMBIGUOUS_NULL"
    assert report["episodes"][0]["row_label"] == "trigger_object_ambiguous"
    assert report["episodes"][0]["trigger_min_distance_m"] == 4.0


def test_object_surface_no_support_complete_when_everything_far(tmp_path: Path) -> None:
    proof_root, iter59_report, iter60_report = _proof_and_reports(
        tmp_path,
        [[(100.0, 100.0)], [(90.0, 90.0)], [(80.0, 80.0)]],
    )

    report = object_surface.build_report(proof_root, iter59_report, iter60_report)

    assert report["verdict"] == "OBJECT_SURFACE_NO_SUPPORT_COMPLETE"
    assert report["summary"]["row_label_counts"] == {"no_monitor_object_support": 3}


def test_object_surface_infra_null_when_iter60_crosscheck_fails(tmp_path: Path) -> None:
    proof_root, iter59_report, iter60_report = _proof_and_reports(
        tmp_path,
        [[(100.0, 100.0)], [(90.0, 90.0)], [(80.0, 80.0)]],
    )
    iter60_report.write_text(json.dumps({"verdict": "WRONG", "classifiable_rows": []}))

    report = object_surface.build_report(proof_root, iter59_report, iter60_report)

    assert report["verdict"] == "OBJECT_SURFACE_INFRA_NULL"
    assert "iter60-verdict-not-BRIDGE_AMBIGUOUS_NULL" in report["infra_problems"]
