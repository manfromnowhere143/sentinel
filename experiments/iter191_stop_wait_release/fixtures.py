"""Constructed straight and curved interfaces; no retained winning trace."""

import math
from experiments.iter189_uniform_timing_eligibility.fixtures import case as straight

LABELS = ("untimed", "timed_straight", "timed_curve")


def case(label):
    if label not in LABELS:
        raise ValueError("fixture_identity")
    value = straight()
    value["id"] = "constructed_" + label
    if label == "untimed":
        return value
    value["geometry"]["comparators"] = {"checkpoint": dict(hazard_time=0.25, rc=0.7)}
    value["geometry"]["reset"] = [17.85, 0.0, 0.0, 0.125, 0.0]
    value["points"] = [[50.0, 0.5, 50.0]]
    if label == "timed_curve":
        radius = 20
        theta = 71.4 / 80 * math.pi / 2
        value["geometry"]["route"] = [
            [radius * (1 - math.cos(i / 80 * math.pi / 2)), radius * math.sin(i / 80 * math.pi / 2)]
            for i in range(81)
        ]
        value["geometry"]["reset"] = [
            radius * math.sin(theta),
            radius * (1 - math.cos(theta)),
            theta,
            0.125,
            math.atan(2.7 / radius),
        ]
    return value


def request(case, target_frame=8, consumed=0, debit=0):
    state = case["geometry"]["reset"]
    route = case["geometry"]["route"]
    goal = math.ceil(0.9 * len(route)) - 1
    a, b = route[goal - 1], route[goal + 1]
    target = [
        route[goal][1],
        route[goal][0],
        math.atan2(b[0] - a[0], b[1] - a[1]),
        2,
        0,
        target_frame,
    ]
    return dict(
        id="constructed_request",
        case=case["id"],
        parent=1,
        before=[*state, 0],
        target=target,
        consumed_attempts=consumed,
        call=1,
        charged_original_wall=debit,
        nodes={
            "1": dict(kind=0, node=1, parent=0, token=0, steps=0, state=[*state, 0], target=None)
        },
    )
