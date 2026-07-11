from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "experiments/iter44_velocity_smoothing_gate/analyze_velocity_smoothing.py"
HYPOTHESIS = ROOT / "experiments/iter44_velocity_smoothing_gate/HYPOTHESIS.md"


def load_module():
    spec = importlib.util.spec_from_file_location("iter44_velocity_smoothing", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def identity_pose():
    return [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]


def frame(idx, *, objs, scores, object_ids=None):
    return {
        "trace_version": "iter42_exact_trace_v1",
        "run": 0,
        "frame_index": idx,
        "ts": idx * 500000,
        "traj": [[1.0, 0.0]],
        "objs": objs,
        "scores": scores,
        "object_ids": object_ids or [],
        "ego2world": identity_pose(),
        "params": {
            "SENTINEL_MIN_SCORE": 0.3,
            "SENTINEL_MAXGAP": 30.0,
            "SENTINEL_CPA_MARGIN": 1.5,
            "SENTINEL_TTC": 2.5,
            "SENTINEL_MIN_CLOSING": 3.0,
            "SENTINEL_RELEASE_K": 4,
        },
    }


def approach_block(positions, oid="a"):
    """One object approaching the ego head-on along +x, one position per frame."""
    frames = []
    for idx, x in enumerate(positions):
        frames.append(
            frame(idx, objs=[[float(x), 0.0, 1.0, 1.0, 0.0]], scores=[0.9], object_ids=[oid])
        )
    return {"frames": frames}


def test_iter44_neutral_cells_replay_identically_to_iter42():
    module = load_module()
    iter42 = module.load_module(module.ITER42_ANALYZER, "iter42_for_test")
    block = approach_block([10.0, 10.0, 8.0, 6.0, 6.0, 6.0])
    raw = iter42.replay_block(block)
    for kind, _, param in module.NEUTRAL_CELLS:
        smoothed = module.replay_block_smoothed(iter42, block, kind, param)
        assert smoothed == raw


def test_iter44_fd_k2_suppresses_a_single_frame_position_jump():
    module = load_module()
    iter42 = module.load_module(module.ITER42_ANALYZER, "iter42_for_test")
    # Stationary object at 10 m, then a 2 m inward jump: the raw one-frame estimator reads
    # 4 m/s closing (TTC 2.0 s < 2.5 -> fires); FD-2 reads 2 m/s (< MIN_CLOSING 3.0 -> holds).
    block = approach_block([10.0, 10.0, 8.0])
    raw = iter42.replay_block(block)
    assert raw[2]["fired"] is True
    fd2 = module.replay_block_smoothed(iter42, block, "fd", 2)
    assert fd2[2]["fired"] is False


def test_iter44_ema_smooths_velocity_and_alpha_one_is_raw():
    module = load_module()
    iter42 = module.load_module(module.ITER42_ANALYZER, "iter42_for_test")
    block = approach_block([10.0, 10.0, 8.0])
    ema_raw = module.replay_block_smoothed(iter42, block, "ema", 1.0)
    assert ema_raw[2]["fired"] is True
    # alpha=0.5 halves the jump velocity (previous smoothed velocity is 0): 2 m/s -> holds.
    ema_half = module.replay_block_smoothed(iter42, block, "ema", 0.5)
    assert ema_half[2]["fired"] is False


def test_iter44_all_estimators_equal_raw_on_constant_velocity_motion():
    module = load_module()
    iter42 = module.load_module(module.ITER42_ANALYZER, "iter42_for_test")
    # Genuine sustained approach at a constant 4 m/s: every average over history equals the
    # instantaneous velocity, so all four verdict estimators replay identically to the raw
    # rule — smoothing costs nothing on exactly linear tracks (raw fires at frame 3, TTC 2.0 s).
    block = approach_block([14.0, 12.0, 10.0, 8.0, 6.0])
    raw = iter42.replay_block(block)
    assert raw[3]["fired"] is True
    for kind, _, param in module.ESTIMATOR_CELLS:
        smoothed = module.replay_block_smoothed(iter42, block, kind, param)
        assert smoothed == raw


def test_iter44_identity_break_clears_estimator_state():
    module = load_module()
    iter42 = module.load_module(module.ITER42_ANALYZER, "iter42_for_test")
    # The object misses frame 2 entirely; on reappearance velocity restarts at zero for both
    # the raw rule and every smoothed estimator (state lifetime semantics unchanged).
    frames = [
        frame(0, objs=[[14.0, 0.0, 1.0, 1.0, 0.0]], scores=[0.9], object_ids=["a"]),
        frame(1, objs=[[12.0, 0.0, 1.0, 1.0, 0.0]], scores=[0.9], object_ids=["a"]),
        frame(2, objs=[], scores=[], object_ids=[]),
        frame(3, objs=[[8.0, 0.0, 1.0, 1.0, 0.0]], scores=[0.9], object_ids=["a"]),
    ]
    block = {"frames": frames}
    raw = iter42.replay_block(block)
    for kind, _, param in [("fd", "fd_k3", 3), ("ema", "ema_a0p3", 0.3)]:
        smoothed = module.replay_block_smoothed(iter42, block, kind, param)
        assert smoothed[3]["fired"] == raw[3]["fired"]
        assert smoothed[3]["min_ttc"] == raw[3]["min_ttc"]


def test_iter44_frozen_grids_match_the_preregistration():
    module = load_module()
    assert module.RUN_ID == "iter44-velocity-smoothing-v1"
    assert [label for _, label, _ in module.ESTIMATOR_CELLS] == [
        "fd_k2",
        "fd_k3",
        "ema_a0p5",
        "ema_a0p3",
    ]
    assert [(f, level) for f, level, _ in module.V2_CELLS] == [
        ("jitter", "sigma_0p05"),
        ("jitter", "sigma_0p10"),
    ]
    assert {f for f, _, _ in module.V3_CELLS} == {"dropout", "score", "churn"}
    assert module.FIDELITY_BARS == {
        "retention_min": 225,
        "new_interventions_max": 4,
        "median_delay_max_frames": 1.0,
        "delay_gt2_fraction_max": 0.05,
        "brake_total_min": 1085,
        "brake_total_max": 1325,
    }
    assert module.DETERMINISM_GUARD == ("fd_k2", "jitter", "sigma_0p10")


def test_iter44_classify_fidelity_bars():
    module = load_module()
    passing = {
        "retained_interventions": 230,
        "new_interventions": 0,
        "median_first_brake_delay_frames": 0,
        "delay_gt2_fraction": 0.0,
        "brake_frames": 1205,
    }
    verdict = module.classify_fidelity(passing)
    assert verdict["classification"] == "PASS"
    assert verdict["failed_bars"] == []

    failing = {
        "retained_interventions": 224,
        "new_interventions": 5,
        "median_first_brake_delay_frames": 2,
        "delay_gt2_fraction": 0.06,
        "brake_frames": 1400,
    }
    verdict = module.classify_fidelity(failing)
    assert verdict["classification"] == "FAIL"
    assert len(verdict["failed_bars"]) == 5


def test_iter44_metrics_measure_delay_against_the_online_stream():
    module = load_module()
    iter42 = module.load_module(module.ITER42_ANALYZER, "iter42_for_test")
    iter43 = module.load_module(module.ITER43_ANALYZER, "iter43_for_test")
    # Online: a one-frame jump fires at frame 2 (annotate online decisions from the raw rule);
    # FD-2 holds through the jump, then fires at frame 3 when the approach is sustained.
    block = approach_block([10.0, 10.0, 8.0, 6.0, 4.0])
    raw = iter42.replay_block(block)
    frames = [{**f, **r} for f, r in zip(block["frames"], raw)]
    blocks = [{"frames": frames}]
    metrics = module.replay_metrics_smoothed(
        iter42, iter43, blocks, [("stationary", "0099")], "fd", 2, None, "unperturbed", 0.0
    )
    assert metrics["retained_interventions"] == 1
    assert metrics["new_interventions"] == 0
    assert metrics["median_first_brake_delay_frames"] == 1
    assert metrics["brake_flips"] == 1


def test_iter44_hypothesis_freezes_bars_verdicts_and_seed_reuse():
    text = HYPOTHESIS.read_text()
    assert "iter44-velocity-smoothing-v1" in text
    assert "iter43-object-stream-perturbation-v1" in text
    assert "VELOCITY_SMOOTHING_REPAIR_PASS" in text
    assert "VELOCITY_SMOOTHING_TRADEOFF_NULL" in text
    assert "VELOCITY_SMOOTHING_NO_REPAIR_NULL" in text
    assert "VELOCITY_SMOOTHING_IDENTITY_NULL" in text
    assert "`k ∈ {2, 3}`" in text
    assert "`alpha ∈ {0.5, 0.3}`" in text
    assert "225/230" in text
    assert "4/170" in text
    assert "[1085, 1325]" in text
    assert "decision-replay" in text
