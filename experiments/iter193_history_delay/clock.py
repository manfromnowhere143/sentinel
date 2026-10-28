"""Static-scene time translation and exact preserved-history splicing."""

import copy
from experiments.iter153_action_feasibility.planner import transition
from experiments.iter153_action_feasibility.geometry import obstacles, route_outcome
from experiments.iter158_constraint_aware_search.search import prior_reason, summary
from .common import require


def extend(prefix, origin, delay, case, old, query):
    require(type(origin) is int and 0 < origin < len(prefix), "origin_domain")
    require(type(delay) is int and 0 <= delay <= 2, "delay_domain")
    rows = copy.deepcopy(prefix[: origin + 1])
    require([r["frame"] for r in rows] == list(range(origin + 1)), "history_clock")
    hold = rows[-1]["action"]
    for frame in range(origin + 1, origin + delay + 1):
        state = transition(rows[-1]["state"], hold, old)
        reason, _ = prior_reason(
            rows[-1]["state"],
            state,
            hold,
            frame,
            case["geometry"],
            old,
            obstacles(case["geometry"]),
        )
        background = summary(query(state))
        rows.append(
            dict(
                id=frame,
                parent=frame - 1,
                frame=frame,
                state=state,
                action=hold[:],
                route=route_outcome(state, case["geometry"]["route"]),
                background=background,
                reason=reason or background["decision"],
            )
        )
    return rows


def translate(case, planner, prefix, old):
    origin = prefix[-1]["frame"]
    require(0 <= origin < old["max_actions"], "remaining_horizon")
    local = copy.deepcopy(case)
    local["geometry"]["reset"] = prefix[-1]["state"][:]
    for checkpoint in local["geometry"]["comparators"].values():
        frame = checkpoint["hazard_time"] / old["dt"]
        require(float(frame).is_integer() and frame > origin, "past_checkpoint")
        checkpoint["hazard_time"] = (int(frame) - origin) * old["dt"]
    config = dict(planner, max_actions=old["max_actions"] - origin)
    return local, config


def join(prefix, suffix):
    require(bool(prefix) and bool(suffix), "empty_path")
    require(
        suffix[0]["frame"] == 0
        and suffix[0]["action"] is None
        and suffix[0]["state"] == prefix[-1]["state"]
        and suffix[0]["background"] == prefix[-1]["background"],
        "history_splice",
    )
    origin = prefix[-1]["frame"]
    rows = copy.deepcopy(prefix)
    for i, row in enumerate(suffix[1:], 1):
        require(row["frame"] == i, "suffix_clock")
        rows.append(dict(row, id=origin + i, parent=origin + i - 1, frame=origin + i))
    return rows
