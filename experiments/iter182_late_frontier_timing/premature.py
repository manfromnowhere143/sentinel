"""Conservative next-position completion bound, exact affine gap minimization.

Computed libm coefficients and declared outward guards; see MATHEMATICS.md.
No collision, action-sampling or producer-search imports.
"""

from fractions import Fraction as F
import math

from .common import require


def rational(value):
    return [str(value.numerator), str(value.denominator)]


def completion_bound(state, frame, geometry, old, target):
    require(
        len(state) == 5 and all(type(v) in (int, float) and math.isfinite(v) for v in state),
        "completion_state",
    )
    require(
        type(frame) is int and type(target) is int and 0 < target - frame <= 8, "completion_clock"
    )
    require(
        max(map(abs, state[:3])) <= 1000 and -1e-12 <= state[3] <= 6 + 1e-12, "completion_domain"
    )
    require(
        old["dt"] == 0.25 and old["acceleration_bound"] == 2 and old["speed_bound"] == 6,
        "completion_dynamics",
    )
    require(
        target == max(c["hazard_time"] * 4 for c in geometry["comparators"].values()),
        "completion_target",
    )
    route = [[F(p[1]), F(p[0])] for p in geometry["route"]]
    require(route and max(abs(v) for p in route for v in p) <= 1000, "completion_route")
    outside = [i for i in range(len(route)) if (i + 1) / (0.9 * len(route)) < 1]
    inside = [i for i in range(len(route)) if i not in outside]
    require(outside and inside, "completion_partition")
    record = dict(
        frame=frame,
        target_frame=target,
        applicable=frame + 1 < target,
        noncompleting_indices=outside,
        velocity_interval=None,
        box=None,
        anchor=None,
        minimum_squared_distance_gap=None,
        excluded=False,
    )
    if not record["applicable"]:
        return record
    eps, guard = F(2, 10**12), F(1, 10**8)
    velocity = F(state[3])
    lo = max(-eps, velocity - (2 + eps) / 4 - eps)
    hi = min(6 + eps, velocity + (2 + eps) / 4 + eps)
    require(lo <= hi, "completion_velocity")
    box = []
    for position, coefficient in zip(state[:2], (math.cos(state[2]), math.sin(state[2]))):
        candidates = [F(position) + v * F(coefficient) / 4 for v in (lo, hi)]
        box.append((min(candidates) - guard, max(candidates) + guard))
    center = [(a + b) / 2 for a, b in box]
    anchor = min(inside, key=lambda i: (sum((center[k] - route[i][k]) ** 2 for k in (0, 1)), i))
    q0 = route[anchor]
    margins = []
    for j in outside:
        constant = sum(route[j][k] ** 2 - q0[k] ** 2 for k in (0, 1))
        margins.append(
            constant + sum(min(2 * (q0[k] - route[j][k]) * z for z in box[k]) for k in (0, 1))
        )
    gap = min(margins)
    record.update(
        velocity_interval=[rational(lo), rational(hi)],
        box=[[rational(a), rational(b)] for a, b in box],
        anchor=anchor,
        minimum_squared_distance_gap=rational(gap),
        excluded=gap > F(1, 10**6),
    )
    return record
