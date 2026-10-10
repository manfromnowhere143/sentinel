from pathlib import Path
import math
import numpy as np
import pytest

from experiments.iter145_constrained_execution.optimizer import (
    ConstrainedController,
    certificate,
    controls_constraints,
    objective,
    require_action,
    rollout,
)
from experiments.iter144_timed_trajectory.control import transition
from experiments.iter144_timed_trajectory.trajectory import ContractError

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("v", [0.0, 4.0, -1.0])
@pytest.mark.parametrize("u", [(1.0, 0.1), (-1.0, -0.1), (0.0, 0.0)])
def test_smooth_feasible_motion_matches_execution(v, u):
    state = np.array([0.0, 0.0, 0.3, v, 0.2])
    seq = np.tile(u, (8, 1))
    states, sens = rollout(state, seq)
    actual = state
    for i in range(8):
        actual = transition(actual, seq[i])[0]
        np.testing.assert_allclose(actual, states[i + 1], atol=1e-10, rtol=0)
    eps = 1e-6
    for j in [0, 1, 14, 15]:
        p = seq.ravel().copy()
        m = p.copy()
        p[j] += eps
        m[j] -= eps
        numerical = (rollout(state, p.reshape(-1, 2))[0] - rollout(state, m.reshape(-1, 2))[0]) / (
            2 * eps
        )
        np.testing.assert_allclose(numerical, sens[:, :, j], atol=1e-6, rtol=0)


def test_objective_gradient_including_actuator_boundary():
    s = np.array([0.0, 0.0, 0.2, 0.0, 0.1])
    u = np.tile([0.4, 0.03], (6, 1))
    u[0, 0] = 2.0
    ref = np.zeros((7, 5))
    ref[:, 0] = np.arange(7) * 0.3
    value, g = objective(u.ravel(), s, ref)
    eps = 1e-6
    numerical = []
    for j in range(u.size):
        p = u.ravel().copy()
        m = p.copy()
        p[j] += eps
        m[j] -= eps
        numerical.append((objective(p, s, ref)[0] - objective(m, s, ref)[0]) / (2 * eps))
    np.testing.assert_allclose(g, numerical, atol=1e-6, rtol=0)
    assert value >= 0


def test_constraints_include_accumulated_steering():
    C, b = controls_constraints(19, 0.9)
    u = np.tile([0.0, math.pi / 12], 19)
    assert max(C @ u - b) > 0
    C, b = controls_constraints(19, 0.0)
    assert max(C @ np.zeros(38) - b) < 0


@pytest.mark.parametrize("n,d", [(0, 0), (20, 0), (3, 2), (3, float("nan"))])
def test_bad_constraint_domain(n, d):
    with pytest.raises(ContractError):
        controls_constraints(n, d)


def test_kkt_requires_feasibility_and_stationarity():
    C, b = controls_constraints(1, 0.0)
    assert certificate(np.zeros(2), np.zeros(2), C, b)["admitted"]
    assert not certificate(np.array([3.0, 0.0]), np.zeros(2), C, b)["admitted"]
    assert not certificate(np.zeros(2), np.ones(2), C, b)["admitted"]
    assert certificate(np.array([2.0, 0.0]), np.array([-1.0, 0.0]), C, b)["admitted"]
    assert not certificate(np.array([2.0, 0.0]), np.array([1.0, 0.0]), C, b)["admitted"]


def test_certificate_does_not_mistake_clipped_derivative_for_feasible_derivative():
    s = [0.0, 0.0, 0.0, 0.0, 0.0]
    u = np.array([[2.0, 0.0]])
    projected_B = transition(s, u[0])[3]
    smooth_B = rollout(s, u)[1][1, :, :2]
    assert projected_B[3, 0] == 0 and smooth_B[3, 0] == 0.25


def test_iteration_limit_cannot_actuate():
    ref = np.zeros((13, 5))
    ref[:, 0] = np.arange(13) * 0.5
    r = ConstrainedController().solve(np.zeros(5), ref, max_iterations=1)
    assert not r["admitted"] and r["applied"] is None
    with pytest.raises(ContractError):
        require_action(r)


def test_exact_straight_motion_is_certified():
    ref = np.zeros((13, 5))
    ref[:, 0] = np.arange(13)
    ref[:, 3] = 4.0
    r = ConstrainedController().solve([0.0, 0.0, 0.0, 4.0, 0.0], ref)
    assert r["admitted"] and r["certificate"]["stationarity_inf"] <= 1e-6
    assert abs(require_action(r)["acc"]) < 1e-8


def test_independent_reverse_gradient_and_certificate():
    from copy import deepcopy
    from experiments.iter145_constrained_execution.independent import (
        certificate as second_cert,
        cost_gradient,
    )

    s = [0.0, 0.0, 0.2, 4.0, 0.1]
    u = np.tile([0.5, 0.01], (6, 1))
    ref = np.zeros((7, 5))
    value, g, _ = cost_gradient(s, u.tolist(), ref.tolist())
    value2, g2 = objective(u.ravel(), np.asarray(s), ref)
    assert value == pytest.approx(value2, abs=1e-9)
    np.testing.assert_allclose(g, g2, atol=1e-9, rtol=0)
    ref = np.zeros((13, 5))
    ref[:, 0] = np.arange(13)
    ref[:, 3] = 4.0
    r = ConstrainedController().solve([0.0, 0.0, 0.0, 4.0, 0.0], ref)
    second_cert(r)
    for field, value in [("stationarity_inf", 1.0), ("max_violation", 1.0)]:
        bad = deepcopy(r)
        bad["certificate"][field] = value
        with pytest.raises(ValueError):
            second_cert(bad)
    bad = deepcopy(r)
    bad["certificate"]["multipliers"][0] = -1.0
    with pytest.raises(ValueError):
        second_cert(bad)


def test_callback_is_not_final_solution_when_no_refinement():
    from copy import deepcopy
    from experiments.iter145_constrained_execution.independent import (
        certificate as second_cert,
        cost_gradient,
    )

    ref = np.zeros((13, 5))
    ref[:, 0] = np.arange(13)
    ref[:, 3] = 4.0
    r = ConstrainedController().solve([0.0, 0.0, 0.0, 4.0, 0.0], ref)
    assert r["refinement"] == []
    progress = np.asarray(r["inputs"])
    progress[0, 0] += 1e-5
    r["history"][-1]["inputs"] = progress.tolist()
    r["history"][-1]["objective"] = cost_gradient(
        r["initial_state"], progress.tolist(), r["reference"]
    )[0]
    second_cert(r)
    bad = deepcopy(r)
    bad["inputs"][0][0] += 0.01
    with pytest.raises(ValueError):
        second_cert(bad)


def make_delivery(frame=0, mode="nominal", episode="fixture", curved=False):
    from experiments.iter145_constrained_execution.nominal import packet
    positions = np.array([[.03*i*i if curved else 0., 2.*i] for i in range(1, 7)], dtype=np.float64)
    return packet(positions, positions.copy(), positions.copy(), episode=episode,
                  frame=frame, time=frame*.25, mode=mode, monitor_sha256="a"*64)


def test_nominal_supported_clock_and_world_heading():
    from experiments.iter145_constrained_execution.nominal import reference
    r = reference(make_delivery(), [10., 20., .3, -1.], episode="fixture", frame=0, time=0.)
    assert r.times == tuple(i*.25 for i in range(13)) and r.states[0][3] == -1
    assert r.states[-1][0] == pytest.approx(10 + 12*math.sin(.3))
    assert r.states[-1][1] == pytest.approx(20 + 12*math.cos(.3))
    assert r.states[-1][2] == pytest.approx(math.pi/2-.3)
    with pytest.raises(ContractError, match="extrapolation"):
        r.at(3.25)


@pytest.mark.parametrize("field,value", [("frame", True), ("frame", 1), ("episode", "wrong"),
    ("observation_time", .25), ("knot_times", [0.,.5,1.,1.5,2.,2.5]), ("coordinate_frame", "world"),
    ("mode", "unknown"), ("monitor_sha256", "z"*64)])
def test_delivery_known_bads(field, value):
    from experiments.iter145_constrained_execution.nominal import validate
    bad = make_delivery(); bad[field] = value
    with pytest.raises((ContractError, ValueError)):
        validate(bad, episode="fixture", frame=0, time=0.)


def test_delivery_bytes_and_policy_known_bads():
    from experiments.iter145_constrained_execution.nominal import validate
    bad = make_delivery(); bad["delivered"]["values"][0][0] = 1
    with pytest.raises(ContractError):
        validate(bad, episode="fixture", frame=0, time=0.)
    bad = make_delivery(); bad["delivered"]["sha256"] = "b"*64
    with pytest.raises(ContractError):
        validate(bad, episode="fixture", frame=0, time=0.)


@pytest.mark.parametrize("speed,curved", [(0., False), (4., False), (0., True), (4., True)])
def test_full_source_step_render_collision_and_short_control(speed, curved, monkeypatch):
    import torch
    from experiments.iter145_constrained_execution.source_fixture import fixture
    from experiments.iter145_constrained_execution.simulator import Session
    monkeypatch.setattr(torch.Tensor, "cuda", lambda self, *a, **k: self)
    env, calls = fixture(ROOT, speed=speed)
    session = Session(env, "fixture", device="cpu")
    obs, info = session.reset()
    assert info["timestamp"] == 0 and env.planner.tick == 0
    for frame in range(12):
        output = session.step(make_delivery(frame=frame, curved=curved))
        assert output[-1]["timestamp"] == (frame+1)*.25
        assert not session.stopped
        group = [c for c in calls if c["time"] == (frame+1)*.25]
        assert [c["kind"] for c in group] == ["collision"] + ["render"]*6
        assert len({c["planning_id"] for c in group}) == 1
        assert group[0]["boxes"] == env.objs_list
        for name, matrix in env.render_kwargs["planning"][0].items():
            state = env.planner.native(name)
            assert matrix[0,3].item() == pytest.approx(state[0], abs=5e-6)
            assert matrix[2,3].item() == pytest.approx(state[1], abs=5e-6)
            rotation = -state[2] if type(env.planner.controller[name]).__name__ == "UnicyclePlanner" else -state[2]-math.pi/2
            assert matrix[0,0].item() == pytest.approx(math.cos(rotation), abs=1e-6)
    assert sum(e["event"] == "select" for e in env.planner.events) == 2
    with pytest.raises(ContractError, match="duplicate_reset"):
        session.reset()


def test_reset_clock_and_runtime_known_bads(monkeypatch):
    from experiments.iter145_constrained_execution.source_fixture import fixture
    from experiments.iter145_constrained_execution.simulator import Session, check_runtime
    env, _ = fixture(ROOT, actors=("ConstantPlanner",))
    env.kinematic["Lr"] = 1.4
    with pytest.raises(ContractError, match="kinematics"):
        check_runtime(env)
    env.kinematic["Lr"] = 1.35
    session = Session(env, "fixture", device="cpu"); session.reset()
    with pytest.raises(ContractError, match="tick"):
        env.planner.plan_traj(.5, env.ego_state)
    with pytest.raises(ContractError, match="stopped"):
        env.planner.plan_traj(.25, env.ego_state)


def test_unicycle_unsupported_time_and_unknown_actor():
    from experiments.iter145_constrained_execution.source_fixture import fixture
    from experiments.iter145_constrained_execution.simulator import Session, TimedPlanner
    env, _ = fixture(ROOT, actors=("UnicyclePlanner",))
    with pytest.raises(ContractError, match="unsupported_time"):
        TimedPlanner.unicycle_support(env.planner.controller["agent_0"], 21.)
    env.planner.controller["agent_0"] = object()
    with pytest.raises(ContractError, match="unknown_actor_type"):
        Session(env, "fixture", device="cpu")
