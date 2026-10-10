"""New simulator-matched ego dynamics and actual source iLQR integration."""

from dataclasses import asdict, replace
import math
import time
import numpy as np

from experiments.iter137_controller_execution_contract.controller import load_source
from .trajectory import ContractError, DT, N, scalar

LIMIT_A = 2.0
LIMIT_R = math.pi / 12
LIMIT_D = math.pi / 3
L = 2.7


def transition(state, requested):
    """[b,a,theta,v,steer], [acc,steer_rate]. Jacobians wrt requested input."""
    if len(state) != 5 or len(requested) != 2:
        raise ContractError("ego_state_or_control_shape")
    x, y, h, v, d = map(scalar, state)
    a0, r0 = map(scalar, requested)
    if abs(d) > LIMIT_D:
        raise ContractError("initial_steering_outside_contract")
    a = min(LIMIT_A, max(-LIMIT_A, a0))
    r = min(LIMIT_R, max(-LIMIT_R, r0))
    dn0 = d + r * DT
    dn = min(LIMIT_D, max(-LIMIT_D, dn0))
    r = (dn - d) / DT
    vn = v + a * DT
    out = np.array(
        [
            x + vn * math.cos(h) * DT,
            y + vn * math.sin(h) * DT,
            h + vn * math.tan(dn) / L * DT,
            vn,
            dn,
        ]
    )
    A, B = np.eye(5), np.zeros((5, 2))
    ga, gr, gd = float(abs(a0) < LIMIT_A), float(abs(r0) < LIMIT_R), float(abs(dn0) < LIMIT_D)
    A[0, 2], A[0, 3] = -vn * math.sin(h) * DT, math.cos(h) * DT
    A[1, 2], A[1, 3] = vn * math.cos(h) * DT, math.sin(h) * DT
    A[2, 3], A[2, 4] = math.tan(dn) / L * DT, vn / (L * math.cos(dn) ** 2) * DT * gd
    A[4, 4] = gd
    B[0, 0], B[1, 0] = math.cos(h) * DT**2 * ga, math.sin(h) * DT**2 * ga
    B[2, 0] = math.tan(dn) / L * DT**2 * ga
    B[2, 1] = vn / (L * math.cos(dn) ** 2) * DT**2 * gr * gd
    B[3, 0], B[4, 1] = DT * ga, DT * gr * gd
    return out, np.array([a, r]), A, B


def brake(velocity):
    v = scalar(velocity)
    return -math.copysign(min(LIMIT_A, abs(v) / DT), v) if v else 0.0


class MatchedController:
    """Numerical mode, explicit .25-second world reference and source stopping log."""

    def __init__(self):
        module, params, _ = load_source()
        self.params = replace(
            params.solver_params,
            discretization_time=DT,
            max_solve_time=None,
            max_acceleration=LIMIT_A,
            max_steering_angle_rate=LIMIT_R,
        )

        class Solver(module.ILQRSolver):
            def _dynamics_and_jacobian(self, current_state, current_input):
                return transition(current_state, current_input)

        self.solver = Solver(self.params, params.warm_start_params)
        self.solver.clock = time.perf_counter
        self.configuration = dict(
            solver=asdict(self.params),
            warm_start=asdict(params.warm_start_params),
            dynamics="sentinel.simulator_matched.v1",
            mode="numerical",
        )

    def run(self, reference, state, *, episode, observation_time):
        start = time.perf_counter_ns()
        if reference.episode != episode or reference.origin != observation_time:
            raise ContractError("controller_stale_reference")
        if reference.times != tuple(observation_time + i * DT for i in range(N)):
            raise ContractError("controller_time_grid")
        transition(state, [0.0, 0.0])  # State validation before the solver.
        ref = np.array(
            [[b, a, math.pi / 2 - heading, speed, 0.0] for a, b, heading, speed in reference.states]
        )
        solver_start = time.perf_counter_ns()
        solutions = self.solver.solve(np.asarray(state, dtype=float), ref)
        solver_ns = time.perf_counter_ns() - solver_start
        final = solutions[-1]
        proposed = final.input_trajectory[0].tolist()
        _, applied, _, _ = transition(state, proposed)
        result = dict(
            reference=reference.record(),
            reference_id=reference.identity,
            initial_state=list(state),
            proposed=proposed,
            applied=applied.tolist(),
            inputs=final.input_trajectory.tolist(),
            states=final.state_trajectory.tolist(),
            iterations=len(solutions) - 1,
            stop_reason=self.solver.execution["stop_reason"],
            norms=self.solver.execution["norms"],
            solver_ns=solver_ns,
        )
        result["complete_call_ns"] = time.perf_counter_ns() - start
        return result
