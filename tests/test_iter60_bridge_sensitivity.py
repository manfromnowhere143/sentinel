from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter60_actor_bridge_sensitivity"
    / "analyze_bridge_sensitivity.py"
)
SPEC = importlib.util.spec_from_file_location("iter60_bridge_sensitivity", MODULE_PATH)
assert SPEC is not None
bridge_sensitivity = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(bridge_sensitivity)


def _eval_doc(obs_forward: float, obs_lateral: float = 0.0) -> dict:
    return {
        "nc": 0.0,
        "dac": 1.0,
        "ttc": 0.0,
        "c": 1.0,
        "pdms": 0.0,
        "rc": 0.2,
        "hdscore": 0.0,
        "details": {
            "1.0": {"nc": 0.0, "dac": 1.0, "ttc": 0.0, "c": 1.0, "pdms": 0.0},
        },
        "collision_provenance": [
            {
                "source": "nc",
                "timestamp": 1.0,
                "trajectory_index": 0,
                "collision_type": "foreground",
                "obs_index": 0,
                "obs_name": "car",
                "obs_box": [obs_forward, obs_lateral, 0.0, 1.7, 3.8, 1.4, 0.0],
                "planned_ego_pose": [obs_forward, obs_lateral, 0.0],
            },
        ],
    }


def _decision_row(*, world_y: float = 10.0, vel_y: float = 0.0) -> dict:
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
        "traj": [[0.0, world_y + vel_y]],
        "objs": [{"id": 1, "world": [0.0, world_y], "vel": [0.0, vel_y]}],
    }


def _write_episode(
    root: Path,
    audit_id: str,
    scenario: str,
    *,
    obs_forward: float,
    obs_lateral: float = 0.0,
    world_y: float = 10.0,
    vel_y: float = 0.0,
) -> None:
    ep = root / "episodes" / f"{audit_id}__{scenario}__on"
    ep.mkdir(parents=True)
    (ep / "eval.json").write_text(json.dumps(_eval_doc(obs_forward, obs_lateral)))
    (ep / "sentinel_iter48_decisions.jsonl").write_text(
        json.dumps(_decision_row(world_y=world_y, vel_y=vel_y)) + "\n"
    )
    (ep / "episode_meta.json").write_text(json.dumps({"audit_id": audit_id, "scenario": scenario}))
    (ep / "output.txt").write_text("SENTINEL_I48_DECISION frame=0\n")


def _proof_and_report(tmp_path: Path, obs_values: list[tuple[float, float]]) -> tuple[Path, Path]:
    proof_root = tmp_path / "proof"
    proof_root.mkdir()
    rows = []
    for idx, (obs_forward, obs_lateral) in enumerate(obs_values):
        audit_id = f"audit_{idx}"
        scenario = f"scene-{idx:04d}"
        _write_episode(
            proof_root,
            audit_id,
            scenario,
            obs_forward=obs_forward,
            obs_lateral=obs_lateral,
        )
        rows.append({
            "audit_id": audit_id,
            "scenario": scenario,
            "support_label": "classifiable_foreground",
            "bridge_distance_m": 99.0,
            "bridge_label": "actor_mismatch",
        })
    report_path = tmp_path / "iter59_report.json"
    report_path.write_text(json.dumps({"verdict": "ACTOR_MATCH_AUDIT_COMPLETE", "episodes": rows}))
    return proof_root, report_path


def test_bridge_robust_mismatch_complete_when_all_min_distances_exceed_threshold(tmp_path: Path) -> None:
    proof_root, report_path = _proof_and_report(tmp_path, [(100.0, 100.0), (90.0, 90.0), (80.0, 80.0)])

    report = bridge_sensitivity.build_report(proof_root, report_path)

    assert report["verdict"] == "BRIDGE_ROBUST_MISMATCH_COMPLETE"
    assert report["summary"]["sensitivity_counts"] == {"robust_mismatch": 3}


def test_bridge_sensitive_null_when_any_variant_can_match(tmp_path: Path) -> None:
    proof_root, report_path = _proof_and_report(tmp_path, [(10.0, 0.0), (90.0, 90.0), (80.0, 80.0)])

    report = bridge_sensitivity.build_report(proof_root, report_path)

    assert report["verdict"] == "BRIDGE_SENSITIVE_NULL"
    assert report["episodes"][0]["best_label"] == "bridge_match_possible"
    assert report["episodes"][0]["best_distance_m"] == 0.0


def test_bridge_ambiguous_null_when_no_match_but_one_variant_is_close(tmp_path: Path) -> None:
    proof_root, report_path = _proof_and_report(tmp_path, [(14.0, 0.0), (90.0, 90.0), (80.0, 80.0)])

    report = bridge_sensitivity.build_report(proof_root, report_path)

    assert report["verdict"] == "BRIDGE_AMBIGUOUS_NULL"
    assert report["episodes"][0]["best_label"] == "bridge_ambiguous_possible"
    assert report["episodes"][0]["best_distance_m"] == 4.0


def test_bridge_sensitive_null_can_use_propagated_position(tmp_path: Path) -> None:
    proof_root = tmp_path / "proof"
    proof_root.mkdir()
    rows = []
    for idx, obs_forward in enumerate((20.0, 90.0, 80.0)):
        audit_id = f"audit_{idx}"
        scenario = f"scene-{idx:04d}"
        _write_episode(
            proof_root,
            audit_id,
            scenario,
            obs_forward=obs_forward,
            world_y=10.0,
            vel_y=10.0 if idx == 0 else 0.0,
        )
        rows.append({
            "audit_id": audit_id,
            "scenario": scenario,
            "support_label": "classifiable_foreground",
            "bridge_distance_m": 99.0,
            "bridge_label": "actor_mismatch",
        })
    report_path = tmp_path / "iter59_report.json"
    report_path.write_text(json.dumps({"verdict": "ACTOR_MATCH_AUDIT_COMPLETE", "episodes": rows}))

    report = bridge_sensitivity.build_report(proof_root, report_path)

    assert report["verdict"] == "BRIDGE_SENSITIVE_NULL"
    assert report["episodes"][0]["best_variant"]["temporal_source"] == "propagated_to_foreground"
    assert report["episodes"][0]["best_distance_m"] == 0.0


def test_bridge_infra_null_when_iter59_crosscheck_fails(tmp_path: Path) -> None:
    proof_root, report_path = _proof_and_report(tmp_path, [(100.0, 100.0), (90.0, 90.0), (80.0, 80.0)])
    report_path.write_text(json.dumps({"verdict": "WRONG", "episodes": []}))

    report = bridge_sensitivity.build_report(proof_root, report_path)

    assert report["verdict"] == "BRIDGE_SENSITIVITY_INFRA_NULL"
    assert "iter59-verdict-not-ACTOR_MATCH_AUDIT_COMPLETE" in report["infra_problems"]
