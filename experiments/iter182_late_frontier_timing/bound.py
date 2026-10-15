"""One-sided necessary progress bound; no collision or feasibility classifier."""

from fractions import Fraction as F
import math

from .common import require


def progress_bound(state, frame, geometry, old, target_frame):
    require(len(state) == 5 and all(math.isfinite(v) for v in state), "bound_state")
    require(
        type(frame) is int and type(target_frame) is int and 0 < target_frame - frame <= 8,
        "bound_clock",
    )
    require(-1e-12 <= state[3] <= 6 + 1e-12 and max(map(abs, state[:2])) <= 1000, "bound_domain")
    require(
        old["dt"] == 0.25 and old["speed_bound"] == 6 and old["acceleration_bound"] == 2,
        "bound_dynamics",
    )
    route = [[F(p[1]), F(p[0])] for p in geometry["route"]]
    require(route and max(abs(v) for q in route for v in q) <= 1000, "bound_route")
    constraints = [
        c["rc"] - old["progress_slack"]
        for c in geometry["comparators"].values()
        if c["hazard_time"] == target_frame / 4
    ]
    require(bool(constraints), "bound_checkpoint")
    allowed = [i for i in range(len(route)) if (i + 1) / (0.9 * len(route)) >= max(constraints)]
    other = [i for i in range(len(route)) if i not in allowed]
    require(bool(allowed) and bool(other), "bound_partition")
    p = list(map(F, state[:2]))
    anchor = min(other, key=lambda i: (sum((p[k] - route[i][k]) ** 2 for k in (0, 1)), i))
    steps = target_frame - frame
    eps = F(2, 10**12)
    radius = sum(
        min(6 + eps, abs(F(state[3])) + j * (2 + eps) / 4) / 4 for j in range(1, steps + 1)
    ) + F(steps, 10**8)
    q0 = route[anchor]
    margins = [
        sum((p[k] - route[j][k]) ** 2 - (p[k] - q0[k]) ** 2 for k in (0, 1))
        - 2 * radius * sum(abs(route[j][k] - q0[k]) for k in (0, 1))
        for j in allowed
    ]
    margin = min(margins)
    return dict(
        frame=frame,
        target_frame=target_frame,
        anchor=anchor,
        allowed_indices=allowed,
        radius=[str(radius.numerator), str(radius.denominator)],
        minimum_squared_distance_gap=[str(margin.numerator), str(margin.denominator)],
        excluded=margin > F(1, 10**6),
    )
