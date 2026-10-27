"""Separate scalar kinematics and joint-control checks; no producer imports."""

import math

from .common import require


def grid(state):
    a, r = 2 + 1e-12, math.pi / 12 + 1e-12
    accelerations = [-a, -2.0, -1.0, 0.0, 1.0, 2.0, a]
    accelerations += [max(-a, min(a, -state[3] / 0.25)), max(-a, min(a, (6 - state[3]) / 0.25))]
    rates = [-r, -math.pi / 24, 0.0, math.pi / 24, r, max(-r, min(r, -state[4] / 0.25))]
    answer = []
    for acceleration in accelerations:
        for rate in rates:
            if [acceleration, rate] not in answer:
                answer.append([acceleration, rate])
    return answer


def replay(state, frame, action, geometry):
    x, y, heading, speed, steering = state
    v = speed + action[0] / 4
    d = steering + action[1] / 4
    result = [x + v * math.cos(heading) / 4, y + v * math.sin(heading) / 4,
              heading + v * math.tan(d) / 10.8, v, d]
    yaw = v * math.tan(d) / 2.7
    control = (abs(action[0]) <= 2 + 1e-12 and abs(action[1]) <= math.pi / 12 + 1e-12
               and abs(d) <= math.pi / 3 + 1e-12 and -1e-12 <= v <= 6 + 1e-12
               and abs(yaw) <= 0.95 + 1e-12 and abs(v * yaw) <= 4.89 + 1e-12)
    distances = [math.hypot(result[0] - p[1], result[1] - p[0]) for p in geometry["route"]]
    nearest = min(range(len(distances)), key=lambda i: (distances[i], i))
    rc = (nearest + 1) / (0.9 * len(distances))
    early = (frame + 1) / 4 < max(c["hazard_time"] for c in geometry["comparators"].values())
    return dict(action=action, state=result, controls_valid=control, nearest=nearest, rc=rc,
                timing_counterexample=bool(early and control and rc < 1))


def verify(row, state, frame, action, geometry, certificate):
    expected = replay(state, frame, action, geometry)
    require(set(row) == set(expected), "probe_schema")
    require(type(row["controls_valid"]) is bool and type(row["timing_counterexample"]) is bool and type(row["nearest"]) is int, "probe_types")
    require(all(row[k] == expected[k] for k in expected if k != "state"), "scalar_countercheck")
    require(len(row["state"]) == 5 and all(type(v) in (int, float) and math.isfinite(v) and abs(v - w) <= 1e-12 for v, w in zip(row["state"], expected["state"])), "scalar_motion")
    if expected["controls_valid"] and certificate["box"] is not None:
        require(all(axis[0] <= value <= axis[1] for axis, value in zip(certificate["box"], expected["state"][:2])), "countercheck_outside_box")
    require(not (certificate["status"] == "excluded" and expected["timing_counterexample"]), "verified_counterexample_defeats_exclusion")
    return expected["timing_counterexample"]
