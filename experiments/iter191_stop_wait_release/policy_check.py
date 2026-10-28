"""Separate scalar feedback specification; imports no producer or transition."""

import math
from experiments.iter153_action_feasibility.check import path_reference, policy
from .common import require


def final_frame(geometry, old):
    ticks = []
    for item in geometry["comparators"].values():
        seconds = item["hazard_time"]
        require(
            type(seconds) in (int, float) and math.isfinite(seconds) and seconds >= 0,
            "schedule_time",
        )
        tick = seconds / old["dt"]
        require(tick == int(tick), "schedule_grid")
        ticks.append(int(tick))
    return max(ticks) if ticks else None


def active(geometry, before, old, plan):
    tick = final_frame(geometry, old)
    return tick is not None and before[5] < tick and before[5] >= tick - plan["connection_horizon"]


def action(state, frame, geometry, old):
    tick = final_frame(geometry, old)
    require(tick is not None, "missing_schedule")
    if frame <= tick:
        q = state[3] / old["dt"]
        limit = old["acceleration_bound"]
        return [-limit if q > limit else limit if q < -limit else -q, 0.0]
    points, lengths = path_reference(
        geometry["route"], dict(offset=0.0, start=0.0, length=10.0), old
    )
    return policy(state, points, lengths, dict(speed=2.0), old)
