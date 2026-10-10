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
