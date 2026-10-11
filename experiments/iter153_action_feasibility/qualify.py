"""Retained-source and constructed geometry/control qualification before search."""

import ast
from copy import deepcopy
import itertools
import math
from pathlib import Path
from types import SimpleNamespace
import numpy as np

from . import check, geometry, planner
from .inputs import BASE, document, load, require, digest

ENV = "experiments/iter136_hugsim_recoverability_canary/proof/source/HUGSIM/sim/hugsim_env/envs/hug_sim.py.txt"
SCORE = "experiments/iter145_constrained_execution/source/score_calculator.py.txt"


def source_functions(root):
    tree = ast.parse((root / ENV).read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "HUGSimEnv")
    step = deepcopy(
        next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "step")
    )
    end = next(
        i
        for i, n in enumerate(step.body)
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "terminated" for t in n.targets)
    )
    step.body = step.body[:end]
    route = deepcopy(
        next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "route_completion")
    )
    route.decorator_list = []
    rectangle = deepcopy(
        next(
            n
            for n in ast.parse((root / SCORE).read_text()).body
            if isinstance(n, ast.FunctionDef) and n.name == "create_rectangle"
        )
    )
    namespace = dict(np=np, ShapelyPolygon=lambda points: list(points))
    module = ast.Module(body=[step, route, rectangle], type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), "<retained-source-slices>", "exec"), namespace)
    return namespace


def run(root):
    root = Path(root).resolve()
    plan = document(root / BASE / "PLAN.json")
    retained = load(root)
    funcs = source_functions(root)
    transition_rows = []
    for heading, velocity, steer, acc, rate in itertools.product(
        (-0.7, 0, 0.8), (1, 4), (-0.2, 0.2), (-2, 2), (-math.pi / 12, math.pi / 12)
    ):
        state = [1.2, -0.3, heading, velocity, steer]
        env = SimpleNamespace(
            timestamp=0,
            dt=0.25,
            planner=None,
            kinematic=dict(Lr=1.35, Lf=1.35),
            velo=velocity,
            steer=steer,
            vab=np.array([state[1], state[0]]),
            vr=np.array([0.0, heading, 0.0]),
        )
        funcs["step"](env, dict(acc=acc, steer_rate=rate))
        source = [env.vab[1], env.vab[0], env.vr[1], env.velo, env.steer]
        action = [acc, rate]
        producer, independent = planner.transition(state, action, plan), check.motion(state, action)
        check.near(producer, source, 1e-12)
        check.near(independent, source, 1e-12)
        transition_rows.append(
            dict(
                state=state,
                action=action,
                source=[float(v) for v in source],
                producer=producer,
                independent=independent,
            )
        )
    rects = []
    for heading, width, length in itertools.product((-1.2, 0, 0.6), (1.6, 2.3), (3.0, 4.2)):
        source = funcs["create_rectangle"](2.0, -1.0, width, length, heading)
        points = geometry.polygon([2.0, -1.0, width, length, heading]).tolist()
        check.near(points, source, 1e-12)
        rects.append(dict(box=[2.0, -1.0, width, length, heading], source=source))
    box_pairs = []
    for x, y, h in itertools.product((-4.0, 0.0, 3.0), (-2.0, 0.0, 2.0), (-0.5, 0.0, 0.7)):
        a = [0, 0, 1.6, 3, 0]
        b = [x, y, 1.9, 4.2, h]
        first, second = geometry.separation(a, b), check.gap(a, b)
        check.near(first, second, 1e-12)
        box_pairs.append(dict(first=a, second=b, producer_gap=first, independent_gap=second))
    a, b = [0, 0, 0, 4, 0], [4, 0, 0, 4, 0]
    dims = [1.0, 1.0, 1.0]
    obs = [[2, 0, 1, 1, 0]]
    require(
        check.gap([0, 0, 1, 1, 0], obs[0]) > 0 and check.gap([4, 0, 1, 1, 0], obs[0]) > 0,
        "tunneling_endpoints",
    )
    require(
        not check.swept(a, b, dims, obs, plan) and not geometry.sweep_clear(a, b, dims, obs, plan),
        "tunneling_rejected",
    )
    require(check.gap([0, 0, 2, 2, 0], [2, 0, 2, 2, 0]) == 0, "touching_closed_set")
    # Actual retained source route method, including original sample denominator.
    route_rows = []
    poses = np.tile(np.eye(4), (len(retained["route"]), 1, 1))
    poses[:, 0, 3] = np.asarray(retained["route"])[:, 0]
    poses[:, 2, 3] = np.asarray(retained["route"])[:, 1]
    for x, y in ((0.0, 0.0), (30.0, -3.0), (95.0, -16.0)):
        env = SimpleNamespace(ground_model=(poses, 0, []), vab=np.array([y, x]))
        rc, dist = funcs["route_completion"](env)
        result = geometry.route_outcome([x, y, 0, 1, 0], retained["route"])
        check.near([result["rc"], result["distance"]], [rc, dist], 1e-12)
        route_rows.append(dict(position=[x, y], source_rc=float(rc), source_distance=float(dist)))
    return dict(
        status="supported",
        geometry_sha256=digest(retained),
        historical_actions_replayed=retained["historical_actions_replayed"],
        source_transition_fixtures=transition_rows,
        source_rectangle_fixtures=rects,
        independent_rectangle_pairs=box_pairs,
        source_route_fixtures=route_rows,
        known_bad_geometry=dict(endpoint_only_contact_rejected=True, touching_is_contact=True),
        scope="CPU source slices: renderer, ground height, point-cloud background and GEOS omitted. No new driving observation.",
    )
