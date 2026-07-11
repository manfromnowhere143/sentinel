from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "experiments/iter41_sensor_input_degradation_gate/analyze_degradation_gate.py"


def load_module():
    spec = importlib.util.spec_from_file_location("iter41_degradation_gate", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def identity_pose(tx: float = 0.0, ty: float = 0.0):
    return [
        [1.0, 0.0, 0.0, tx],
        [0.0, 1.0, 0.0, ty],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]


def test_iter41_transform_point_applies_world_translation():
    module = load_module()
    assert module.transform_point(identity_pose(10.0, -3.0), [2.0, 5.0]) == (12.0, 2.0)


def test_iter41_dropout_and_jitter_are_deterministic_and_bounded():
    module = load_module()
    scen = "stationary-0099"

    assert module.dropout_object(scen, 3, 4, 5) == module.dropout_object(scen, 3, 4, 5)

    x1 = module.jitter_offset(scen, 3, 4, 5, "x")
    x2 = module.jitter_offset(scen, 3, 4, 5, "x")
    y = module.jitter_offset(scen, 3, 4, 5, "y")
    assert x1 == x2
    assert -0.25 <= x1 <= 0.25
    assert -0.25 <= y <= 0.25
    assert x1 != y


def test_iter41_replay_episode_fires_and_releases_latch():
    module = load_module()
    block = {
        "frames": [
            {
                "ts": 0,
                "traj": [[1.0, 0.0], [2.0, 0.0]],
                "objs": [[1.0, 0.0, 1.0, 1.0, 0.0]],
                "scores": [1.0],
            },
            {"ts": 500000, "traj": [[1.0, 0.0]], "objs": [], "scores": []},
            {"ts": 1000000, "traj": [[1.0, 0.0]], "objs": [], "scores": []},
            {"ts": 1500000, "traj": [[1.0, 0.0]], "objs": [], "scores": []},
        ]
    }
    poses = {str(frame["ts"]): identity_pose() for frame in block["frames"]}

    replay = module.replay_episode(
        block,
        poses,
        "unit-0001",
        0,
        params=module.ReplayParams(release_k=2),
    )

    assert replay["brake_frame_indices"] == [0, 1]
    assert replay["first_brake_frame_index"] == 0


def test_iter41_pose_coverage_reports_exact_timestamp_miss():
    module = load_module()
    blocks = [
        {
            "frames": [{"ts": 100}, {"ts": 200}],
            "brakes": [],
            "releases": [],
            "reset_run": 0,
        }
    ]
    pair_order = [("stationary", "0001")]
    pose_maps = {("stationary", "0001", 0): {"150": identity_pose()}}

    report = module.pose_timestamp_coverage(blocks, pair_order, pose_maps)

    assert report["total_frame_rows_checked"] == 2
    assert report["missing_exact_timestamp_count"] == 2
    assert report["examples"][0]["nearest_delta_us"] == 50


def test_iter41_s1_counts_lost_interventions_as_large_delay():
    module = load_module()
    key = ("frontal", "0001", 0)
    vanilla = {
        key: {
            "intervention_episode": True,
            "first_brake_timestamp_us": 1_000_000,
            "brake_frame_count": 4,
        }
    }
    perturbed = {
        key: {
            "intervention_episode": False,
            "first_brake_timestamp_us": None,
            "brake_frame_count": 0,
        }
    }
    meta = {key: {"off_collision": True}}

    report = module.evaluate_s1_mode("dropout_20pct", vanilla, perturbed, meta)

    assert not report["pass"]
    assert report["retained_fraction"] == 0.0
    assert report["large_or_lost_delay_fraction"] == 1.0


def test_iter41_verdict_order():
    module = load_module()
    ok = {"pass": True}
    fail = {"pass": False}

    assert module.verdict(fail, None, None, None, None) == "DEGRADATION_GATE_INFRASTRUCTURE_NULL"
    assert module.verdict(ok, fail, None, None, None) == (
        "DEGRADATION_GATE_NULL_SAFETY_RETENTION_FAIL"
    )
    assert module.verdict(ok, ok, fail, None, None) == (
        "DEGRADATION_GATE_NULL_SELECTIVITY_COST_FAIL"
    )
    assert module.verdict(ok, ok, ok, fail, None) == (
        "DEGRADATION_GATE_NULL_LEADTIME_STABILITY_FAIL"
    )
    assert module.verdict(ok, ok, ok, ok, fail) == "DEGRADATION_GATE_OVERCLAIM_NULL"
    assert module.verdict(ok, ok, ok, ok, ok) == (
        "DEGRADATION_GATE_PASS_OFFLINE_OBJECT_STREAM_SCOPE"
    )
