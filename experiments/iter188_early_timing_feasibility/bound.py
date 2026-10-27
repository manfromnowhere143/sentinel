"""Necessary one-step exclusion: outward binary64 box, exact affine predicate."""

from fractions import Fraction as F
import math

from .common import require


def pair(q):
    return [str(q.numerator), str(q.denominator)]


def operation(a, b, multiply=False):
    values = [x * y if multiply else x + y for x in a for y in b]
    return [math.nextafter(min(values), -math.inf), math.nextafter(max(values), math.inf)]


def certificate(state, frame, geometry, old):
    require(isinstance(state, list) and len(state) == 5, "state_shape")
    require(all(type(x) in (int, float) and math.isfinite(x) for x in state), "state_finite")
    require(type(frame) is int and 0 <= frame <= 96, "frame")
    route = geometry["route"]
    require(isinstance(route, list) and 2 <= len(route) <= 4096, "route_shape")
    require(all(isinstance(p, list) and len(p) == 2 and all(type(x) in (int, float) and math.isfinite(x) for x in p) for p in route), "route_finite")
    times = [c["hazard_time"] for c in geometry["comparators"].values()]
    require(times and all(type(t) in (int, float) and math.isfinite(t) and t >= 0 for t in times), "checkpoints")
    target = max(times) * 4
    record = dict(frame=frame, target_frame=target, status="unknown", reason=None,
                  coefficients=None, speed_interval=None, box=None, anchor=None,
                  minimum_squared_distance_gap=None, comparison_margin=None)
    if target != 32 or (old["dt"], old["acceleration_bound"], old["speed_bound"]) != (0.25, 2, 6):
        record["reason"] = "unsupported_contract"
        return record
    if max(map(abs, state[:3])) > 1000 or not -1e-12 <= state[3] <= 6 + 1e-12 or any(abs(v) > 1000 for p in route for v in p):
        record["reason"] = "outside_numeric_contract"
        return record
    if frame + 1 >= target:
        record["reason"] = "next_frame_not_early"
        return record
    sites = [(F(p[1]), F(p[0])) for p in route]
    completing = [i for i in range(len(sites)) if (i + 1) / (0.9 * len(sites)) >= 1]
    noncompleting = [i for i in range(len(sites)) if i not in completing]
    require(completing and noncompleting, "route_partition")
    acceleration = 2 + 1e-12
    speed = operation([state[3]] * 2, operation([-acceleration, acceleration], [0.25] * 2, True))
    speed = [max(-1e-12, speed[0]), min(6 + 1e-12, speed[1])]
    require(speed[0] <= speed[1], "speed_interval")
    coefficients = [math.cos(state[2]), math.sin(state[2])]
    require(all(math.isfinite(c) and abs(c) <= 1 for c in coefficients), "coefficient_domain")
    box = [operation([p] * 2, operation(operation(speed, [c] * 2, True), [0.25] * 2, True)) for p, c in zip(state[:2], coefficients)]
    require(all(abs(z) < 1002 for axis in box for z in axis), "enclosure_domain")
    rectangle = [list(map(F, axis)) for axis in box]
    center = [sum(axis) / 2 for axis in rectangle]
    anchor = min(completing, key=lambda i: (sum((center[k] - sites[i][k]) ** 2 for k in (0, 1)), i))
    q = sites[anchor]
    gaps = [sum(sites[i][k] ** 2 - q[k] ** 2 + min(2 * (q[k] - sites[i][k]) * x for x in rectangle[k]) for k in (0, 1)) for i in noncompleting]
    gap = min(gaps)
    margin = F(1, 2**23)
    excluded = gap > margin
    record.update(status="excluded" if excluded else "unknown", reason="forced_premature_completion" if excluded else "not_certified",
                  coefficients=coefficients, speed_interval=speed, box=box, anchor=anchor,
                  minimum_squared_distance_gap=pair(gap), comparison_margin=pair(margin))
    return record
