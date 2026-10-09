"""End-to-end stub action delivery and known-bads for the preregistered pulse contract."""

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

from experiments.iter137_controller_execution_contract.verify import Replay
from experiments.iter138_numerical_live_replay.verify_live import read_contract
from experiments.iter139_finite_pulse_recoverability import (
    independent,
    instrument,
    live_trace,
    run_episode,
    summarize,
    trace,
    verify_live,
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


def stub(folder, monkeypatch, arm, plan=None, count=26):
    folder.mkdir()
    source = instrument.instrument((OLD / "proof/source/HUGSIM/closed_loop.py.txt").read_bytes())
    driver = folder / "driver.py"
    driver.write_bytes(source)
    identity = json.loads((OLD / "proof/runtime_v2/identity.json.txt").read_text())
    identity["driver_sha256"] = hashlib.sha256(source).hexdigest()
    (folder / "identity.json").write_text(json.dumps(identity))
    monkeypatch.setenv("SENTINEL_I139_IDENTITY", str(folder / "identity.json"))
    monkeypatch.setenv("SENTINEL_I139_ARM", arm)
    monkeypatch.setattr(live_trace, "threadpool_info", lambda: [dict(num_threads=1)])
    obs = {k: {"front": np.zeros((2, 2), dtype="float32")} for k in ("rgb", "semantic", "depth")}
    actions = []
    resets = []

    def reset():
        resets.append(1)
        return obs, state(0.0)

    def step(action):
        actions.append(action)
        i = len(actions)
        info = state(i * 0.25)
        info.update(
            rc=1.02 if i == count and arm.startswith("pulse") else 0.2,
            collision=i == count and arm.startswith("reference"),
        )
        return obs, 0.0, i == count, False, info

    (folder / "obs_pipe").touch()
    if plan is None:
        plan = np.array([[0.0, 1.0]] * 6, dtype="float32")
    (folder / "plan_pipe").write_bytes(pickle.dumps(plan))
    node = next(
        n
        for n in ast.parse(source).body
        if isinstance(n, ast.FunctionDef) and n.name == "create_gym_env"
    )
    ns = dict(
        __file__=str(driver),
        Recorder=live_trace.Recorder,
        os=os,
        pickle=pickle,
        json=json,
        np=np,
        gymnasium=SimpleNamespace(make=lambda *a, **k: SimpleNamespace(reset=reset, step=step)),
        traj_transform_to_global=lambda *a: [],
        to_video=lambda *a: None,
        hugsim_evaluate=lambda *a: {},
        o3d=SimpleNamespace(
            io=SimpleNamespace(read_point_cloud=lambda p: SimpleNamespace(points=np.zeros((1, 3))))
        ),
    )
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(driver), "exec"), ns)
    ns["create_gym_env"]({}, str(folder))
    assert len(resets) == 2 and len(actions) == count
    driving = trace.load_trace(folder / "iter139_trace.jsonl")
    contract = read_contract(folder / "controller139.jsonl")
    decisions = [
        dict(
            trace_version="iter48_hugsim_union_v1",
            params=verify_live.PARAMS,
            frame_index=i,
            ts=i * 0.25,
            brake=False,
            traj=plan.tolist(),
        )
        for i in range(count)
    ]
    (folder / "sentinel_iter48_decisions.jsonl").write_text(
        "".join(json.dumps(d) + "\n" for d in decisions)
    )
    return driving, contract, actions


@pytest.fixture
def captured(tmp_path, monkeypatch):
    a = stub(tmp_path / "reference", monkeypatch, "reference_a")
    b = stub(tmp_path / "pulse", monkeypatch, "pulse_0_1")
    return a, b, tmp_path


@pytest.mark.parametrize("arm", list(trace.ARMS)[2:])
def test_full_driver_pulse_and_resumption(tmp_path, monkeypatch, arm):
    a, ca, _ = stub(tmp_path / "reference", monkeypatch, "reference_a")
    b, cb, actions = stub(tmp_path / "pulse", monkeypatch, arm)
    cases = verify_live.validate_linkage(b, cb)
    replay = Replay()
    for case, row, action in zip(cases, cb[1:-1], actions):
        replay.check(row["receipt"], case, "numerical")
        assert row["receipt"]["numerical"]["control"] == [action["acc"], action["steer_rate"]]
    assert verify_live.compare_prefix(a, b, ca, cb) == "matched"
    result = verify_live.outcomes(a, b)
    assert result["useful_recovery"] and result["complete_pulse_observed"]
    assert result["realized_override_frames"] == trace.ARMS[arm][1] * 4
    assert result["changed_plan_frames"] == result["realized_override_frames"]
    assert (
        independent.check(
            tmp_path / "reference/iter139_trace.jsonl", tmp_path / "pulse/iter139_trace.jsonl"
        )["outcomes"]
        == result
    )
    assert all(row["incoming_typed"]["dtype"] == "<f4" for row in cb[1:-1])


def test_reference_pair_and_monitor(captured):
    (a, ca, _), (_, _, _), _ = captured
    assert verify_live.compare_prefix(a, deepcopy(a), ca, deepcopy(ca)) == "matched"
    ds = [
        dict(
            trace_version="iter48_hugsim_union_v1",
            params=verify_live.PARAMS,
            frame_index=r["frame"],
            ts=r["time"],
            brake=False,
            traj=r["incoming_plan"],
        )
        for r in a[1:-1]
    ]
    assert verify_live.monitor_check(a, ds) == 0
    ds[0]["params"] = {}
    with pytest.raises(ValueError):
        verify_live.monitor_check(a, ds)


@pytest.mark.parametrize(
    "bad",
    [
        "onset",
        "duration",
        "early_release",
        "late_release",
        "progress",
        "missing_outcome",
        "false_terminal",
        "post_terminal",
    ],
)
def test_trace_known_bads(captured, bad):
    _, (b, _, _), folder = captured
    b = deepcopy(b)
    if bad == "onset":
        b[0]["onset"] = 0.25
    elif bad == "duration":
        b[0]["duration"] = 3
    elif bad == "early_release":
        b[4]["executed_plan"] = b[4]["incoming_plan"]
    elif bad == "late_release":
        b[5]["executed_plan"] = [[0.0, 0.0]] * 6
    elif bad == "progress":
        b[-2]["route_completion"] = 1.12
    elif bad == "missing_outcome":
        b[-2]["collision"] = None
    elif bad == "false_terminal":
        b[-2]["terminated"] = False
    elif bad == "post_terminal":
        b[1]["terminated"] = True
    with pytest.raises(ValueError):
        trace.validate(b)
    path = folder / "bad.jsonl"
    path.write_bytes(b"\n".join(trace.canonical(r) for r in b) + b"\n")
    with pytest.raises(ValueError):
        independent.read(path)


@pytest.mark.parametrize(
    "bad", ["missing", "time", "typed_bytes", "dtype", "active", "action", "duration"]
)
def test_controller_linkage_known_bads(captured, bad):
    _, (b, cb, _), _ = captured
    b = deepcopy(b)
    cb = deepcopy(cb)
    if bad == "missing":
        del cb[1]
    elif bad == "time":
        cb[1]["time"] = 1.0
    elif bad == "typed_bytes":
        cb[1]["incoming_typed"]["bytes_hex"] = "00"
    elif bad == "dtype":
        cb[1]["receipt"]["numerical"]["input"]["plan"]["dtype"] = "<f8"
    elif bad == "active":
        cb[1]["pulse_active"] = False
    elif bad == "action":
        b[1]["control"][0] += 1.0
    elif bad == "duration":
        cb[1]["complete_call_ns"] = -1
    with pytest.raises(ValueError):
        verify_live.validate_linkage(b, cb)


def test_first_action_input_and_runtime_divergence(captured):
    (a, ca, _), (b, cb, _), folder = captured
    b = deepcopy(b)
    b[1]["observation_sha256"] = "f" * 64
    with pytest.raises(ValueError, match="onset"):
        verify_live.compare_prefix(a, b, ca, cb)
    p = folder / "bad_prefix.jsonl"
    p.write_bytes(b"\n".join(trace.canonical(r) for r in b) + b"\n")
    with pytest.raises(ValueError, match="onset"):
        independent.check(folder / "reference/iter139_trace.jsonl", p)
    b = deepcopy(a)
    cb = deepcopy(ca)
    cb[0]["numpy"] = "different"
    with pytest.raises(ValueError, match="runtime"):
        verify_live.compare_prefix(a, b, ca, cb)


def shorten(rows, n, reason):
    rows = deepcopy(rows[: n + 1])
    last = rows[-1]
    last.update(
        collision=reason == "collision",
        terminated=reason != "truncated",
        truncated=reason == "truncated",
        route_completion=0.15,
    )
    rows.append(dict(end="completed", frames=n, reason=reason))
    return rows


@pytest.mark.parametrize("reason", ["collision", "truncated", "other_termination"])
def test_no_prevention_from_early_end_or_censoring(captured, reason):
    (a, _, _), (b, _, _), folder = captured
    b = shorten(b, 8, reason)
    trace.validate(b)
    o = verify_live.outcomes(a, b)
    assert not o["useful_recovery"] and o["hazard_progress"] is None
    assert o["collision_free_through_hazard"] is (False if reason == "collision" else None)
    p = folder / "short.jsonl"
    p.write_bytes(b"\n".join(trace.canonical(r) for r in b) + b"\n")
    assert independent.check(folder / "reference/iter139_trace.jsonl", p)["outcomes"] == o


def test_bounded_horizon_is_not_full_recovery(captured):
    (a, _, _), (b, _, _), folder = captured
    b = deepcopy(b)
    b[-2].update(route_completion=0.3, terminated=False, truncated=True)
    b[-1]["reason"] = "truncated"
    trace.validate(b)
    o = verify_live.outcomes(a, b)
    assert (
        o["collision_free_through_hazard"]
        and o["hazard_progress_bar_met"]
        and not o["useful_recovery"]
        and o["censored"]
    )
    p = folder / "censored.jsonl"
    p.write_bytes(b"\n".join(trace.canonical(r) for r in b) + b"\n")
    assert independent.check(folder / "reference/iter139_trace.jsonl", p)["outcomes"] == o


@pytest.mark.parametrize(
    "bad",
    [
        np.full((6, 2), np.nan, dtype="float32"),
        np.zeros((5, 2), dtype="float32"),
        np.zeros((6, 2), dtype="int32"),
    ],
)
def test_invalid_input_fails_before_actuation(tmp_path, monkeypatch, bad):
    folder = tmp_path / "invalid"
    with pytest.raises(ValueError, match="invalid planner input"):
        stub(folder, monkeypatch, "pulse_0_1", plan=bad)
    rows = [json.loads(x) for x in (folder / "controller139.jsonl").read_text().splitlines()]
    assert (
        rows[-1]["input_failure"]["status"] == "failed"
        and rows[-1]["input_failure"]["control"] is None
    )
    assert len((folder / "iter139_trace.jsonl").read_text().splitlines()) == 1


def test_zero_incoming_is_not_effective_dose(tmp_path, monkeypatch):
    b, cb, _ = stub(
        tmp_path / "zero", monkeypatch, "pulse_0_1", plan=np.zeros((6, 2), dtype="float32"), count=6
    )
    verify_live.validate_linkage(b, cb)
    active = [r for r in cb[1:-1] if r["pulse_active"]]
    assert len(active) == 4
    assert sum(r["incoming_plan"] != r["executed_plan"] for r in b[1:-1]) == 0


def test_grid_does_not_promote_partial_or_censored(captured):
    (a, _, _), (b, _, _), _ = captured
    o = verify_live.outcomes(a, b)
    reports = {
        "reference_b": dict(verdict="REPLAY_MATCHED"),
        "pulse_0_1": dict(status="validated", prefix="matched", outcomes=o),
    }
    assert summarize.summarize(reports)["verdict"] == "FINITE_PULSE_GRID_INCOMPLETE"
    for arm in list(trace.ARMS)[2:]:
        reports[arm] = dict(status="validated", prefix="matched", outcomes=deepcopy(o))
    assert summarize.summarize(reports)["status"] == "supported"
    for arm in list(trace.ARMS)[2:]:
        reports[arm]["outcomes"]["useful_recovery"] = False
    assert summarize.summarize(reports)["status"] == "null"
    reports["pulse_4_2"]["outcomes"]["censored"] = True
    assert summarize.summarize(reports)["status"] == "inconclusive"


@pytest.mark.parametrize(
    "free,remaining,exists", [(99, 1300, False), (101, 1229, False), (101, 1300, True)]
)
def test_resource_gate(free, remaining, exists):
    with pytest.raises(ValueError):
        run_episode.check_budget(free, remaining, exists)


def test_predecessor_identity_and_pair_gate(tmp_path):
    p = tmp_path / "scene-0411_hard_00"
    p.mkdir()
    files = {}
    for name in ["iter139_trace.jsonl", "controller139.jsonl", "sentinel_iter48_decisions.jsonl"]:
        (p / name).write_bytes(b"proof")
        files[name] = hashlib.sha256(b"proof").hexdigest()
    report = dict(status="validated", verdict="REPLAY_MATCHED", candidate=dict(files=files))
    run_episode.check_predecessor(report, "reference_b", tmp_path)
    bad = deepcopy(report)
    bad["verdict"] = "NO_RECOVERABILITY_TARGET"
    with pytest.raises(ValueError):
        run_episode.check_predecessor(bad, "reference_b", tmp_path)
    (p / "iter139_trace.jsonl").write_bytes(b"changed")
    with pytest.raises(ValueError):
        run_episode.check_predecessor(report, "reference_b", tmp_path)


def test_missing_or_failed_predecessor_is_not_admitted(tmp_path, monkeypatch):
    monkeypatch.setattr(run_episode, "CONTROL", tmp_path / "control")
    with pytest.raises(ValueError, match="incomplete"):
        run_episode.predecessors("reference_b", tmp_path)
    prior = tmp_path / "reference_a"
    prior.mkdir()
    (prior / "episode.json").write_text('{"returncode":0}')
    with pytest.raises(ValueError, match="missing predecessor"):
        run_episode.predecessors("reference_b", tmp_path)
    with pytest.raises(ValueError, match="not validated"):
        run_episode.check_predecessor({"status": "failed"}, "reference_a", prior)


@pytest.mark.parametrize("bad", ["pending", "stockout", "wrong_id", "stopped"])
def test_provider_gate_rejects_failed_or_unready_start(bad):
    from experiments.iter139_finite_pulse_recoverability.provider_gate import require_ready

    zone = "https://www.googleapis.com/compute/v1/projects/sunlit-unison-487018-b0/zones/us-west1-a"
    operation = dict(status="DONE", operationType="start", targetId="3834622546652649531", zone=zone)
    instance = dict(id="3834622546652649531", status="RUNNING", zone=zone,
                    machineType=zone + "/machineTypes/g2-standard-8")
    require_ready(operation, instance)
    if bad == "pending":
        operation["status"] = "RUNNING"
    elif bad == "stockout":
        operation["error"] = {"errors": [{"code": "ZONE_RESOURCE_POOL_EXHAUSTED_WITH_DETAILS"}]}
    elif bad == "wrong_id":
        instance["id"] = "other"
    else:
        instance["status"] = "TERMINATED"
    with pytest.raises(ValueError):
        require_ready(operation, instance)
