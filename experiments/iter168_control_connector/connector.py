"""Deterministic receding lookahead, independent of the OMPL tree.

Every computed transition is charged. Common prefixes are computed once per call;
no partial expansion is used after budget exhaustion. Commit only the first edge.
"""

import math
import time

from experiments.iter153_action_feasibility.geometry import obstacles
from experiments.iter153_action_feasibility.planner import reference, transition
from experiments.iter158_constraint_aware_search.search import prior_reason
from experiments.iter167_planner_terminal_contract.adapter import distance
from .common import require, rss
from .controls import proposals


def task_reason(state, frame, task, reset):
    if frame <= task["wait_until"]:
        if any(abs(a - b) > 1e-10 for a, b in zip(state, reset)):
            return "wait_contract"
    if task["stop_from"] is not None and frame >= task["stop_from"] and abs(state[3]) > 1e-10:
        return "stop_contract"
    return None


def reached(state, frame, task):
    residual = [a - b for a, b in zip(state, task["target"])]
    residual[2] = math.remainder(residual[2], 2 * math.pi)
    return frame == task["terminal_frame"] and all(
        abs(d) <= tolerance for d, tolerance in zip(residual, task["tolerance"])
    )


def search(geometry, task, old, plan, query, emit, depth):
    require(depth in (1, 2), "lookahead")
    require(0 < task["terminal_frame"] <= plan["max_actions"], "task_horizon")
    started = time.monotonic()
    path, arc = reference(geometry["route"], dict(offset=0, start=0, length=10), old)
    boxes = obstacles(geometry)
    state = geometry["reset"]
    initial = query(state)
    reason, outcome = prior_reason(state, state, [0, 0], 0, geometry, old, boxes)
    require(reason is None and initial["decision"] == "clear", "initial_rejected")
    root = dict(
        id=0,
        parent=None,
        frame=0,
        action=None,
        state=state,
        route=outcome,
        background=initial,
        reason="clear",
    )
    trace = [root]
    attempts = queries = calls = 0
    stop = "terminal_frame"
    while trace[-1]["frame"] < task["terminal_frame"]:
        current = trace[-1]
        calls += 1
        frontier = [(current, [])]
        level = min(depth, task["terminal_frame"] - current["frame"])
        interrupted = None
        for _ in range(level):
            successors = []
            for parent, chain in frontier:
                for action in proposals(parent["state"], path, arc, old):
                    if attempts >= plan["attempt_budget"]:
                        interrupted = "attempt_budget"
                        break
                    if time.monotonic() - started >= plan["per_run_seconds"]:
                        interrupted = "time_budget"
                        break
                    require(rss() <= plan["max_rss_bytes"], "memory_budget")
                    attempts += 1
                    frame = parent["frame"] + 1
                    after = transition(parent["state"], action, old)
                    reason, outcome = prior_reason(
                        parent["state"], after, action, frame, geometry, old, boxes
                    )
                    if reason is None:
                        reason = task_reason(after, frame, task, geometry["reset"])
                    background = None
                    if reason is None:
                        queries += 1
                        background = query(after)
                        reason = background["decision"]
                    row = dict(
                        id=attempts,
                        parent=parent["id"],
                        frame=frame,
                        action=action,
                        state=after,
                        route=outcome,
                        reason=reason,
                        background=background,
                        call=calls,
                        before=parent["state"],
                    )
                    emit("attempt", row)
                    if reason == "clear":
                        successors.append((row, chain + [row]))
                if interrupted:
                    break
            frontier = successors
            if interrupted or not frontier:
                break
        chosen = None
        if frontier and not interrupted:
            chosen = min(
                frontier,
                key=lambda pair: (
                    distance(
                        [*pair[0]["state"], pair[0]["frame"]],
                        [*task["target"], task["terminal_frame"]],
                    ),
                    pair[0]["id"],
                ),
            )
        emit(
            "call",
            dict(
                call=calls,
                root=current["id"],
                depth=level,
                selected=None if chosen is None else chosen[1][0]["id"],
                leaf=None if chosen is None else chosen[0]["id"],
                interrupted=interrupted,
            ),
        )
        if chosen is None:
            stop = interrupted or "no_valid_rollout"
            break
        trace.append(chosen[1][0])
    return dict(
        trace=trace,
        complete=reached(trace[-1]["state"], trace[-1]["frame"], task),
        attempts=attempts,
        queries=queries + 1,
        calls=calls,
        stop=stop,
        elapsed_seconds=time.monotonic() - started,
        peak_rss_bytes=rss(),
    )
