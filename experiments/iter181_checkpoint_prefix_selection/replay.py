"""Separate motion/accounting replay with independently specified prefix selection."""

import math
import struct

from experiments.iter153_action_feasibility.check import near
from experiments.iter168_control_connector.check import physical, completed
from experiments.iter169_full_horizon_control.check import variables, objective
from experiments.iter172_integrated_rrt.check import task_check, outcome
from .common import require
from .selection_check import selection_index, selection_rank


def evaluation(row, connection, case, old):
    task = connection["task"]
    before = connection["before"]
    trace = row["trace"]
    horizon = task["terminal_frame"]
    g = case["geometry"]
    require(1 <= len(trace) <= horizon + 1, "evaluation_length")
    root = trace[0]
    require(
        root["state"] == before[:5]
        and root["frame"] == root["id"] == int(before[5])
        and root["parent"] is None
        and root["action"] is None
        and root["reason"] == "clear",
        "evaluation_root",
    )
    params = row["values"]
    keys = variables(task)
    require(
        len(params) == len(keys)
        and all(type(v) in (int, float) and math.isfinite(v) for v in params),
        "parameters",
    )
    table = dict(zip(keys, params))
    prefix = 0
    slacks = []
    last_checkpoint = max((4 * c["hazard_time"] for c in g["comparators"].values()), default=0)
    for local, state_row in enumerate(trace):
        state = state_row["state"]
        frame = int(before[5]) + local
        require(
            state_row["id"] == state_row["frame"] == frame
            and (local == 0 or state_row["parent"] == frame - 1),
            "absolute_clock",
        )
        expected = outcome(state, g)
        require(state_row["route"]["nearest"] == expected["nearest"], "route_index")
        near(
            [state_row["route"]["rc"], state_row["route"]["distance"]],
            [expected["rc"], expected["distance"]],
        )
        if not local:
            continue
        action = [2 * table[(local, 0)], math.pi / 12 * table[(local, 1)]]
        near(state_row["action"], action, 1e-12)
        reason = physical(
            trace[local - 1]["state"], state, action, frame, dict(case, task=task), old
        )
        if reason is None and expected["rc"] >= 1 and frame < last_checkpoint:
            reason = "premature_completion"
        background = state_row["background"]
        if reason is None:
            require(isinstance(background, dict), "missing_background")
            lo, n, hi = [background[k] for k in ("certain_inside", "count", "possible_inside")]
            require(
                all(type(v) is int for v in [lo, n, hi])
                and 0 <= lo <= n <= hi <= len(case["points"]),
                "background_counts",
            )
            reason = (
                "clear" if hi <= 100 else ("collision" if lo > 100 else "numerically_ambiguous")
            )
            require(background["decision"] == reason, "background_label")
        else:
            require(background is None, "rejected_background")
        require(state_row["reason"] == reason, "attempt_reason")
        if prefix == local - 1 and reason == "clear":
            prefix = local
        if prefix == local and expected["rc"] >= 1:
            require(local == len(trace) - 1, "continued_after_completion")
        v, d = state[3:]
        omega = v * math.tan(d) / 2.7
        slacks.extend(
            [
                2 - action[0],
                2 + action[0],
                math.pi / 12 - action[1],
                math.pi / 12 + action[1],
                v,
                6 - v,
                math.pi / 3 - d,
                math.pi / 3 + d,
                0.95 - omega,
                0.95 + omega,
                4.89 - v * omega,
                4.89 + v * omega,
            ]
        )
    near(row["constraints"], slacks)
    full = len(trace) == horizon + 1
    world = prefix > 0 and prefix == len(trace) - 1 and trace[-1]["route"]["rc"] >= 1
    interrupted = row["interrupted"]
    require(
        interrupted in (None, "time_budget") and (full or world or interrupted is not None),
        "incomplete_evaluation",
    )
    require(
        row["full"] is full and row["world_complete"] is world and row["valid_prefix"] == prefix,
        "evaluation_flags",
    )
    target_complete = full and prefix == horizon and completed(trace[-1]["state"], horizon, task)
    require(row["target_complete"] is target_complete, "target_complete")
    if full:
        near([row["objective"]], [objective(trace[-1]["state"], task)])
    else:
        require(row["objective"] is None, "partial_objective")
    selected = selection_index(row, connection, case, old)
    require(row["selected_prefix"] == selected, "prefix_selection")
    return len(trace) - 1


def connection_check(c, events, case, old, plan, remaining):
    task_check(c["before"], c["target"], c["task"], plan)
    if c["result"] is None:
        require(not events and c["budget"] == remaining, "empty_connection")
        require(
            (c["task"] is None and c["stop"] == "horizon")
            or (
                c["task"] is not None
                and remaining < c["task"]["terminal_frame"]
                and c["stop"] == "attempt_reservation"
            ),
            "empty_reason",
        )
        return 0, 0
    result = c["result"]
    budget = min(plan["connection_attempt_budget"], remaining)
    require(c["budget"] == budget, "local_budget")
    ev = [r for r in events if r["kind"] == "evaluation"]
    req = [r for r in events if r["kind"] == "request"]
    require(
        [r["id"] for r in ev] == list(range(1, len(ev) + 1))
        and [r["id"] for r in req] == list(range(1, len(req) + 1)),
        "event_order",
    )
    require(result["evaluations"] == len(ev) and result["requests"] == len(req), "call_counts")
    cache = {}
    pending = None
    seen = []
    hits = 0
    for row in events:
        if row["kind"] == "request":
            require(pending is None, "missing_evaluation")
            key = struct.pack(">" + "d" * len(row["values"]), *row["values"])
            if row["stopped"]:
                require(
                    row is req[-1]
                    and row["evaluation"] is None
                    and not row["cached"]
                    and row["stopped"] == result["stop"],
                    "stopped_request",
                )
            elif row["cached"]:
                hits += 1
                require(cache.get(key) == row["evaluation"], "cache_identity")
            else:
                require(key not in cache, "duplicate_evaluation")
                pending = (key, row)
        else:
            require(row["kind"] == "evaluation" and pending is not None, "unexpected_event")
            key, request = pending
            require(
                row["id"] == request["evaluation"] and row["values"] == request["values"],
                "request_pair",
            )
            seen.append(row["id"])
            if row["full"]:
                cache[key] = row["id"]
            pending = None
    require(
        pending is None and seen == list(range(1, len(ev) + 1)) and hits == result["cache_hits"],
        "cache_accounting",
    )
    attempts = sum(evaluation(row, c, case, old) for row in ev)
    require(
        attempts == result["attempts"] <= budget
        and result["unused_attempt_budget"] == budget - attempts,
        "transition_budget",
    )
    queries = 1 + sum(r["background"] is not None for e in ev for r in e["trace"][1:])
    require(result["queries"] == queries, "query_count")
    candidates = [r for r in ev if r["selected_prefix"]]

    def rank(r):
        return selection_rank(r, c, case, old)

    best = min(candidates, key=rank) if candidates else None
    require(
        result["selected_evaluation"] == (None if best is None else best["id"]),
        "selected_evaluation",
    )
    require(
        c["trace"]
        == (
            [ev[0]["trace"][0]]
            if best is None and ev
            else c["trace"]
            if best is None
            else best["trace"][: best["selected_prefix"] + 1]
        ),
        "selected_trace",
    )
    if best is None:
        require(len(c["trace"]) == 1 and c["trace"][0]["state"] == c["before"][:5], "empty_trace")
    require(
        result["selected_prefix"] == (0 if best is None else best["selected_prefix"]),
        "selected_prefix",
    )
    require(
        result["world_complete"] is bool(best is not None and best["world_complete"]), "world_flag"
    )
    require(
        result["target_complete"]
        is bool(
            best is not None
            and best["target_complete"]
            and best["selected_prefix"] == c["task"]["terminal_frame"]
        ),
        "target_flag",
    )
    stop = result["stop"]
    require(c["stop"] == stop, "connection_stop")
    if stop == "attempt_budget":
        require(
            budget - attempts < c["task"]["terminal_frame"] and req[-1]["stopped"] == stop,
            "reservation_stop",
        )
    elif stop in ("model_complete", "qualified_candidate"):
        key = "world_complete" if stop == "model_complete" else "target_complete"
        require(
            ev[-1][key]
            and all(not e["world_complete"] and not e["target_complete"] for e in ev[:-1]),
            "first_completion",
        )
    elif stop == "time_budget":
        require(result["elapsed_seconds"] > 0, "time_stop")
    else:
        require(
            stop == "optimizer_return"
            and result["optimizer"]["returned"]
            and req[-1]["caller"] == "returned_point",
            "optimizer_stop",
        )
    optimizer = result["optimizer"]
    if optimizer["returned"]:
        require(
            optimizer["started"] and optimizer["success"] == (optimizer["status"] > 0),
            "optimizer_status",
        )
    else:
        require(
            all(
                optimizer[k] is None
                for k in (
                    "success",
                    "status",
                    "message",
                    "iterations",
                    "function_evaluations",
                    "gradient_evaluations",
                )
            ),
            "unobserved_optimizer",
        )
    require(0 < result["peak_rss_bytes"] <= plan["max_rss_bytes"], "local_memory")
    return attempts, queries
