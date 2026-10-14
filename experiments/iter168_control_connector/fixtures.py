"""Disclosed constructive control tasks, independent scalar witnesses.

Targets are generated from witnesses; their controls never enter the connector API.
These fixtures qualify modeled behavior, not held-out generalization.
"""

import json
import math
from pathlib import Path

import numpy as np

from experiments.iter153_action_feasibility.check import motion
from .common import BASE, write


def cases():
    specs = []
    for v in (0.125, 0.375, 1.25, 2.0):
        actions, speed = [], v
        while speed > 0:
            a = -min(2, speed * 4)
            actions.append([a, 0.0])
            speed += a / 4
        stop_frame = len(actions)
        specs.append(
            (f"stop_{v}", [0.0, 0.0, 0.0, v, 0.0], actions + [[0.0, 0.0]] * 2, 0, stop_frame)
        )
    for n, steer in ((4, 0.0), (8, 0.13)):
        specs.append((f"wait_{n}", [0.0, 0.0, 0.0, 0.0, steer], [[0.0, 0.0]] * n, n, None))
    for n in (2, 4):
        specs.append(
            (
                f"wait_restart_{n}",
                [0.0, 0.0, 0.0, 0.0, 0.0],
                [[0.0, 0.0]] * n + [[2.0, 0.0]] * 2,
                n,
                None,
            )
        )
    for n in (1, 4):
        for sign in (1, -1):
            specs.append(
                (
                    f"turn_{2 * n}_{'left' if sign == 1 else 'right'}",
                    [0.0, 0.0, 0.0, 2.0, 0.0],
                    [[0.0, sign * math.pi / 12]] * n + [[0.0, -sign * math.pi / 12]] * n,
                    0,
                    None,
                )
            )
    output = []
    for name, reset, actions, wait_until, stop_from in specs:
        states = [reset]
        for action in actions:
            states.append(motion(states[-1], action))
        route = [[0.0, k / 8] for k in range(161)]
        comparators = {}
        for f in sorted({max(1, len(actions) // 2), len(actions)}):
            s = states[f]
            nearest = min(
                range(len(route)), key=lambda i: (math.hypot(route[i][1] - s[0], s[1]), i)
            )
            comparators[str(f)] = dict(hazard_time=f / 4, rc=(nearest + 1) / (0.9 * len(route)))
        geometry = dict(
            reset=reset,
            route=route,
            ego_dimensions=[1.6, 3.0, 1.5],
            obstacles=[[4.0, -4.0, 0.0, 0.5, 0.5, 1.0, 0.0]],
            comparators=comparators,
        )
        points = [
            [side * 4 + j * 0.012, 0.5, x + k * 0.012]
            for x in (0, 2, 4, 6)
            for side in (-1, 1)
            for j in range(-5, 6)
            for k in range(-5, 6)
        ]
        task = dict(
            target=states[-1],
            terminal_frame=len(actions),
            tolerance=[0.02, 0.02, 0.002, 0.01, 0.002],
            wait_until=wait_until,
            stop_from=stop_from,
        )
        output.append(
            dict(
                id=name,
                geometry=geometry,
                task=task,
                points=np.asarray(points, dtype="<f4").tolist(),
                ground=np.eye(4)[None].tolist(),
                witness_actions=actions,
            )
        )
    return output


if __name__ == "__main__":
    result = cases()
    write(Path.cwd() / BASE / "CASES.json", result)
    print(
        json.dumps(dict(cases=len(result), actions=sum(len(c["witness_actions"]) for c in result)))
    )
