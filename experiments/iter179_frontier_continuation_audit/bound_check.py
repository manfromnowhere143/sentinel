"""Independent rational corner inequalities; no producer-bound import."""

from fractions import Fraction
import itertools
import math

from .common import require


def check_bound(record, state, frame, geometry, old, target):
    require(
        set(record)
        == {
            "frame",
            "target_frame",
            "anchor",
            "allowed_indices",
            "radius",
            "minimum_squared_distance_gap",
            "excluded",
        },
        "bound_schema",
    )
    require(
        type(record["excluded"]) is bool
        and record["frame"] == frame
        and record["target_frame"] == target
        and type(frame) is int
        and 1 <= target - frame <= 4,
        "bound_clock",
    )
    require(
        len(state) == 5
        and all(math.isfinite(v) for v in state)
        and -1e-12 <= state[3] <= 6 + 1e-12
        and all(abs(v) <= 1000 for v in state[:2]),
        "bound_domain",
    )
    require(
        old["dt"] == 0.25 and old["acceleration_bound"] == 2 and old["speed_bound"] == 6,
        "bound_dynamics",
    )
    points = [(Fraction(yx[1]), Fraction(yx[0])) for yx in geometry["route"]]
    require(points and all(abs(v) <= 1000 for q in points for v in q), "bound_route")
    checkpoints = [c for c in geometry["comparators"].values() if c["hazard_time"] == target * 0.25]
    require(bool(checkpoints), "bound_checkpoint")
    accepted = [
        j
        for j in range(len(points))
        if all(
            (j + 1) / (0.9 * len(points)) >= c["rc"] - old["progress_slack"] for c in checkpoints
        )
    ]
    remaining = [j for j in range(len(points)) if j not in accepted]
    require(
        bool(accepted) and bool(remaining) and accepted == record["allowed_indices"],
        "bound_partition",
    )
    x, y = map(Fraction, state[:2])
    squared = [
        ((x - a) ** 2 + (y - b) ** 2, j) for j, (a, b) in enumerate(points) if j in remaining
    ]
    index = min(squared)[1]
    require(index == record["anchor"], "bound_anchor")
    velocity = abs(Fraction(state[3]))
    distance = Fraction(0)
    for _ in range(target - frame):
        velocity = min(
            Fraction(6) + Fraction(2, 10**12), velocity + Fraction(1, 2) + Fraction(1, 2 * 10**12)
        )
        distance += velocity / 4 + Fraction(1, 10**8)
    require(
        record["radius"] == [str(distance.numerator), str(distance.denominator)], "bound_radius"
    )
    corners = [
        (x + a * distance, y + b * distance) for a, b in itertools.product((-1, 1), repeat=2)
    ]
    a0, b0 = points[index]
    margins = [
        ((u - points[j][0]) ** 2 + (v - points[j][1]) ** 2) - ((u - a0) ** 2 + (v - b0) ** 2)
        for j in accepted
        for u, v in corners
    ]
    margin = min(margins)
    require(
        record["minimum_squared_distance_gap"] == [str(margin.numerator), str(margin.denominator)]
        and record["excluded"] == (margin > Fraction(1, 10**6)),
        "bound_exclusion",
    )
    return record["excluded"]
