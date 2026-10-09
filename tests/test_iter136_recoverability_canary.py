"""Known bads and a stubbed driver integration; no driving outcome claims."""

import ast
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import pickle
from types import SimpleNamespace

import numpy as np
import pytest

from experiments.iter136_hugsim_recoverability_canary import instrument_driver as driver
from experiments.iter136_hugsim_recoverability_canary import independent_reference_check as independent
from experiments.iter136_hugsim_recoverability_canary import inspect_host
from experiments.iter136_hugsim_recoverability_canary import probe_reset as reset
from experiments.iter136_hugsim_recoverability_canary import replay_trace as trace


ROOT = Path(__file__).resolve().parents[1] / "experiments/iter136_hugsim_recoverability_canary"


def identity():
    return {"case": "scene-0411-hard-00", "hugsim_commit": reset.HUGSIM_COMMIT,
            "uniad_commit": "5fb279e39912a5ac7f58e00d56b065cadcd0a749",
            "scenario_sha256": "9f38bbdcdc49fe6ac5274a967b9a209417d621f67060357b97deacb887cf67a9",
            "checkpoint_sha256": "0ad0c2f5dc9788a41c313305779ea49346aeb742d1f6bb5ad25c46f9beffc990",
            "client_sha256": "a"*64, "driver_sha256": "b"*64,
            "simulator_seed": 136, "client_seed": 0}


def state(t):
    return {"timestamp": t, "ego_pos": [t, 0.0, 0.0], "ego_rot": [0.0]*3,
            "ego_velo": 1.0, "ego_steer": 0.0, "accelerate": 0.0, "steer_rate": 0.0,
            "command": 2, "ego_box": [0.0]*7, "obj_boxes": [[1.0]*7]}


def fixture(arm="reference", onset=None, frames=10, reason="collision"):
    rows = [{"schema": trace.SCHEMA, "identity": identity(), "arm": arm, "stop_at": onset}]
    for i in range(frames):
        incoming = [[0.0, 1.0]]*6
        last = i == frames-1
        rows.append({"frame": i, "time": i*0.25, "observation_sha256": "c"*64,
                     "before": state(i*0.25), "after": state((i+1)*0.25),
                     "incoming_plan": incoming,
                     "executed_plan": [[0.0, 0.0]]*6 if onset is not None and i*0.25 >= onset
                     else incoming,
                     "control": [0.0, 0.0], "terminated": last and reason != "truncated",
                     "truncated": last and reason == "truncated",
                     "collision": last and reason == "collision",
                     "route_completion": 1.0 if last and reason == "route_complete" else 0.5})
    rows.append({"end": "completed", "frames": frames, "reason": reason})
    return rows


def test_exact_pinned_reset_exposes_state_leak():
    result = reset.probe()
    assert result["repeated_reset_equal"] is False
    assert result["steering_and_control_history_retained"] is True
    assert result["seed_parameter_read_by_method"] is False
    assert result["first_reset"][1]["actor_update_count"] == 1
    assert result["second_reset"][1]["actor_update_count"] == 2
    assert result["live_simulation_observed"] is False


def test_pinned_reset_rejects_changed_bytes_even_with_rewritten_inventory(tmp_path):
    inventory = json.loads((ROOT / "proof/source_inventory.json").read_text())
    entry = next(r for r in inventory if r["path"] == "sim/hugsim_env/envs/hug_sim.py")
    entry["retained_path"] = "changed.txt"
    data = b"def changed(): pass\n"
    entry["sha256"] = hashlib.sha256(data).hexdigest()
    (tmp_path / "changed.txt").write_bytes(data)
    (tmp_path / "source_inventory.json").write_text(json.dumps([entry]))
    with pytest.raises(ValueError, match="source bytes"):
        reset.load_reset(tmp_path)


def test_exact_reference_and_only_registered_absolute_tolerance():
    a, b = fixture(), fixture()
    assert trace.compare(a, b)["status"] == "REPLAY_MATCHED"
    b[1]["control"][0] = 0.5e-6
    assert trace.compare(a, b)["status"] == "REPLAY_MATCHED"
    b[1]["control"][0] = 2e-6
    assert trace.compare(a, b)["status"] == "REPLAY_DIVERGED"


@pytest.mark.parametrize("mutation", [
    lambda r: r[1].update(frame=1),
    lambda r: r.pop(2),
    lambda r: r[1]["control"].__setitem__(0, float("nan")),
    lambda r: r[1]["before"].update(ego_pos=None),
    lambda r: r[1].update(time=0.25),
    lambda r: r[0]["identity"].update(simulator_seed=True),
    lambda r: r[0]["identity"].update(hugsim_commit="0"*40),
    lambda r: r[-1].update(reason="route_complete"),
    lambda r: r[1].update(terminated=True),
    lambda r: r[2]["before"].update(ego_velo=99),
    lambda r: r[1].update(collision=0),
    lambda r: r[1].update(executed_plan=[[0.0, 0.0]]*6),
    lambda r: r[0].update(arm="stop", stop_at=1.0),
])
def test_malformed_or_unregistered_trace_rejected(mutation):
    rows = fixture()
    mutation(rows)
    with pytest.raises(ValueError):
        trace.validate(rows)


def test_observation_and_source_changes_are_detected():
    a, b = fixture(), fixture()
    b[1]["observation_sha256"] = "e"*64
    assert trace.compare(a, b)["status"] == "REPLAY_DIVERGED"
    b = fixture()
    b[0]["identity"]["client_sha256"] = "f"*64
    assert trace.compare(a, b)["status"] == "invalid"


def test_onset_observation_is_in_prefix_and_post_onset_change_is_allowed():
    reference = fixture()
    branch = fixture("stop", 2.0, reason="route_complete")
    branch[9]["observation_sha256"] = "e"*64  # Decision at t=2.0 must match.
    assert trace.compare(reference, branch)["status"] == "invalid"
    branch[9]["observation_sha256"] = "c"*64
    branch[10]["observation_sha256"] = "e"*64
    assert trace.compare(reference, branch)["status"] == "supported"


def test_unobserved_grid_point_is_not_an_unsuccessful_intervention():
    result = trace.compare(fixture(), fixture("stop", 4.0))
    assert result["status"] == "unobserved"


@pytest.mark.parametrize("reason", ["other_termination", "truncated", "collision"])
def test_terminal_without_prevention_cannot_pass(reason):
    result = trace.compare(fixture(), fixture("stop", 0.0, frames=2, reason=reason))
    assert result["status"] == "not_demonstrated"
    assert result["collision_avoided"] is False


def test_no_collision_reference_closes_target():
    result = trace.compare(fixture(reason="route_complete"),
                           fixture("stop", 0.0, reason="route_complete"))
    assert result["status"] == "NO_RECOVERABILITY_TARGET"


def test_loader_rejects_truncation_duplicate_keys_and_nonfinite(tmp_path):
    path = tmp_path / "trace.jsonl"
    data = b"\n".join(trace.canonical(r) for r in fixture()) + b"\n"
    path.write_bytes(data)
    assert trace.load_trace(path) == fixture()
    for bad in (data[:-1], data.replace(b'"frame":0', b'"frame":0,"frame":0'),
                data.replace(b'"time":0.0', b'"time":NaN')):
        path.write_bytes(bad)
        with pytest.raises(ValueError):
            trace.load_trace(path)
        with pytest.raises(ValueError):
            independent.read(path)


def test_readers_reject_symlink_and_oversized_input(tmp_path):
    target, link = tmp_path / "target", tmp_path / "link"
    target.write_bytes(b"{}\n")
    link.symlink_to(target)
    for reader in (trace.load_trace, independent.read):
        with pytest.raises(ValueError):
            reader(link)
    with target.open("wb") as stream:
        stream.truncate(trace.MAX_BYTES + 1)
    for reader in (trace.load_trace, independent.read):
        with pytest.raises(ValueError):
            reader(target)


def test_observation_hash_covers_each_modality_and_shape():
    obs = {k: {"front": np.zeros((2, 2), dtype=np.float32)}
           for k in ("rgb", "semantic", "depth")}
    original = trace.observation_hash(obs)
    for key in obs:
        changed = deepcopy(obs)
        changed[key]["front"][0, 0] = 1
        assert trace.observation_hash(changed) != original
    obs["depth"]["front"] = np.zeros((4, 1), dtype=np.float32)
    assert trace.observation_hash(obs) != original
    obs["depth"]["front"][0, 0] = np.nan
    with pytest.raises(ValueError, match="nonfinite observation"):
        trace.observation_hash(obs)


@pytest.mark.parametrize("value", [None, 0, 1, "false", []])
def test_missing_or_unparseable_outcome_is_not_false(value):
    with pytest.raises(ValueError, match="non-Boolean"):
        trace._boolean(value)


def test_driver_hash_guard_and_compile():
    raw = (ROOT / "proof/source/HUGSIM/closed_loop.py.txt").read_bytes()
    generated = driver.instrument(raw)
    compile(generated, "driver.py", "exec")
    assert generated.count(b"env.reset()") == raw.count(b"env.reset()") == 2
    with pytest.raises(ValueError, match="hash mismatch"):
        driver.instrument(raw + b"\n")


def test_host_inventory_rejects_other_hosts(monkeypatch):
    monkeypatch.setattr(inspect_host.socket, "gethostname", lambda: "other-host")
    with pytest.raises(ValueError, match="identity"):
        inspect_host.inventory()


def test_host_missing_asset_is_unknown_and_changed_asset_rejected(tmp_path):
    p = tmp_path / "asset"
    assert inspect_host.file_record(str(p), "a"*64)["sha256"] is None
    p.write_bytes(b"wrong data")
    assert inspect_host.file_record(str(p), "a"*64)["status"] == "mismatch"


def test_separate_decimal_checker_agrees_on_known_bads(tmp_path):
    a, b = tmp_path / "a.jsonl", tmp_path / "b.jsonl"
    a.write_bytes(b"\n".join(trace.canonical(r) for r in fixture()) + b"\n")
    for change, expected in ((None, True), ("control", False), ("observation_sha256", False),
                             ("client_sha256", False)):
        rows = fixture()
        if change == "control":
            rows[1][change][0] = 2e-6
        elif change == "observation_sha256":
            rows[1][change] = "e"*64
        elif change == "client_sha256":
            rows[0]["identity"][change] = "e"*64
        b.write_bytes(b"\n".join(trace.canonical(r) for r in rows) + b"\n")
        assert independent.check(a, b)["matched"] is expected
        assert (trace.compare(trace.load_trace(a), trace.load_trace(b))["status"]
                == "REPLAY_MATCHED") is expected


@pytest.mark.parametrize("onset", ["reference", "0"])
def test_instrumented_driver_runs_through_stub_environment(tmp_path, monkeypatch, onset):
    raw = (ROOT / "proof/source/HUGSIM/closed_loop.py.txt").read_bytes()
    generated = driver.instrument(raw)
    script = tmp_path / "driver.py"
    script.write_bytes(generated)
    meta = identity()
    meta["driver_sha256"] = hashlib.sha256(generated).hexdigest()
    metadata = tmp_path / "identity.json"
    metadata.write_text(json.dumps(meta))
    monkeypatch.setenv("SENTINEL_I136_IDENTITY", str(metadata))
    monkeypatch.setenv("SENTINEL_I136_STOP_AT", onset)
    obs = {key: {"front": np.zeros((2, 2), dtype=np.float32)}
           for key in ("rgb", "semantic", "depth")}
    calls = []

    def reset_env():
        calls.append("reset")
        return obs, state(0.0)

    def step(action):
        calls.append(action)
        info = state(0.25)
        info.update(rc=1.0, collision=False)
        return obs, 0, True, False, info

    env = SimpleNamespace(reset=reset_env, step=step)
    (tmp_path / "obs_pipe").touch()
    (tmp_path / "plan_pipe").write_bytes(pickle.dumps(np.array([[0.0, 1.0]]*6)))
    module = ast.parse(generated)
    function = next(n for n in module.body if isinstance(n, ast.FunctionDef)
                    and n.name == "create_gym_env")
    namespace = {
        "__file__": str(script), "Recorder": trace.Recorder, "os": os, "pickle": pickle,
        "json": json, "np": np, "gymnasium": SimpleNamespace(make=lambda *a, **k: env),
        "traj2control": lambda *a: (0.0, 0.0), "traj_transform_to_global": lambda *a: [],
        "to_video": lambda *a: None, "hugsim_evaluate": lambda *a: {},
        "o3d": SimpleNamespace(io=SimpleNamespace(read_point_cloud=lambda p:
                              SimpleNamespace(points=np.zeros((1, 3))))),
    }
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(script), "exec"), namespace)
    namespace["create_gym_env"]({}, str(tmp_path))
    rows = trace.load_trace(tmp_path / "iter136_trace.jsonl")
    assert calls[:2] == ["reset", "reset"]
    assert rows[-1]["reason"] == "route_complete"
    assert rows[1]["time"] == 0.0 and rows[1]["after"]["timestamp"] == 0.25
    expected = [[0.0, 0.0]]*6 if onset == "0" else [[0.0, 1.0]]*6
    assert rows[1]["executed_plan"] == expected
