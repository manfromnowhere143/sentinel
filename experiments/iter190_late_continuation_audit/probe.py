"""Fixed conditional programs and an unchanged checkpoint-beam comparator."""

import math
import time

from experiments.iter153_action_feasibility.geometry import obstacles, route_outcome
from experiments.iter153_action_feasibility.planner import command, reference, transition
from experiments.iter158_constraint_aware_search.search import prior_reason
from experiments.iter182_late_frontier_timing.probe import probe as checkpoint_probe
from .common import require, rss

PROGRAMS = [(mode, speed) for mode in ("hold", "center", "route") for speed in (2.0, 4.0, 6.0)]


def controls(state, frame, mode, speed, path, arc, old):
    routed = command(state, path, arc, {"speed": speed}, old)
    if frame > 32:
        return routed
    acceleration = max(-2.0, min(2.0, -state[3] / old["dt"]))
    rate = (
        0.0
        if mode == "hold"
        else (
            max(-math.pi / 12, min(math.pi / 12, -state[4] / old["dt"]))
            if mode == "center"
            else routed[1]
        )
    )
    return [acceleration, rate]


def chain(rows, index):
    result = []
    while index is not None:
        result.append(index)
        index = rows[index]["parent"]
    return result[::-1]


def run(method, state, frame, geometry, old, cap, query, deadline, max_rss):
    path, arc = reference(geometry["route"], dict(offset=0, start=0, length=10), old)
    boxes = obstacles(geometry)
    root = dict(
        id=0,
        parent=None,
        state=state,
        frame=frame,
        action=None,
        route=route_outcome(state, geometry["route"]),
        reason="clear",
        background=query(state),
    )
    reason, _ = prior_reason(state, state, [0.0, 0.0], frame, geometry, old, boxes)
    require(
        reason is None and root["background"]["decision"] == "clear" and root["route"]["rc"] < 1,
        "probe_root",
    )
    rows, programs, checkpoint, complete, beam = [root], [], None, None, None
    queries, stop = 1, None

    def step(parent, action):
        nonlocal queries
        require(rss() <= max_rss, "probe_memory")
        after = transition(parent["state"], action, old)
        at = parent["frame"] + 1
        rejected, outcome = prior_reason(parent["state"], after, action, at, geometry, old, boxes)
        if rejected is None and outcome["rc"] >= 1 and at < 32:
            rejected = "premature_completion"
        background = None
        if rejected is None:
            background = query(after)
            queries += 1
            rejected = background["decision"]
        row = dict(
            id=len(rows),
            parent=parent["id"],
            state=after,
            frame=at,
            action=action,
            route=outcome,
            reason=rejected,
            background=background,
        )
        rows.append(row)
        return row

    if method == "beam_then_route":
        # The first root query above is charged; the unchanged comparator makes
        # its own initial query too, and both are retained in query accounting.
        beam = checkpoint_probe(
            state,
            frame,
            geometry,
            old,
            dict(target_frame=32, per_root_attempts=cap, beam_width=16, max_rss_bytes=max_rss),
            query,
            deadline,
        )
        rows = beam.pop("attempt_records")
        queries += beam["queries"]
        if beam["witness"]:
            checkpoint = chain(rows, beam["selected"])
            parent = rows[beam["selected"]]
            if parent["route"]["rc"] >= 1:
                complete = checkpoint
                stop = "complete"
            schedule = [("route", 2.0)] if complete is None else []
        else:
            stop = beam["stop"]
            schedule = []
    else:
        require(method == "stop_wait_route", "probe_method")
        schedule = PROGRAMS
    for number, (mode, speed) in enumerate(schedule):
        parent = rows[beam["selected"]] if beam else rows[0]
        ids = chain(rows, parent["id"])
        terminal = None
        while parent["frame"] < 96:
            if len(rows) - 1 >= cap:
                terminal = stop = "attempt_budget"
                break
            if time.monotonic() >= deadline:
                terminal = stop = "time_budget"
                break
            action = (
                command(parent["state"], path, arc, {"speed": speed}, old)
                if beam
                else controls(parent["state"], parent["frame"] + 1, mode, speed, path, arc, old)
            )
            parent = step(parent, action)
            ids.append(parent["id"])
            if parent["reason"] != "clear":
                terminal = "rejected"
                break
            if parent["frame"] == 32 and checkpoint is None:
                checkpoint = list(ids)
            if parent["route"]["rc"] >= 1:
                complete = list(ids)
                terminal = stop = "complete"
                break
        terminal = terminal or "horizon"
        programs.append(dict(number=number, mode=mode, speed=speed, ids=ids, stop=terminal))
        if stop:
            break
    if stop is None:
        stop = "programs_exhausted"
    return dict(
        method=method,
        attempts=len(rows) - 1,
        queries=queries,
        rows=rows,
        programs=programs,
        beam=beam,
        checkpoint_ids=checkpoint,
        complete_ids=complete,
        stop=stop,
    )
