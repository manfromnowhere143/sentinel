"""Disclosed constructive cases. Witness actions never enter the search API.

The route is constructed from an executable command path. These are diagnostic
fixtures, deliberately easier than an unknown scene, not held-out road evidence.
"""

import math

import numpy as np

from experiments.iter153_action_feasibility.check import motion
from experiments.iter153_action_feasibility.geometry import route_outcome


def make_case(kind, mirror):
    sign = float(mirror)
    if kind == "bend":
        reset = [0.0, 0.0, 0.0, 2.0, 0.0]
        blocks = [(8, 0, 0), (6, 0, 1), (12, 0, 0), (6, 0, -1), (20, 0, 0)]
    elif kind == "chicane":
        reset = [0.0, 0.0, 0.0, 4.0, 0.0]
        blocks = [
            (4, -2, 0),
            (4, 0, 0),
            (6, 0, 1),
            (8, 0, 0),
            (12, 0, -1),
            (8, 0, 0),
            (6, 0, 1),
            (16, 0, 0),
        ]
    else:
        raise ValueError("case_kind")
    actions = [[float(a), sign * r * math.pi / 12] for n, a, r in blocks for _ in range(n)]
    states = [reset]
    for action in actions:
        states.append(motion(states[-1], action))
    # Fine route samples avoid a different nearest-index tie convention in checks.
    route = []
    for a, b in zip(states, states[1:]):
        for k in range(4):
            route.append([a[1] + (b[1] - a[1]) * k / 4, a[0] + (b[0] - a[0]) * k / 4])
    route.append([states[-1][1], states[-1][0]])
    geometry = dict(
        reset=reset,
        route=route,
        ego_dimensions=[1.6, 3.0, 1.5],
        obstacles=[],
        comparators={},
    )
    for frame in (16, 32):
        geometry["comparators"][f"checkpoint_{frame}"] = dict(
            hazard_time=frame / 4, rc=route_outcome(states[frame], route)["rc"]
        )
    # Dense small, unique patches enforce the existing >100 source predicate.
    # Patches flank the route; they do not represent measured physical surfaces.
    points = []
    for state in states[::2]:
        x, y, heading = state[:3]
        for side in (-1, 1):
            u = y + side * 2.8 * math.cos(heading)
            v = x - side * 2.8 * math.sin(heading)
            points.extend(
                [[u + j * 0.012, 0.5, v + k * 0.012] for j in range(-5, 6) for k in range(-5, 6)]
            )
    # A separate foreground object exercises its full footprint/sweep predicate.
    anchor = states[len(states) // 2]
    x, y, heading = anchor[:3]
    geometry["obstacles"] = [
        [
            x - 4.0 * math.sin(heading),
            -(y + 4.0 * math.cos(heading)),
            0.0,
            0.5,
            0.5,
            1.0,
            -heading,
        ]
    ]
    points = np.asarray(points, dtype="<f4")
    return dict(
        id=f"{kind}_{'left' if mirror == 1 else 'right'}",
        geometry=geometry,
        points=points.tolist(),
        ground=np.eye(4)[None].tolist(),
        witness_actions=actions,
    )


def cases():
    return [make_case(kind, side) for kind in ("bend", "chicane") for side in (1, -1)]
