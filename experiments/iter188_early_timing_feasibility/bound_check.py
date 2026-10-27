"""Separate exact-operation reconstruction and corner proof; no bound import."""

from fractions import Fraction
import itertools
import math

from .common import require


def encoded(number):
    return [str(number.numerator), str(number.denominator)]


def envelope(first, second, product):
    exact = []
    for x, y in itertools.product(first, second):
        a, b = Fraction(x), Fraction(y)
        exact.append(a * b if product else a + b)
    return [math.nextafter(float(min(exact)), -math.inf), math.nextafter(float(max(exact)), math.inf)]


def verify(record, state, frame, geometry, old):
    require(set(record) == {"frame", "target_frame", "status", "reason", "coefficients", "speed_interval", "box", "anchor", "minimum_squared_distance_gap", "comparison_margin"}, "certificate_fields")
    require(isinstance(state, list) and len(state) == 5 and all(type(z) in (int, float) and math.isfinite(z) for z in state), "check_state")
    require(type(frame) is int and 0 <= frame <= 96 and type(record["frame"]) is int and record["frame"] == frame, "check_frame")
    route = geometry["route"]
    require(isinstance(route, list) and 2 <= len(route) <= 4096 and all(isinstance(q, list) and len(q) == 2 and all(type(z) in (int, float) and math.isfinite(z) for z in q) for q in route), "check_route")
    deadlines = [c["hazard_time"] for c in geometry["comparators"].values()]
    require(deadlines and all(type(t) in (int, float) and math.isfinite(t) and t >= 0 for t in deadlines), "check_deadlines")
    target = max(deadlines) / 0.25
    require(type(record["target_frame"]) in (int, float) and record["target_frame"] == target, "target_frame")
    reason = None
    if target != 32 or old["dt"] != 0.25 or old["speed_bound"] != 6 or old["acceleration_bound"] != 2:
        reason = "unsupported_contract"
    elif any(abs(z) > 1000 for z in state[:3]) or not -1e-12 <= state[3] <= 6 + 1e-12 or any(abs(z) > 1000 for q in route for z in q):
        reason = "outside_numeric_contract"
    elif frame >= target - 1:
        reason = "next_frame_not_early"
    numeric = ("coefficients", "speed_interval", "box", "anchor", "minimum_squared_distance_gap", "comparison_margin")
    if reason is not None:
        require(record["status"] == "unknown" and record["reason"] == reason and all(record[k] is None for k in numeric), "unknown_contract")
        return False
    scalar = float(2 + 1e-12)
    acceleration_delta = envelope((-scalar, scalar), (0.25, 0.25), True)
    speeds = envelope((state[3], state[3]), acceleration_delta, False)
    speeds[0], speeds[1] = max(-1e-12, speeds[0]), min(6 + 1e-12, speeds[1])
    require(speeds[0] <= speeds[1] and record["speed_interval"] == speeds, "speed_enclosure")
    coefficients = [math.cos(state[2]), math.sin(state[2])]
    require(all(math.isfinite(c) and abs(c) <= 1 for c in coefficients) and record["coefficients"] == coefficients, "source_coefficients")
    intervals = []
    for axis in (0, 1):
        movement = envelope(speeds, (coefficients[axis], coefficients[axis]), True)
        movement = envelope(movement, (0.25, 0.25), True)
        intervals.append(envelope((state[axis], state[axis]), movement, False))
    require(record["box"] == intervals and all(abs(z) < 1002 for axis in intervals for z in axis), "position_enclosure")
    require(all(type(z) in (int, float) and math.isfinite(z) for z in record["coefficients"] + record["speed_interval"] + [z for axis in record["box"] for z in axis]), "numeric_certificate_types")
    points = [(Fraction(q[1]), Fraction(q[0])) for q in route]
    yes, no = [], []
    for index in range(len(points)):
        (yes if (index + 1) / (0.9 * len(points)) >= 1 else no).append(index)
    require(yes and no, "check_partition")
    cx, cy = [sum(map(Fraction, axis)) / 2 for axis in intervals]
    chosen = min(((cx - points[i][0]) ** 2 + (cy - points[i][1]) ** 2, i) for i in yes)[1]
    require(type(record["anchor"]) is int and record["anchor"] == chosen, "anchor")
    corners = list(itertools.product(*[list(map(Fraction, axis)) for axis in intervals]))
    ax, ay = points[chosen]
    gap = min((x - points[i][0]) ** 2 + (y - points[i][1]) ** 2 - (x - ax) ** 2 - (y - ay) ** 2 for i in no for x, y in corners)
    margin = Fraction(1, 8388608)
    require(record["minimum_squared_distance_gap"] == encoded(gap) and record["comparison_margin"] == encoded(margin), "exact_gap_and_margin")
    excluded = gap > margin
    require(record["status"] == ("excluded" if excluded else "unknown") and record["reason"] == ("forced_premature_completion" if excluded else "not_certified"), "certificate_conclusion")
    return excluded
