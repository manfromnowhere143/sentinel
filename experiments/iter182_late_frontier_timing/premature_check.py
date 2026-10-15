"""Independent corner verification; no producer-bound import."""

from fractions import Fraction
import itertools
import math

from .common import require


def pair(v):
    return [str(v.numerator), str(v.denominator)]


def check_completion(record, state, frame, geometry, old, target):
    require(
        set(record)
        == {
            "frame",
            "target_frame",
            "applicable",
            "noncompleting_indices",
            "velocity_interval",
            "box",
            "anchor",
            "minimum_squared_distance_gap",
            "excluded",
        },
        "completion_schema",
    )
    require(
        type(frame) is int
        and type(target) is int
        and 1 <= target - frame <= 8
        and record["frame"] == frame
        and record["target_frame"] == target,
        "completion_clock",
    )
    require(
        type(record["applicable"]) is bool and type(record["excluded"]) is bool, "completion_types"
    )
    require(
        len(state) == 5
        and all(type(v) in (int, float) and math.isfinite(v) for v in state)
        and all(abs(v) <= 1000 for v in state[:3])
        and -1e-12 <= state[3] <= 6 + 1e-12,
        "completion_domain",
    )
    require(
        old["dt"] == 0.25 and old["speed_bound"] == 6 and old["acceleration_bound"] == 2,
        "completion_dynamics",
    )
    require(
        max(c["hazard_time"] for c in geometry["comparators"].values()) == target / 4,
        "completion_target",
    )
    points = [(Fraction(p[1]), Fraction(p[0])) for p in geometry["route"]]
    require(points and all(abs(v) <= 1000 for p in points for v in p), "completion_route")
    rejected = [j for j in range(len(points)) if (j + 1) / (0.9 * len(points)) >= 1]
    accepted = [j for j in range(len(points)) if j not in rejected]
    require(
        accepted and rejected and record["noncompleting_indices"] == accepted,
        "completion_partition",
    )
    applicable = frame < target - 1
    require(record["applicable"] == applicable, "completion_applicability")
    if not applicable:
        require(
            record["excluded"] is False
            and all(
                record[k] is None
                for k in ("velocity_interval", "box", "anchor", "minimum_squared_distance_gap")
            ),
            "completion_inapplicable",
        )
        return False
    padding = Fraction(1, 500000000000)
    speeds = [
        Fraction(state[3]) + sign * (Fraction(1, 2) + padding / 4 + padding) for sign in (-1, 1)
    ]
    speeds[0] = max(-padding, speeds[0])
    speeds[1] = min(6 + padding, speeds[1])
    require(
        speeds[0] <= speeds[1] and record["velocity_interval"] == list(map(pair, speeds)),
        "completion_velocity",
    )
    intervals = []
    for k in (0, 1):
        trig = math.cos(state[2]) if k == 0 else math.sin(state[2])
        ends = sorted(Fraction(state[k]) + s * Fraction(trig) / 4 for s in speeds)
        intervals.append([ends[0] - Fraction(1, 100000000), ends[1] + Fraction(1, 100000000)])
    require(record["box"] == [[pair(z) for z in axis] for axis in intervals], "completion_box")
    cx, cy = [sum(axis) / 2 for axis in intervals]
    closest = min(((cx - points[j][0]) ** 2 + (cy - points[j][1]) ** 2, j) for j in rejected)[1]
    require(type(record["anchor"]) is int and record["anchor"] == closest, "completion_anchor")
    x0, y0 = points[closest]
    corners = list(itertools.product(*intervals))
    gap = min(
        (x - points[j][0]) ** 2 + (y - points[j][1]) ** 2 - (x - x0) ** 2 - (y - y0) ** 2
        for j in accepted
        for x, y in corners
    )
    require(
        record["minimum_squared_distance_gap"] == pair(gap)
        and record["excluded"] == (gap > Fraction(1, 1000000)),
        "completion_exclusion",
    )
    return record["excluded"]
