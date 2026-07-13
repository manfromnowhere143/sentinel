from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter59_hugsim_actor_match_audit"
    / "analyze_actor_match.py"
)
SPEC = importlib.util.spec_from_file_location("iter59_actor_match", MODULE_PATH)
assert SPEC is not None
actor_match = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(actor_match)


def _eval_doc(obs_forward: float = 10.0) -> dict:
    return {
        "nc": 0.0,
        "dac": 1.0,
        "ttc": 0.0,
        "c": 1.0,
        "pdms": 0.0,
        "rc": 0.2,
        "hdscore": 0.0,
        "details": {
            "0.25": {"nc": 0.0, "dac": 1.0, "ttc": 0.0, "c": 1.0, "pdms": 0.0},
        },
        "collision_provenance": [
            {
                "source": "nc",
                "timestamp": 1.0,
                "trajectory_index": 0,
                "collision_type": "foreground",
                "obs_index": 0,
                "obs_name": "car",
                "obs_box": [obs_forward, 0.0, 0.0, 1.7, 3.8, 1.4, 0.0],
                "planned_ego_pose": [obs_forward, 0.0, 0.0],
            },
        ],
    }


def _decision_row(fired: bool = True) -> dict:
    return {
        "frame_index": 0,
        "ts": 0.0,
        "fired": fired,
        "brake": fired,
        "min_ttc": 1_000_000_000.0,
        "min_cpa": 0.0 if fired else 10.0,
        "l2g_r_mat": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        "l2g_t": [0.0, 0.0, 0.0],
        "params": {"dt": 1.0, "min_closing": 0.1},
        "traj": [[0.0, 10.0]],
        "objs": [{"id": 1, "world": [0.0, 10.0], "vel": [0.0, 0.0]}],
    }


def _write_episode(root: Path, audit_id: str, scenario: str, *, fired: bool, obs_forward: float) -> None:
    ep = root / "episodes" / f"{audit_id}__{scenario}__on"
    ep.mkdir(parents=True)
    (ep / "eval.json").write_text(json.dumps(_eval_doc(obs_forward)))
    (ep / "sentinel_iter48_decisions.jsonl").write_text(json.dumps(_decision_row(fired)) + "\n")
    (ep / "episode_meta.json").write_text(json.dumps({"audit_id": audit_id, "scenario": scenario}))
    (ep / "output.txt").write_text("SENTINEL_I48_DECISION frame=0\n")


def _proof_root(tmp_path: Path, classifiable: int) -> Path:
    root = tmp_path / "proof"
    root.mkdir()
    (root / "receipts.json").write_text("{}")
    distances = [10.0, 14.0, 20.0]
    for idx, (audit_id, scenario) in enumerate(actor_match.SCHEDULE):
        fired = idx < classifiable
        obs_forward = distances[idx] if idx < len(distances) else 10.0
        _write_episode(root, audit_id, scenario, fired=fired, obs_forward=obs_forward)
    return root


def test_actor_match_audit_complete_with_three_classifiable_rows(tmp_path: Path) -> None:
    report = actor_match.build_report(_proof_root(tmp_path, classifiable=3))

    assert report["verdict"] == "ACTOR_MATCH_AUDIT_COMPLETE"
    assert report["summary"]["classifiable_foreground"] == 3
    assert report["summary"]["bridge_counts"] == {
        "actor_ambiguous": 1,
        "actor_match": 1,
        "actor_mismatch": 1,
    }


def test_actor_match_support_null_when_too_few_classifiable_rows(tmp_path: Path) -> None:
    report = actor_match.build_report(_proof_root(tmp_path, classifiable=2))

    assert report["verdict"] == "ACTOR_MATCH_SUPPORT_NULL"
    assert report["summary"]["classifiable_foreground"] == 2


def test_actor_match_infra_null_when_required_artifact_missing(tmp_path: Path) -> None:
    root = _proof_root(tmp_path, classifiable=3)
    first_audit, first_scenario = actor_match.SCHEDULE[0]
    decision_path = root / "episodes" / f"{first_audit}__{first_scenario}__on" / "sentinel_iter48_decisions.jsonl"
    decision_path.unlink()

    report = actor_match.build_report(root)

    assert report["verdict"] == "ACTOR_MATCH_INFRA_NULL"
    assert report["episodes"][0]["problems"] == ["missing-decisions"]
