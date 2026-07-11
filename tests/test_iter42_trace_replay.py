from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "experiments/iter42_exact_trace_replay_support/analyze_trace_replay.py"
PATCH = ROOT / "experiments/iter42_exact_trace_replay_support/server_patch_union_trace.py"
RUN = ROOT / "experiments/iter42_exact_trace_replay_support/iter42_trace_run.sh"


def load_module():
    spec = importlib.util.spec_from_file_location("iter42_trace_replay", SCRIPT)
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


def params(release_k=4):
    return {
        "SENTINEL_MIN_SCORE": 0.3,
        "SENTINEL_MAXGAP": 30.0,
        "SENTINEL_CPA_MARGIN": 1.5,
        "SENTINEL_TTC": 2.5,
        "SENTINEL_MIN_CLOSING": 3.0,
        "SENTINEL_RELEASE_K": release_k,
    }


def frame(idx, *, objs, scores, fired, brake, release, pre_braking, pre_clear, post_braking, post_clear):
    return {
        "trace_version": "iter42_exact_trace_v1",
        "run": 0,
        "frame_index": idx,
        "ts": idx * 500000,
        "traj": [[1.0, 0.0]],
        "objs": objs,
        "scores": scores,
        "object_ids": [],
        "ego2world": identity_pose(),
        "params": params(release_k=2),
        "pre_braking": pre_braking,
        "pre_clear": pre_clear,
        "min_cpa": 0.0 if fired else 1e9,
        "min_ttc": 1e9,
        "fired": fired,
        "post_braking": post_braking,
        "post_clear": post_clear,
        "brake": brake,
        "release": release,
    }


def test_iter42_replay_block_reproduces_fire_brake_release_sequence():
    module = load_module()
    block = {
        "frames": [
            frame(
                0,
                objs=[[1.0, 0.0, 1.0, 1.0, 0.0]],
                scores=[1.0],
                fired=True,
                brake=True,
                release=False,
                pre_braking=False,
                pre_clear=0,
                post_braking=True,
                post_clear=0,
            ),
            frame(
                1,
                objs=[],
                scores=[],
                fired=False,
                brake=True,
                release=False,
                pre_braking=True,
                pre_clear=0,
                post_braking=True,
                post_clear=1,
            ),
            frame(
                2,
                objs=[],
                scores=[],
                fired=False,
                brake=False,
                release=True,
                pre_braking=True,
                pre_clear=1,
                post_braking=False,
                post_clear=0,
            ),
        ]
    }
    old_expected = module.EXPECTED.copy()
    module.EXPECTED.update({"brake_frames": 2, "release_frames": 1, "intervention_episodes": 1})
    try:
        report = module.compare_replay([block])
    finally:
        module.EXPECTED.clear()
        module.EXPECTED.update(old_expected)

    assert report["pass"]
    assert report["replay_brake_frames"] == 2
    assert report["replay_release_frames"] == 1


def test_iter42_compare_replay_flags_logged_decision_mismatch():
    module = load_module()
    row = frame(
        0,
        objs=[[1.0, 0.0, 1.0, 1.0, 0.0]],
        scores=[1.0],
        fired=False,
        brake=False,
        release=False,
        pre_braking=False,
        pre_clear=0,
        post_braking=False,
        post_clear=0,
    )
    old_expected = module.EXPECTED.copy()
    module.EXPECTED.update({"brake_frames": 1, "release_frames": 0, "intervention_episodes": 1})
    try:
        report = module.compare_replay([{"frames": [row]}])
    finally:
        module.EXPECTED.clear()
        module.EXPECTED.update(old_expected)

    assert not report["pass"]
    assert "fired" in report["mismatch_examples"][0]["mismatched_fields"]
    assert "brake" in report["mismatch_examples"][0]["mismatched_fields"]


def test_iter42_field_failures_reject_bad_pose_and_forbidden_token():
    module = load_module()
    row = frame(
        0,
        objs=[],
        scores=[],
        fired=False,
        brake=False,
        release=False,
        pre_braking=False,
        pre_clear=0,
        post_braking=False,
        post_clear=0,
    )
    row["ego2world"] = [[1.0]]
    row["sample_token"] = "forbidden"

    failures = module.field_failures(row)

    assert "bad_ego2world" in failures
    assert "forbidden_field_sample_token" in failures


def test_iter42_parse_trace_blocks_and_pair_order(tmp_path):
    module = load_module()
    trace = tmp_path / "trace.jsonl"
    rows = [
        {"trace_version": "iter42_exact_trace_v1", "reset": True, "run": 0},
        frame(
            0,
            objs=[],
            scores=[],
            fired=False,
            brake=False,
            release=False,
            pre_braking=False,
            pre_clear=0,
            post_braking=False,
            post_clear=0,
        ),
    ]
    trace.write_text("\n".join(json.dumps(row) for row in rows) + "\n")
    log = tmp_path / "run.log"
    log.write_text("##### I42PAIR trace stationary 0099 #####\n")

    blocks = module.parse_trace_blocks(trace)

    assert len(blocks) == 1
    assert blocks[0]["reset_run"] == 0
    assert blocks[0]["frames"][0]["frame_index"] == 0
    assert module.parse_pair_order(log) == [("stationary", "0099")]


def test_iter42_patch_and_run_script_static_constraints():
    patch = PATCH.read_text()
    run = RUN.read_text()

    assert "ITER42_UNION_TRACE_PATCHED" in patch
    assert "iter42_exact_trace_v1" in patch
    assert "ego2world" in patch
    assert "SENTINEL_RELEASE_K" in patch
    assert "for arm in" not in run
    assert "SENTINEL_ENABLED=0" not in run
    assert "SENTINEL_ENABLED=1" in run
    assert "I42_TRACE_ALL_DONE" in run
