"""Finite route-reference candidates and explicit bounded diagnostic controls."""

import math
import numpy as np


def candidates(plan):
    specs = []
    for speed in plan["candidate_speeds"]:
        specs.append(dict(speed=speed, offset=0.0, start=0.0, length=10.0))
    for speed in plan["candidate_speeds"]:
        for offset in plan["candidate_offsets"]:
            for start in plan["shift_starts"]:
                for length in plan["shift_lengths"]:
                    specs.append(dict(speed=speed, offset=offset, start=start, length=length))
    return [dict(id=f"maneuver_{i:03d}", **row) for i, row in enumerate(specs)]


def quintic(value):
    z = np.clip(value, 0, 1)
    return z**3 * (10 - 15 * z + 6 * z**2)


def reference(route, spec, plan):
    path = np.asarray(route, dtype=float)[:, ::-1]
    path = path[np.r_[True, np.linalg.norm(np.diff(path, axis=0), axis=1) > 1e-12]]
    if len(path) < 2:
        raise ValueError("degenerate_route")
    arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))]
    tangent = np.empty_like(path)
    tangent[0], tangent[-1] = path[1] - path[0], path[-1] - path[-2]
    tangent[1:-1] = path[2:] - path[:-2]
    norms = np.linalg.norm(tangent, axis=1)
    if np.any(norms <= 1e-12):
        raise ValueError("degenerate_tangent")
    tangent /= norms[:, None]
    offset = spec["offset"] * quintic((arc - spec["start"]) / spec["length"])
    offset *= 1 - quintic((arc - plan["return_start"]) / plan["return_length"])
    shifted = path + np.c_[-tangent[:, 1], tangent[:, 0]] * offset[:, None]
    shifted_arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(shifted, axis=0), axis=1))]
    return shifted, shifted_arc


def command(state, path, arc, spec, plan):
    x, y, heading, velocity, steering = state
    nearest = int(np.argmin(np.sum((path - [x, y]) ** 2, axis=1)))
    station = min(arc[-1], arc[nearest] + plan["lookahead"])
    target = np.array([np.interp(station, arc, path[:, j]) for j in (0, 1)])
    dx, dy = target - [x, y]
    distance = math.hypot(dx, dy)
    if distance <= 1e-12:
        desired = 0.0
    else:
        curvature = 2 * math.sin(math.atan2(dy, dx) - heading) / distance
        desired = math.atan(plan["wheelbase"] * curvature)
    desired = float(np.clip(desired, -math.pi / 3, math.pi / 3))
    rate = float(np.clip((desired - steering) / plan["dt"], -math.pi / 12, math.pi / 12))
    acc = float(np.clip((spec["speed"] - velocity) / plan["dt"], -2, 2))
    return [acc, rate]


def transition(state, action, plan):
    x, y, heading, velocity, steering = state
    dt = plan["dt"]
    velocity += action[0] * dt
    steering += action[1] * dt
    return [
        x + velocity * math.cos(heading) * dt,
        y + velocity * math.sin(heading) * dt,
        heading + velocity * math.tan(steering) * dt / plan["wheelbase"],
        velocity,
        steering,
    ]


def limits(state, action, plan):
    velocity, steering = state[3:]
    yaw_rate = velocity * math.tan(steering) / plan["wheelbase"]
    return bool(
        abs(action[0]) <= plan["acceleration_bound"] + 1e-12
        and abs(action[1]) <= math.pi / 12 + 1e-12
        and abs(steering) <= math.pi / 3 + 1e-12
        and -1e-12 <= velocity <= plan["speed_bound"] + 1e-12
        and abs(yaw_rate) <= plan["max_yaw_rate"] + 1e-12
        and abs(velocity * yaw_rate) <= plan["max_lateral_acceleration"] + 1e-12
    )
