"""Frozen local CPU fixture runner. Writes raw data only; separate replay interprets."""

import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
import platform
import sys
from types import SimpleNamespace
import numpy as np
import scipy
import torch

from .control import MatchedController, transition
from .runtime import ActorWorld, apply_step
from .source import bound_inputs, environment_prefix, load_sampler
from .trajectory import DT, Trajectory


class BranchFixture:
    """Actual source generation restricted to a declared branch; empty injection for fallback."""

    def __init__(self, root, branch):
        self.sampler = load_sampler(root, straight=True)
        self.branch = branch

    def gen_trajectories(self, x0, tf, lanes, dyn_filter):
        if self.branch == "fallback":
            return torch.empty((0, 19, 7)), None
        rows, _ = self.sampler.gen_trajectories(x0, tf, lanes, dyn_filter)
        end = 5.0 if self.branch == "spline" else 4.75
        chosen = rows[(rows[:, -1, -1] - end).abs() < 1e-6]
        if len(chosen) != 1:
            raise ValueError("straight fixture expected exactly one declared branch candidate")
        return chosen, None


class FixtureEnv(SimpleNamespace):
    @property
    def ego_state(self):
        return [float(self.vab[0]), float(self.vab[1]), float(self.vr[1]), float(self.velo)]


def reference(velocity, curved, origin=0.0, state=None, episode="qualification"):
    state = [0.0, 0.0, 0.0, velocity, 0.0] if state is None else state
    x, y, h, v, d = state
    speed = max(2.0, velocity)
    rows = []
    for i in range(20):
        tau = i * DT
        dx = speed * tau
        dy = 0.1 * tau * tau if curved else 0.0
        local_heading = math.atan2(0.2 * tau, speed) if curved else 0.0
        b = x + math.cos(h) * dx - math.sin(h) * dy
        a = y + math.sin(h) * dx + math.cos(h) * dy
        rows.append(
            (a, b, math.pi / 2 - h - local_heading, math.hypot(speed, 0.2 * tau if curved else 0.0))
        )
    return Trajectory(
        episode,
        "nominal_reference",
        origin,
        tuple(origin + i * DT for i in range(20)),
        tuple(rows),
        "synthetic_reference",
    )


def run(root):
    inputs = bound_inputs(root)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    np.random.seed(144)
    torch.manual_seed(144)
    straight = []
    for branch, v in [("spline", 4.0), ("low_speed", 1.0), ("fallback", 4.0)]:
        for yaw in [-0.4, 0.0, 0.4]:
            initial = (1.0, 2.0, yaw, v)
            world = ActorWorld(
                "qualification", {"actor": initial}, {"actor": BranchFixture(root, branch)}
            )
            rows = [dict(time=0.0, actor=world.plan_traj(0.0, (0.0, 0.0, 0.0, 4.0))["actor"])]
            for i in range(1, 21):
                rows.append(
                    dict(
                        time=i * DT,
                        actor=world.plan_traj(i * DT, (0.0, i * DT * 4, 0.0, 4.0))["actor"],
                    )
                )
            straight.append(
                dict(
                    branch=branch,
                    velocity=v,
                    yaw=yaw,
                    initial=initial,
                    rows=rows,
                    selections=world.selections,
                    events=world.executors["actor"].events,
                )
            )
    full = []
    for v, yaw in itertools.product([0.0, 1.0, 4.0], [-0.4, 0.0, 0.4]):
        world = ActorWorld(
            "qualification", {"actor": (1.0, 2.0, yaw, v)}, {"actor": load_sampler(root)}
        )
        world.plan_traj(0.0, (0.0, 0.0, 0.0, 4.0))
        world.plan_traj(0.25, (0.0, 0.0, 0.0, 4.0))
        full.append(dict(velocity=v, yaw=yaw, selection=world.selections[0]))
    ego = []
    for v, h, d, u in itertools.product(
        [0.0, 4.0], [0.0, 0.3], [0.0, 0.2], [(0.0, 0.0), (2.0, 0.2), (-2.0, -0.2), (3.0, 0.4)]
    ):
        s = [0.0, 0.0, h, v, d]
        out, applied, A, B = transition(s, u)
        ego.append(dict(state=s, requested=u, applied=applied.tolist(), after=out.tolist()))
    jacobians = []
    for u, d in itertools.product(
        [(1.0, 0.1), (3.0, 0.4), (-3.0, -0.4), (0.0, 0.2)], [0.0, math.pi / 3 - 0.01]
    ):
        s = np.array([0.0, 0.0, 0.3, 4.0, d])
        u = np.array(u)
        out, applied, A, B = transition(s, u)
        eps = 1e-6
        perturbed_state = [
            dict(
                plus=transition(s + np.eye(5)[i] * eps, u)[0].tolist(),
                minus=transition(s - np.eye(5)[i] * eps, u)[0].tolist(),
            )
            for i in range(5)
        ]
        perturbed_input = [
            dict(
                plus=transition(s, u + np.eye(2)[i] * eps)[0].tolist(),
                minus=transition(s, u - np.eye(2)[i] * eps)[0].tolist(),
            )
            for i in range(2)
        ]
        jacobians.append(
            dict(
                state=s.tolist(),
                requested=u.tolist(),
                A=A.tolist(),
                B=B.tolist(),
                epsilon=eps,
                perturbed_state=perturbed_state,
                perturbed_input=perturbed_input,
            )
        )
    solver = []
    for v, curve in itertools.product([0.0, 4.0], [False, True]):
        for replica in [1, 2]:
            controller = MatchedController()
            row = controller.run(
                reference(v, curve),
                [0.0, 0.0, 0.0, v, 0.0],
                episode="qualification",
                observation_time=0.0,
            )
            solver.append(
                dict(
                    velocity=v,
                    curved=curve,
                    replica=replica,
                    configuration=controller.configuration,
                    record=row,
                )
            )
    world = ActorWorld(
        "integration", {"actor": (2.0, 5.0, 0.3, 4.0)}, {"actor": load_sampler(root, straight=True)}
    )
    initial = world.plan_traj(0.0, (0.0, 0.0, 0.0, 4.0))
    env = FixtureEnv(
        timestamp=0.0,
        dt=DT,
        planner=world,
        render_kwargs={},
        vab=np.zeros(2),
        vr=np.zeros(3),
        velo=4.0,
        steer=0.0,
        kinematic={"Lf": 1.35, "Lr": 1.35},
    )
    step = environment_prefix(root)
    controller = MatchedController()
    integration = []
    for i in range(20):
        state = [
            float(env.vab[1]),
            float(env.vab[0]),
            float(env.vr[1]),
            float(env.velo),
            float(env.steer),
        ]
        result = controller.run(
            reference(4.0, True, env.timestamp, state, "integration"),
            state,
            episode="integration",
            observation_time=env.timestamp,
        )
        applied = apply_step(env, result["proposed"], step)
        integration.append(
            dict(
                tick=i,
                controller=result,
                application=applied,
                actor=env.render_kwargs["planning"]["actor"],
            )
        )
    return dict(
        schema="sentinel.iter144.raw.v1",
        fixture_status="completed",
        environment=dict(
            python=platform.python_version(),
            platform=platform.platform(),
            numpy=np.__version__,
            torch=torch.__version__,
            scipy=scipy.__version__,
            torch_threads=torch.get_num_threads(),
            device="cpu",
        ),
        inputs={p: hashlib.sha256(b).hexdigest() for p, b in inputs.items()},
        straight=straight,
        full_sampler=full,
        ego=ego,
        jacobians=jacobians,
        solver=solver,
        integration=dict(
            initial_actor=initial["actor"],
            rows=integration,
            selections=world.selections,
            events=world.executors["actor"].events,
            stop_reason="fixture_horizon",
        ),
        exclusions=[
            "renderer",
            "collision",
            "route termination",
            "map lanes",
            "CUDA transforms",
            "live assets",
            "full reset including sensor/steering state",
            "nominal planner process",
            "released monitor",
            "wall deadline policy",
        ],
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = run(args.root)
        code = 0
    except Exception as exc:
        result = dict(fixture_status="invalid", error_type=type(exc).__name__, error=str(exc))
        code = 2
    with args.output.open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps(dict(fixture_status=result["fixture_status"], returncode=code)))
    return code


if __name__ == "__main__":
    sys.exit(main())
