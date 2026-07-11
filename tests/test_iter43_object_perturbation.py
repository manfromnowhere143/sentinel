from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "experiments/iter43_object_stream_perturbation_gate/analyze_object_perturbation.py"
HYPOTHESIS = ROOT / "experiments/iter43_object_stream_perturbation_gate/HYPOTHESIS.md"


def load_module():
    spec = importlib.util.spec_from_file_location("iter43_object_perturbation", SCRIPT)
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


def test_iter43_zero_strength_perturbation_is_identity_on_decisions():
    module = load_module()
    iter42 = module.load_iter42_module()
    original = frame(0, objs=[[1.0, 0.5, 1.0, 1.0, 0.0], [4.0, -2.0, 1.0, 1.0, 0.0]], scores=[0.9, 0.6])
    block = {"frames": [original]}
    perturbed = module.perturb_block(block, None, "zero", 0.0, "stationary", "0099")
    assert perturbed["frames"][0]["objs"] == [[1.0, 0.5, 1.0, 1.0, 0.0], [4.0, -2.0, 1.0, 1.0, 0.0]]
    assert perturbed["frames"][0]["scores"] == [0.9, 0.6]
    # Materialized identities must equal the iter42 index fallback.
    assert perturbed["frames"][0]["object_ids"] == ["idx_0", "idx_1"]
    raw_replay = iter42.replay_block(block)
    zero_replay = iter42.replay_block(perturbed)
    assert raw_replay == zero_replay


def test_iter43_grid_and_seed_are_frozen():
    module = load_module()
    assert module.SEED == "iter43-object-stream-perturbation-v1"
    assert len(module.GRID) == 14
    families = {family for family, _, _ in module.GRID}
    assert families == {"jitter", "dropout", "score", "churn"}
    assert len(module.MILD_CELLS) == 5
    for cell in module.MILD_CELLS:
        assert cell in {(family, level) for family, level, _ in module.GRID}


def test_iter43_jitter_is_deterministic_and_bounded_in_effect():
    module = load_module()
    base = frame(3, objs=[[2.0, 1.0, 1.0, 1.0, 0.0]], scores=[0.8])
    a = module.perturb_frame(dict(base), "jitter", "sigma_0p25", 0.25, "side", "0108")
    b = module.perturb_frame(dict(base), "jitter", "sigma_0p25", 0.25, "side", "0108")
    assert a["objs"] == b["objs"]
    assert a["objs"][0][:2] != [2.0, 1.0]
    # Non-position fields untouched.
    assert a["objs"][0][2:] == [1.0, 1.0, 0.0]
    assert a["scores"] == [0.8]
    other_frame = module.perturb_frame(
        {**base, "frame_index": 4}, "jitter", "sigma_0p25", 0.25, "side", "0108"
    )
    assert other_frame["objs"] != a["objs"]


def test_iter43_dropout_removes_object_without_renumbering_survivors():
    module = load_module()
    base = frame(1, objs=[[float(i), 0.0, 1.0, 1.0, 0.0] for i in range(30)], scores=[0.9] * 30)
    perturbed = module.perturb_frame(dict(base), "dropout", "p_0p20", 0.20, "frontal", "0103")
    assert 0 < len(perturbed["objs"]) < 30
    assert len(perturbed["objs"]) == len(perturbed["scores"]) == len(perturbed["object_ids"])
    # Survivors keep their original materialized identity (no index renumbering).
    for obj, oid in zip(perturbed["objs"], perturbed["object_ids"]):
        assert oid == f"idx_{int(obj[0])}"


def test_iter43_score_attenuation_scales_scores_only():
    module = load_module()
    base = frame(2, objs=[[1.0, 0.0, 1.0, 1.0, 0.0]], scores=[0.5])
    perturbed = module.perturb_frame(dict(base), "score", "f_0p60", 0.60, "stationary", "0101")
    assert perturbed["scores"] == [0.5 * 0.60]
    assert perturbed["objs"] == [[1.0, 0.0, 1.0, 1.0, 0.0]]


def test_iter43_churn_at_full_rate_gives_unique_per_frame_identities():
    module = load_module()
    base = frame(5, objs=[[1.0, 0.0, 1.0, 1.0, 0.0], [2.0, 0.0, 1.0, 1.0, 0.0]], scores=[0.9, 0.9])
    perturbed = module.perturb_frame(dict(base), "churn", "p_1p00", 1.00, "side", "0110")
    assert all(str(oid).startswith("churn_") for oid in perturbed["object_ids"])
    assert len(set(perturbed["object_ids"])) == 2


def test_iter43_classify_cell_bars():
    module = load_module()
    stable = {
        "retained_interventions": 230,
        "new_interventions": 0,
        "median_first_brake_delay_frames": 0,
        "delay_gt2_fraction": 0.0,
        "brake_frames": 1205,
    }
    verdict = module.classify_cell(stable)
    assert verdict["classification"] == "STABLE"
    assert verdict["failed_bars"] == []

    fragile = {
        "retained_interventions": 200,
        "new_interventions": 20,
        "median_first_brake_delay_frames": 3,
        "delay_gt2_fraction": 0.5,
        "brake_frames": 500,
    }
    verdict = module.classify_cell(fragile)
    assert verdict["classification"] == "FRAGILE"
    assert len(verdict["failed_bars"]) == 5

    no_retained = {
        "retained_interventions": 0,
        "new_interventions": 0,
        "median_first_brake_delay_frames": None,
        "delay_gt2_fraction": None,
        "brake_frames": 0,
    }
    verdict = module.classify_cell(no_retained)
    assert verdict["classification"] == "FRAGILE"
    assert "median_delay_undefined_no_retained_interventions" in verdict["failed_bars"]


def test_iter43_replay_metrics_detects_lost_and_new_interventions():
    module = load_module()
    iter42 = module.load_iter42_module()
    # Block with one close firing object online; score attenuation to 0.60 pushes 0.45 -> 0.27
    # below MIN_SCORE and removes the intervention.
    firing = frame(0, objs=[[0.5, 0.0, 1.0, 1.0, 0.0]], scores=[0.45])
    replayed_online = iter42.replay_block({"frames": [firing]})
    assert replayed_online[0]["brake"] is True
    online_frame = {**firing, **replayed_online[0]}
    blocks = [{"frames": [online_frame]}]
    metrics = module.replay_metrics(iter42, blocks, [("stationary", "0099")], "score", "f_0p60", 0.60)
    assert metrics["retained_interventions"] == 0
    assert metrics["lost_interventions"] == 1
    assert metrics["brake_frames"] == 0
    assert metrics["brake_flips"] == 1


def test_iter43_hypothesis_precedes_tooling_and_freezes_bars():
    text = HYPOTHESIS.read_text()
    assert "iter43-object-stream-perturbation-v1" in text
    assert "OBJECT_PERTURBATION_MILD_STABLE_PASS" in text
    assert "OBJECT_PERTURBATION_MILD_FRAGILE" in text
    assert "[1025, 1385]" in text
    assert "219/230" in text
    assert "8/170" in text
    assert "decision-flip sensitivity" in text
