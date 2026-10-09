"""Live adapter linkage, independent known-bads and resource gates; stub simulation only."""

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

from experiments.iter136_hugsim_recoverability_canary import replay_trace as legacy
from experiments.iter137_controller_execution_contract.verify import Replay
from experiments.iter138_numerical_live_replay import (
    instrument,
    live_trace,
    verify_live,
    run_episode,
    audit137,
)

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / "experiments/iter136_hugsim_recoverability_canary"


def state(t):
    return dict(
        timestamp=t,
        ego_pos=[t, 0.0, 0.0],
        ego_rot=[0.0] * 3,
        ego_velo=1.0,
        ego_steer=0.0,
        accelerate=0.0,
        steer_rate=0.0,
        command=2,
        ego_box=[0.0] * 7,
        obj_boxes=[[1.0] * 7],
    )


def run_stub(tmp_path, monkeypatch, plan):
    raw = (OLD / "proof/source/HUGSIM/closed_loop.py.txt").read_bytes()
    generated = instrument.instrument(raw)
    script = tmp_path / "driver.py"
    script.write_bytes(generated)
    identity = json.loads((OLD / "proof/runtime_v2/identity.json.txt").read_text())
    identity["driver_sha256"] = hashlib.sha256(generated).hexdigest()
    (tmp_path / "identity.json").write_text(json.dumps(identity))
    monkeypatch.setenv("SENTINEL_I138_IDENTITY", str(tmp_path / "identity.json"))
    monkeypatch.setattr(live_trace, "threadpool_info", lambda: [dict(num_threads=1)])
    obs = {k: {"front": np.zeros((2, 2), dtype=np.float32)} for k in ("rgb", "semantic", "depth")}
    calls = []

    def reset():
        calls.append("reset")
        return obs, state(0.0)

    def step(action):
        calls.append(action)
        info = state(0.25)
        info.update(rc=1.0, collision=False)
        return obs, 0.0, True, False, info

    (tmp_path / "obs_pipe").touch()
    (tmp_path / "plan_pipe").write_bytes(pickle.dumps(plan))
    node = next(
        n
        for n in ast.parse(generated).body
        if isinstance(n, ast.FunctionDef) and n.name == "create_gym_env"
    )
    env = SimpleNamespace(reset=reset, step=step)
    ns = dict(
        __file__=str(script),
        Recorder=live_trace.Recorder,
        os=os,
        pickle=pickle,
        json=json,
        np=np,
        gymnasium=SimpleNamespace(make=lambda *a, **k: env),
        traj_transform_to_global=lambda *a: [],
        to_video=lambda *a: None,
        hugsim_evaluate=lambda *a: {},
        o3d=SimpleNamespace(
            io=SimpleNamespace(read_point_cloud=lambda p: SimpleNamespace(points=np.zeros((1, 3))))
        ),
    )
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(script), "exec"), ns)
    ns["create_gym_env"]({}, str(tmp_path))
    assert calls[:2] == ["reset", "reset"] and len(calls) == 3
    return (
        legacy.load_trace(tmp_path / "iter138_trace.jsonl"),
        verify_live.read_contract(tmp_path / "controller138.jsonl"),
        calls[-1],
    )


@pytest.fixture
def capture(tmp_path, monkeypatch):
    return run_stub(tmp_path, monkeypatch, np.array([[0.0, 1.0]] * 6, dtype="float32"))


@pytest.mark.parametrize("dtype", ["float32", "float64"])
def test_complete_stub_driver_and_source_replay(tmp_path, monkeypatch, dtype):
    d, c, action = run_stub(tmp_path, monkeypatch, np.array([[0.0, 1.0]] * 6, dtype=dtype))
    cases = verify_live.validate_linkage(d, c)
    assert c[1]["receipt"]["numerical"]["input"]["plan"]["dtype"] == np.dtype(dtype).str
    Replay().check(c[1]["receipt"], cases[0], "numerical")
    assert d[1]["control"] == [action["acc"], action["steer_rate"]]
    assert c[-1] == dict(end="completed", frames=1)


@pytest.mark.parametrize(
    "bad",
    [
        "missing",
        "frame",
        "time",
        "dtype",
        "input",
        "state",
        "action",
        "mode",
        "config",
        "reason",
        "source",
        "complete_time",
        "client_time",
        "digest",
    ],
)
def test_linkage_and_independent_source_known_bads(capture, bad):
    d, c, _ = deepcopy(capture)
    row = c[1]
    if bad == "missing":
        c.pop(1)
    elif bad == "frame":
        row["frame"] = 1
    elif bad == "time":
        row["time"] = 0.25
    elif bad == "dtype":
        row["receipt"]["numerical"]["input"]["plan"]["dtype"] = "<f2"
    elif bad == "input":
        row["receipt"]["numerical"]["input"]["plan"]["values"][0][0] = 3.0
    elif bad == "state":
        row["receipt"]["numerical"]["input"]["velocity"] = 2.0
    elif bad == "action":
        d[1]["control"][0] += 1.0
    elif bad == "mode":
        row["receipt"]["mode"] = "timed"
    elif bad == "config":
        row["receipt"]["configuration"]["solver"]["max_solve_time"] = 0.05
    elif bad == "reason":
        row["receipt"]["numerical"]["stop_reason"] = "deadline"
    elif bad == "source":
        c[0]["controller_sha256"] = "0" * 64
    elif bad == "complete_time":
        row["complete_call_ns"] = 0
    elif bad == "client_time":
        row.pop("client_roundtrip_ns")
    elif bad == "digest":
        row["receipt"]["numerical_sha256"] = "0" * 64
    if bad == "reason":
        row["receipt"]["numerical_sha256"] = hashlib.sha256(
            legacy.canonical(row["receipt"]["numerical"])
        ).hexdigest()
    with pytest.raises(ValueError):
        cases = verify_live.validate_linkage(d, c)
        Replay().check(row["receipt"], cases[0], "numerical")


def test_exact_controller_repeat_gate(capture):
    _, c, _ = capture
    assert verify_live.compare_controller(c, c)["matched"]
    changed = deepcopy(c)
    changed[1]["receipt"]["numerical"]["control"][0] += 1e-12
    assert not verify_live.compare_controller(c, changed)["matched"]
    assert not verify_live.compare_controller(c, c[:-1])["matched"]


@pytest.mark.parametrize("plan", [np.zeros((6, 2), dtype="float16"), np.full((6, 2), np.nan)])
def test_failed_control_retained_before_actuation(tmp_path, monkeypatch, plan):
    with pytest.raises(ValueError, match="before actuation"):
        run_stub(tmp_path, monkeypatch, plan)
    rows = [json.loads(x) for x in (tmp_path / "controller138.jsonl").read_text().splitlines()]
    failure = rows[-1].get("receipt", rows[-1].get("input_failure"))
    assert failure["status"] == "failed" and failure["control"] is None
    assert len((tmp_path / "iter138_trace.jsonl").read_text().splitlines()) == 1


def test_source_mutation_rejected():
    with pytest.raises(ValueError):
        instrument.instrument((OLD / "proof/source/HUGSIM/closed_loop.py.txt").read_bytes() + b"\n")


@pytest.mark.parametrize("pools", [[], [dict(num_threads=2)]])
def test_loaded_threadpool_gate(pools):
    with pytest.raises(ValueError):
        live_trace.check_runtime(pools)


@pytest.mark.parametrize(
    "free,remaining,exists", [(99, 2000, False), (110, 1229, False), (110, 2000, True)]
)
def test_execution_budget(free, remaining, exists):
    with pytest.raises(ValueError):
        run_episode.check_budget(free, remaining, exists)


def test_failed_predecessor_blocks_b(tmp_path):
    with pytest.raises(ValueError):
        run_episode.predecessors("reference_b", tmp_path)
    a = tmp_path / "reference_a"
    a.mkdir()
    (a / "episode.json").write_text('{"returncode":1}')
    with pytest.raises(ValueError):
        run_episode.predecessors("reference_b", tmp_path)


@pytest.mark.parametrize("status", ["validated", "failed"])
def test_b_requires_independent_a_validation(tmp_path, monkeypatch, status):
    a = tmp_path / "reference_a"
    a.mkdir()
    (a / "episode.json").write_text('{"returncode":0}')
    monkeypatch.setattr(
        run_episode.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(
            returncode=0, stdout=json.dumps(dict(status=status)), stderr=""
        ),
    )
    if status == "failed":
        with pytest.raises(ValueError):
            run_episode.predecessors("reference_b", tmp_path)
    else:
        run_episode.predecessors("reference_b", tmp_path)


def test_audit137_recomputes_full_record():
    r = audit137.audit()
    assert r["all_reported_groups_match"] and r["numerical_identical_cases"] == 114
    assert r["timed_control_variable_cases"] == 114


def test_audit_quantile_uses_nearest_rank():
    assert audit137.quantile(list(range(1, 229))) == dict(p50=114, p95=217, p99=226, max=228)
