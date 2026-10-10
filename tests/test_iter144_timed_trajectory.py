"""Execution contract, adversarial admissions, and actual upstream integration."""

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import math
import numpy as np
import pytest
import torch

from experiments.iter144_timed_trajectory import trajectory as t
from experiments.iter144_timed_trajectory.control import MatchedController, brake, transition
from experiments.iter144_timed_trajectory.runtime import ActorWorld, apply_step
from experiments.iter144_timed_trajectory.source import environment_prefix, load_sampler
from experiments.iter144_timed_trajectory.study import readiness, schedule

ROOT = Path(__file__).resolve().parents[1]


def plan():
    return t.constant_motion((0.0, 0.0, 0.0, 4.0), 0.0, "episode", "actor")


@pytest.mark.parametrize(
    "field,value",
    [
        ("units", ("ms", "m", "m", "rad", "m/s")),
        ("frame", "unknown"),
        ("schema", "legacy"),
        ("episode", ""),
        ("owner", ""),
        ("origin", 0.1),
        ("origin", float("nan")),
        ("times", (0.0, 0.0)),
        ("times", (0.0, float("inf"))),
        ("times", (0.0,)),
        ("states", ((0.0, 0.0, 0.0, 4.0),)),
        ("states", ((0.0, 0.0, 0.0),) * 20),
        ("states", ((0.0, 0.0, 0.0, None),) * 20),
        ("states", ((0.0, 0.0, 0.0, True),) * 20),
    ],
)
def test_bad_trajectory(field, value):
    with pytest.raises(t.ContractError):
        replace(plan(), **{field: value})


@pytest.mark.parametrize("time", [-0.01, 4.75001, float("nan"), True, None])
def test_extrapolation_or_bad_query(time):
    with pytest.raises(t.ContractError):
        plan().at(time)


def test_exact_boundaries_and_angular_interpolation():
    p = t.Trajectory(
        "e",
        "a",
        0.0,
        (0.0, 1.0),
        ((0.0, 0.0, math.pi - 0.1, 1.0), (1.0, 0.0, -math.pi + 0.1, 1.0)),
        "synthetic",
    )
    assert p.at(0) == p.states[0] and p.at(1) == p.states[1]
    assert abs(p.at(0.5)[2]) == pytest.approx(math.pi)
    assert p.at(0.5)[0] == 0.5


@pytest.mark.parametrize("yaw", [-math.pi, -0.4, 0.0, 0.4, math.pi])
def test_actor_roundtrip_and_distinct_ego_frame(yaw):
    native = (1.0, 2.0, yaw, 4.0)
    assert t.same_state(t.common_to_actor(t.actor_to_common(native)), native)
    actor, ego = t.actor_to_common(native), t.ego_to_common(native)
    assert math.cos(actor[2]) == pytest.approx(-math.sin(yaw))
    assert math.cos(ego[2]) == pytest.approx(math.sin(yaw))


def test_reset_and_replan_are_time_based():
    e = t.Executor("episode", "actor", plan().states[0])
    assert e.time == 0 and e.state == (0.0, 0.0, 0.0, 4.0)
    e.install(plan())
    for i in range(1, 11):
        assert e.advance(i * 0.25)[0] == i
    with pytest.raises(t.ContractError, match="stale"):
        e.advance(2.75)
    e.install(t.constant_motion(e.state, 2.5, "episode", "actor"))
    assert e.advance(2.75)[0] == 11


@pytest.mark.parametrize("bad", ["episode", "owner", "origin", "reset_advance", "grid"])
def test_invalid_install_preserves_active(bad):
    e = t.Executor("episode", "actor", plan().states[0])
    e.install(plan())
    original = e.plan
    values = {
        "episode": dict(episode="other"),
        "owner": dict(owner="other"),
        "origin": dict(origin=1.0, times=tuple(1.0 + i * 0.25 for i in range(20))),
        "reset_advance": dict(states=((1.0, 0.0, 0.0, 4.0),) + plan().states[1:]),
        "grid": dict(times=tuple(i * 0.2 for i in range(20))),
    }
    with pytest.raises(t.ContractError):
        e.install(replace(plan(), **values[bad]))
    assert e.plan is original and e.tick == 0


@pytest.mark.parametrize("time", [0.0, 0.1, 0.5])
def test_wrong_execution_tick(time):
    e = t.Executor("episode", "actor", plan().states[0])
    e.install(plan())
    with pytest.raises(t.ContractError):
        e.advance(time)
    assert e.tick == 0


def source_rows():
    return [[4 * i * 5 / 19, 0.0, 4.0, 0.0, 0.0, 0.0, i * 5 / 19] for i in range(1, 20)]


@pytest.mark.parametrize("mutation", ["dropped", "shifted", "duplicate", "nonfinite", "length"])
def test_bad_source_time(mutation):
    rows = source_rows()
    if mutation == "dropped":
        rows = [r[:-1] for r in rows]
    elif mutation == "shifted":
        for r in rows:
            r[-1] += 0.01
    elif mutation == "duplicate":
        rows[1][-1] = rows[0][-1]
    elif mutation == "nonfinite":
        rows[3][-1] = float("nan")
    else:
        rows.pop()
    with pytest.raises(t.ContractError):
        t.from_source(rows, plan().states[0], 0.0, "episode", "actor")


def test_cost_uses_common_times_and_explicit_neighbors():
    p = plan()
    ego = t.constant_motion((0.0, 2.0, 0.0, 4.0), 0.0, "episode", "ego")
    assert t.costs([p], ego, []) == [2.0]
    assert t.costs([p], ego, [p]) == [2.1]
    with pytest.raises(t.ContractError):
        t.costs([replace(p, origin=1.0, times=tuple(1.0 + i * 0.25 for i in range(20)))], ego, [])
    with pytest.raises(t.ContractError):
        t.costs([replace(p, episode="other")], ego, [])


@pytest.mark.parametrize("control", [(1.0, 0.1), (3.0, 0.4), (-3.0, -0.4), (0.0, 0.2)])
@pytest.mark.parametrize("steer", [0.0, math.pi / 3 - 0.01])
def test_analytic_jacobians_against_differences(control, steer):
    state = np.array([0.0, 0.0, 0.3, 4.0, steer])
    u = np.array(control)
    _, _, A, B = transition(state, u)
    eps = 1e-6
    Aj = np.column_stack(
        [
            (
                transition(state + np.eye(5)[i] * eps, u)[0]
                - transition(state - np.eye(5)[i] * eps, u)[0]
            )
            / (2 * eps)
            for i in range(5)
        ]
    )
    Bj = np.column_stack(
        [
            (
                transition(state, u + np.eye(2)[i] * eps)[0]
                - transition(state, u - np.eye(2)[i] * eps)[0]
            )
            / (2 * eps)
            for i in range(2)
        ]
    )
    np.testing.assert_allclose(A, Aj, atol=1e-5, rtol=0)
    np.testing.assert_allclose(B, Bj, atol=1e-5, rtol=0)


@pytest.mark.parametrize("v", [-4.0, -0.1, 0.0, 0.1, 4.0])
def test_braking_never_crosses_zero(v):
    vn = transition([0.0, 0.0, 0.0, v, 0.0], [brake(v), 0.0])[0][3]
    assert abs(vn) <= abs(v) and vn * v >= 0


@pytest.mark.parametrize("v", [0.0, 1.0, 4.0])
def test_full_actual_sampler_admission(v):
    sampler = load_sampler(ROOT)
    initial = (0.0, 0.0, math.pi / 2, v)
    rows, _ = sampler.gen_trajectories(
        torch.tensor([0.0, 0.0, v, math.pi / 2], dtype=torch.float64),
        5.0,
        lanes=None,
        dyn_filter=True,
    )
    assert len(rows) > 0
    trajectories = [t.from_source(row, initial, 0.0, "e", "a") for row in rows.tolist()]
    assert all(p.times[-1] == 4.75 and len(p.source_rows) == 19 for p in trajectories)


def test_real_solver_runs_and_logs_stopping():
    ref = t.constant_motion((0.0, 0.0, math.pi / 2, 4.0), 0.0, "e", "ego_plan")
    row = MatchedController().run(ref, [0.0, 0.0, 0.0, 4.0, 0.0], episode="e", observation_time=0.0)
    assert row["stop_reason"] in {"converged", "iteration_limit"}
    assert row["solver_ns"] <= row["complete_call_ns"]
    assert len(row["inputs"]) == 19 and len(row["states"]) == 20


def test_controller_rejects_stale_reference():
    with pytest.raises(t.ContractError):
        MatchedController().run(plan(), [0.0] * 5, episode="other", observation_time=0.0)


def test_actual_environment_prefix_integration():
    world = ActorWorld(
        "e", {"actor": (1.0, 0.0, 0.3, 4.0)}, {"actor": load_sampler(ROOT, straight=True)}
    )
    world.plan_traj(0.0, (0.0, 0.0, 0.0, 4.0))

    class Env(SimpleNamespace):
        @property
        def ego_state(self):
            return [float(self.vab[0]), float(self.vab[1]), float(self.vr[1]), self.velo]

    env = Env(
        timestamp=0.0,
        dt=0.25,
        planner=world,
        render_kwargs={},
        vab=np.zeros(2),
        vr=np.zeros(3),
        velo=4.0,
        steer=0.0,
        kinematic={"Lf": 1.35, "Lr": 1.35},
    )
    step = environment_prefix(ROOT)
    for _ in range(12):
        record = apply_step(env, [3.0, 0.4], step)
        np.testing.assert_allclose(record["after"], record["predicted"], atol=1e-8, rtol=0)
    assert [s["time"] for s in world.selections] == [0.0, 2.5]
    assert world.executors["actor"].events[0]["advanced"] is False
    with pytest.raises(t.ContractError):
        world.plan_traj(env.timestamp, env.ego_state)
    assert world.stop_reason is not None


def test_study_keeps_all_rows_and_never_invents_bindings():
    s = schedule(ROOT)
    assert len(s["slots"]) == 112 and len(s["inventory"]) == 88
    assert len({r["scenario"] for r in s["slots"]}) == 14
    assert all(r["outcome"] is None for r in s["slots"])
    assert len(readiness(s)["missing_bindings"]) == 7
    assert s["cloud_budget"] == 0 and not s["live_admitted"]


def test_stopping_latches_after_bad_world_tick():
    world = ActorWorld("e", {}, {})
    world.plan_traj(0.0, [0.0, 0.0, 0.0, 0.0])
    with pytest.raises(t.ContractError):
        world.plan_traj(0.5, [0.0, 0.0, 0.0, 0.0])
    assert world.stop_reason == "ContractError:world_reset_or_tick"
    with pytest.raises(t.ContractError, match="already_stopped"):
        world.plan_traj(0.25, [0.0, 0.0, 0.0, 0.0])


def test_reverse_actor_stops_before_generation():
    world = ActorWorld("e", {"a": (0.0, 0.0, 0.0, -1.0)}, {"a": None})
    world.plan_traj(0.0, [0.0, 0.0, 0.0, 0.0])
    with pytest.raises(t.ContractError, match="reverse_actor"):
        world.plan_traj(0.25, [0.0, 0.0, 0.0, 0.0])
    assert world.tick == 0


def test_single_reset_only():
    world = ActorWorld("e", {}, {})
    world.plan_traj(0.0, [0.0, 0.0, 0.0, 0.0])
    with pytest.raises(t.ContractError, match="reset_or_tick"):
        world.plan_traj(0.0, [0.0, 0.0, 0.0, 0.0])


@pytest.mark.parametrize(
    "state,control",
    [
        ([0.0] * 4, [0.0, 0.0]),
        ([0.0] * 5, [0.0]),
        ([0.0, 0.0, 0.0, None, 0.0], [0.0, 0.0]),
        ([0.0] * 5, [float("nan"), 0.0]),
        ([0.0, 0.0, 0.0, 0.0, math.pi / 2], [0.0, 0.0]),
    ],
)
def test_bad_ego_inputs(state, control):
    with pytest.raises((t.ContractError, TypeError)):
        transition(state, control)


def test_default_low_and_spline_source_branches_present():
    sampler = load_sampler(ROOT)
    rows, _ = sampler.gen_trajectories(
        torch.tensor([0.0, 0.0, 1.0, math.pi / 2], dtype=torch.float64),
        5.0,
        lanes=None,
        dyn_filter=True,
    )
    branches = {
        t.from_source(r, (0.0, 0.0, math.pi / 2, 1.0), 0.0, "e", "a").branch for r in rows.tolist()
    }
    assert branches == {"low_speed", "spline"}


def test_independent_time_and_units_rejection():
    import json
    from experiments.iter144_timed_trajectory.independent import check_trajectory

    value = json.loads(json.dumps(plan().record()))
    check_trajectory(value)
    value["times"][-1] += 0.01
    with pytest.raises(ValueError):
        check_trajectory(value)
    value = json.loads(json.dumps(plan().record()))
    value["units"][0] = "ms"
    with pytest.raises(ValueError):
        check_trajectory(value)


def test_source_hash_gate_fires(tmp_path):
    import json
    import shutil
    from experiments.iter144_timed_trajectory.source import BASE, bound_inputs

    names = [BASE + "/INPUTS.json", BASE + "/SOURCE_ADDITION.json"]
    names += list(json.loads((ROOT / names[0]).read_text())["files"])
    names += [json.loads((ROOT / names[1]).read_text())["path"]]
    for name in names:
        dest = tmp_path / name
        dest.parent.mkdir(exist_ok=True, parents=True)
        shutil.copyfile(ROOT / name, dest)
    target = tmp_path / names[-1]
    target.write_bytes(target.read_bytes() + b"\n")
    with pytest.raises(t.ContractError, match="source_identity"):
        bound_inputs(tmp_path)
