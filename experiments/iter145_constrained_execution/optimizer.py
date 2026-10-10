"""Constrained shooting: smooth applied-control dynamics plus explicit constraints."""

import math
import time
import numpy as np
from scipy.optimize import minimize, nnls

from experiments.iter144_timed_trajectory.control import MatchedController
from experiments.iter144_timed_trajectory.trajectory import ContractError

DT, WHEELBASE = 0.25, 2.7
Q = np.array([1.0, 1.0, 10.0, 0.0, 0.0])
R = np.array([1.0, 10.0])
MAX_ITER = 100


def controls_constraints(n, steering):
    """C u <= b: acceleration/rate boxes and every cumulative steering angle."""
    if (
        type(n) is not int
        or not 1 <= n <= 19
        or not np.isfinite(steering)
        or abs(steering) > math.pi / 3
    ):
        raise ContractError("control_constraint_domain")
    eye = np.eye(2 * n)
    lim = np.tile([2.0, math.pi / 12], n)
    cumulative = np.zeros((n, 2 * n))
    cumulative[:, 1::2] = np.tril(np.ones((n, n))) * DT
    return np.vstack([eye, -eye, cumulative, -cumulative]), np.r_[
        lim, lim, np.full(n, math.pi / 3 - steering), np.full(n, math.pi / 3 + steering)
    ]


def rollout(state, inputs):
    """Smooth transition and exact sensitivity to all physically applied inputs."""
    state = np.asarray(state, dtype=float)
    inputs = np.asarray(inputs, dtype=float)
    if (
        state.shape != (5,)
        or inputs.ndim != 2
        or inputs.shape[1] != 2
        or not np.isfinite(state).all()
        or not np.isfinite(inputs).all()
    ):
        raise ContractError("rollout_shape_or_nonfinite")
    n = len(inputs)
    states = [state.copy()]
    sens = [np.zeros((5, 2 * n))]
    for i, (acc, rate) in enumerate(inputs):
        x, y, h, v, d = states[-1]
        vn = v + acc * DT
        dn = d + rate * DT
        c, s, td = math.cos(h), math.sin(h), math.tan(dn)
        sec2 = 1 / math.cos(dn) ** 2
        A = np.eye(5)
        B = np.zeros((5, 2))
        A[0, 2], A[0, 3] = -vn * s * DT, c * DT
        A[1, 2], A[1, 3] = vn * c * DT, s * DT
        A[2, 3], A[2, 4] = td / WHEELBASE * DT, vn * sec2 / WHEELBASE * DT
        B[0, 0], B[1, 0] = c * DT**2, s * DT**2
        B[2, 0], B[2, 1] = td / WHEELBASE * DT**2, vn * sec2 / WHEELBASE * DT**2
        B[3, 0], B[4, 1] = DT, DT
        sensitivity = A @ sens[-1]
        sensitivity[:, 2 * i : 2 * i + 2] += B
        states.append(
            np.array([x + vn * c * DT, y + vn * s * DT, h + vn * td / WHEELBASE * DT, vn, dn])
        )
        sens.append(sensitivity)
    return np.asarray(states), np.asarray(sens)


def objective(flat, state, reference):
    inputs = np.asarray(flat, dtype=float).reshape(-1, 2)
    states, sens = rollout(state, inputs)
    error = states - reference
    error[:, 2] = np.arctan2(np.sin(error[:, 2]), np.cos(error[:, 2]))
    value = float(np.sum(error**2 * Q) + np.sum(inputs**2 * R))
    gradient = 2 * np.einsum("ti,tij->j", error * Q, sens) + 2 * (inputs * R).ravel()
    if not math.isfinite(value) or not np.isfinite(gradient).all():
        raise ContractError("nonfinite_objective")
    return value, gradient


def certificate(u, gradient, C, b):
    slack = b - C @ u
    active = np.flatnonzero(slack <= 1e-7)
    multipliers = np.zeros(len(b))
    if len(active):
        multipliers[active] = nnls(C[active].T, -gradient, maxiter=1000)[0]
    residual = gradient + C.T @ multipliers
    violation = float(max(0.0, -min(slack)))
    stationarity = float(np.linalg.norm(residual, ord=np.inf))
    complementarity = float(np.max(np.abs(slack * multipliers)))
    ok = violation <= 1e-9 and stationarity <= 1e-6 and complementarity <= 1e-7
    return dict(
        admitted=bool(ok),
        max_violation=violation,
        stationarity_inf=stationarity,
        complementarity_inf=complementarity,
        gradient=gradient.tolist(),
        slack=slack.tolist(),
        multipliers=multipliers.tolist(),
        active=active.tolist(),
    )


def refine(u, state, ref, C, b, remaining):
    """Bounded feasible Gauss-Newton refinement under the unchanged certificate."""
    u = u.copy()
    history = []
    for _ in range(min(8, remaining)):
        value, g = objective(u, state, ref)
        cert = certificate(u, g, C, b)
        if cert["admitted"]:
            break
        _, J = rollout(state, u.reshape(-1, 2))
        H = 2 * np.einsum("tij,i,tik->jk", J, Q, J) + np.diag(2 * np.tile(R, len(u) // 2))
        active = np.flatnonzero(np.asarray(cert["multipliers"]) > 1e-9)
        A = C[active]
        if len(active):
            _, singular, vectors = np.linalg.svd(A, full_matrices=True)
            rank = int(np.sum(singular > np.finfo(float).eps * max(A.shape) * singular[0]))
            basis = vectors[rank:].T
        else:
            basis = np.eye(len(u))
        if basis.shape[1] == 0:
            break
        direction = -basis @ np.linalg.solve(basis.T @ H @ basis, basis.T @ g)
        slope = float(g @ direction)
        if slope >= 0:
            break
        movement = C @ direction
        forward = movement > 1e-14
        maximum = (
            min(1.0, float(np.min(np.maximum(0.0, b - C @ u)[forward] / movement[forward])))
            if forward.any()
            else 1.0
        )
        accepted = None
        for backtrack in range(20):
            alpha = maximum * 2.0**-backtrack
            candidate = u + alpha * direction
            next_value, _ = objective(candidate, state, ref)
            if (
                alpha > 0
                and np.max(C @ candidate - b) <= 1e-9
                and next_value <= value + 1e-4 * alpha * slope + 2e-14 * max(1.0, abs(value))
            ):
                accepted = candidate
                history.append(
                    dict(
                        objective=next_value,
                        inputs=candidate.reshape(-1, 2).tolist(),
                        alpha=alpha,
                        slope=slope,
                        previous_objective=value,
                        previous_inputs=u.reshape(-1, 2).tolist(),
                        stationarity_before=cert["stationarity_inf"],
                        backtracks=backtrack,
                    )
                )
                break
        if accepted is None:
            break
        u = accepted
    return u, history


class ConstrainedController:
    """First-order certificate gates action admission; no fallback on solver failure."""

    def __init__(self):
        self.warm_solver = MatchedController().solver

    def solve(self, state, reference, *, max_iterations=MAX_ITER):
        start = time.perf_counter_ns()
        state = np.asarray(state, dtype=float)
        ref = np.asarray(reference, dtype=float)
        if (
            state.shape != (5,)
            or ref.ndim != 2
            or ref.shape[1] != 5
            or not 2 <= len(ref) <= 20
            or not np.isfinite(state).all()
            or not np.isfinite(ref).all()
        ):
            raise ContractError("reference_or_state_shape")
        if max_iterations not in range(1, 101):
            raise ContractError("iteration_cap")
        n = len(ref) - 1
        C, b = controls_constraints(n, float(state[4]))
        warm = self.warm_solver._input_warm_start(state, ref).input_trajectory.ravel()
        if np.max(C @ warm - b) > 1e-10:
            raise ContractError("warm_start_infeasible")
        history = []

        def callback(u):
            value, g = objective(u, state, ref)
            history.append(
                dict(
                    objective=value,
                    inputs=u.reshape(-1, 2).tolist(),
                    gradient_inf=float(np.max(np.abs(g))),
                )
            )

        solver_start = time.perf_counter_ns()
        result = minimize(
            objective,
            warm,
            args=(state, ref),
            jac=True,
            method="SLSQP",
            bounds=[(-2.0, 2.0), (-math.pi / 12, math.pi / 12)] * n,
            constraints=[dict(type="ineq", fun=lambda u: b - C @ u, jac=lambda u: -C)],
            callback=callback,
            options=dict(maxiter=max_iterations, ftol=1e-12, disp=False),
        )
        slsqp_inputs = result.x.reshape(-1, 2).tolist()
        refined, polishing = refine(result.x, state, ref, C, b, max_iterations - int(result.nit))
        result.x = refined
        solver_ns = time.perf_counter_ns() - solver_start
        cost, gradient = objective(result.x, state, ref)
        cert = certificate(result.x, gradient, C, b)
        admitted = bool(result.success and cert["admitted"])
        states, _ = rollout(state, result.x.reshape(-1, 2))
        record = dict(
            schema="sentinel.constrained_controller.v2",
            refinement_method="active_nullspace_gauss_newton",
            initial_state=state.tolist(),
            reference=ref.tolist(),
            warm_inputs=warm.reshape(-1, 2).tolist(),
            warm_objective=objective(warm, state, ref)[0],
            inputs=result.x.reshape(-1, 2).tolist(),
            states=states.tolist(),
            objective=cost,
            certificate=cert,
            library_success=bool(result.success),
            library_status=int(result.status),
            library_message=str(result.message),
            iterations=int(result.nit) + len(polishing),
            slsqp_iterations=int(result.nit),
            slsqp_returned_inputs=slsqp_inputs,
            refinement=polishing,
            history=history,
            admitted=admitted,
            stop_reason="kkt_converged" if admitted else "solver_or_certificate_rejected",
            proposed=result.x[:2].tolist(),
            applied=result.x[:2].tolist() if admitted else None,
            solver_ns=solver_ns,
        )
        record["complete_call_ns"] = time.perf_counter_ns() - start
        return record

    def run(self, reference, state, *, episode, observation_time):
        if (
            reference.episode != episode
            or reference.origin != observation_time
            or reference.times
            != tuple(observation_time + i * DT for i in range(len(reference.times)))
        ):
            raise ContractError("reference_identity_or_time")
        ref = np.array(
            [[b, a, math.pi / 2 - heading, speed, 0.0] for a, b, heading, speed in reference.states]
        )
        result = self.solve(state, ref)
        result.update(
            reference_id=reference.identity,
            observation_time=observation_time,
            application_time=observation_time + DT,
            episode=episode,
        )
        return result


def require_action(record):
    if not record.get("admitted") or record.get("applied") is None:
        raise ContractError("uncertified_controller_result")
    return dict(acc=record["applied"][0], steer_rate=record["applied"][1])
