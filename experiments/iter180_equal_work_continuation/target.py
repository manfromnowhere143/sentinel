"""Deterministic nominal-speed route target; no propagation or outcome input."""

import bisect
import math
from .common import require


def target_for(state, frame, geometry, target_frame=16):
    n = target_frame - frame
    require(type(frame) is int and 1 <= n <= 4, "target_clock")
    route = [(p[1], p[0]) for p in geometry["route"]]
    require(len(route) >= 2, "target_route")
    arc = [0.0]
    for a, b in zip(route, route[1:]):
        length = math.hypot(b[0] - a[0], b[1] - a[1])
        require(length > 0 and math.isfinite(length), "target_segment")
        arc.append(arc[-1] + length)
    nearest = min(
        range(len(route)),
        key=lambda i: (math.hypot(state[0] - route[i][0], state[1] - route[i][1]), i),
    )
    speed = max(0.0, min(6.0, state[3]))
    station = min(arc[-1], arc[nearest] + speed * n / 4)
    index = bisect.bisect_left(arc, station)
    a, b = (
        (route[index], route[index + 1])
        if index + 1 < len(route)
        else (route[index - 1], route[index])
    )
    heading = math.atan2(b[1] - a[1], b[0] - a[0])
    return dict(
        nearest=nearest,
        index=index,
        station=station,
        state=[*route[index], heading, speed, 0.0],
        frame=target_frame,
    )


def task_for(target, frame):
    return dict(
        target=target["state"],
        terminal_frame=target["frame"] - frame,
        tolerance=[0.02, 0.02, 0.002, 0.01, 0.002],
        wait_until=0,
        stop_from=None,
    )
