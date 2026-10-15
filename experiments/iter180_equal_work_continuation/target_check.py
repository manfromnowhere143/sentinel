"""Independent target indices, arc position, heading and task reconstruction."""

import math
from experiments.iter153_action_feasibility.check import near
from .common import require


def check_target(target, state, frame, geometry, target_frame):
    require(set(target) == {"nearest", "index", "station", "state", "frame"}, "target_schema")
    require(type(frame) is int and 1 <= target_frame - frame <= 4, "target_clock")
    points = geometry["route"]
    distances = [math.hypot(state[0] - p[1], state[1] - p[0]) for p in points]
    nearest = min(range(len(points)), key=lambda k: (distances[k], k))
    stations = [0.0]
    for i in range(1, len(points)):
        length = math.hypot(points[i][1] - points[i - 1][1], points[i][0] - points[i - 1][0])
        require(length > 0 and math.isfinite(length), "target_segment")
        stations.append(stations[-1] + length)
    speed = min(6.0, max(0.0, state[3]))
    station = min(stations[-1], stations[nearest] + speed * (target_frame - frame) / 4)
    index = next(k for k, s in enumerate(stations) if s >= station)
    require(
        target["nearest"] == nearest
        and target["index"] == index
        and target["frame"] == target_frame,
        "target_identity",
    )
    near(target["station"], station, 1e-12)
    j = min(index, len(points) - 2)
    heading = math.atan2(points[j + 1][0] - points[j][0], points[j + 1][1] - points[j][1])
    expected = [points[index][1], points[index][0], heading, speed, 0.0]
    near(target["state"], expected, 1e-12)
    return dict(
        target=target["state"],
        terminal_frame=target_frame - frame,
        tolerance=[0.02, 0.02, 0.002, 0.01, 0.002],
        wait_until=0,
        stop_from=None,
    )
