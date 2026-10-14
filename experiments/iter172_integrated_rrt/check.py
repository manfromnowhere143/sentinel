"""Separate scalar physics and sequence-token/accounting admission.

No producer controller, native bridge or vector geometry imports. All attempted
motion is checked; full scalar masks cover returned paths. Native tree search and
unselected background masks are not independently reconstructed.
"""

import argparse
import json
import math
from pathlib import Path
import struct
import time

from experiments.iter153_action_feasibility.check import near
from experiments.iter168_control_connector.check import physical, completed
from experiments.iter169_full_horizon_control.check import variables, objective
from experiments.iter164_monitor_time_continuation.path_check import verify_path
from experiments.iter162_source_grouping_qualification.check import completion_check
from .common import BASE, read, require, rss, write
from .records import committed


def distance(a, b):
    delta = [a[i] - b[i] for i in range(6)]
    delta[2] = math.remainder(delta[2], 2 * math.pi)
    return math.sqrt(sum((delta[i] * [1, 1, 2, 0.5, 2, 0.01][i]) ** 2 for i in range(6)))


def task_check(before, target, task, plan):
    require(
        len(before) == len(target) == 6 and all(math.isfinite(v) for v in before + target),
        "connection_domain",
    )
    require(
        float(before[5]).is_integer() and 0 <= before[5] <= plan["max_actions"], "connection_clock"
    )
    remaining = plan["max_actions"] - int(before[5])
    if remaining == 0:
        require(task is None, "horizon_task")
        return
    horizon = min(plan["connection_horizon"], remaining, max(1, math.ceil(target[5] - before[5])))
    require(
        task
        == dict(
            target=target[:5],
            terminal_frame=horizon,
            tolerance=plan["target_tolerance"],
            wait_until=0,
            stop_from=None,
        ),
        "target_binding",
    )


def outcome(state, geometry):
    d = [math.hypot(p[0] - state[1], p[1] - state[0]) for p in geometry["route"]]
    i = min(range(len(d)), key=lambda k: (d[k], k))
    return dict(nearest=i, distance=d[i], rc=(i + 1) / (0.9 * len(d)))


def evaluation(row, connection, case, old):
    task = connection["task"]
    before = connection["before"]
    target = connection["target"]
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
    choices = range(1, prefix + 1) if interrupted is None else []
    selected = (
        min(choices, key=lambda k: (distance([*trace[k]["state"], trace[k]["frame"]], target), k))
        if choices
        else 0
    )
    if world:
        selected = prefix
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
        k = r["selected_prefix"]
        node = r["trace"][k]
        return (
            not r["world_complete"],
            distance([*node["state"], node["frame"]], c["target"]),
            r["id"],
            k,
        )

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


def path_tokens(native, connections, trace, old, reset):
    rows = native["rows"]
    ids = native["selected_connections"]
    if not rows:
        require(len(trace) == 1 and not ids, "empty_native_path")
        return
    require(rows[0] == [*reset, 0, 0, 0, 0], "native_root")
    require(len(rows) == len(ids) + 1, "native_path_count")
    assembled = []
    before = [*reset, 0]
    for row, token in zip(rows[1:], ids):
        require(
            type(token) is int and token in connections and row[6] == token and row[7] == 0,
            "native_token",
        )
        c = connections[token]
        require(
            c["before"] == before and c["result"] is not None and len(c["trace"]) > 1,
            "native_parent",
        )
        segment = c["trace"]
        end = segment[-1]
        require(
            row[:6] == [*end["state"], end["frame"]] and row[8] == (len(segment) - 1) * old["dt"],
            "native_duration_endpoint",
        )
        assembled.extend(segment[1:])
        before = row[:6]
    require(assembled == trace[1:], "native_expansion")


def check(root, commit):
    started = time.monotonic()
    plan = json.loads(read(root, BASE / "PLAN.json"))
    raw = root / BASE / "proof/search_raw"
    execution = committed(root, raw, commit, plan)
    old = json.loads(read(root, "experiments/iter153_action_feasibility/PLAN.json"))
    cases = json.loads(read(root, "experiments/iter161_grouping_width_ablation/CASES.json"))
    require(
        len(execution["records"]) == len(plan["cases"]) == len(plan["seeds"]) == 4, "population"
    )
    records = []
    for name, seed, record in zip(plan["cases"], plan["seeds"], execution["records"]):
        case = next(c for c in cases if c["id"] == name)
        folder = raw / name
        result = json.loads(read(folder, "result.json"))
        require(
            result == record and result["case"] == name and result["seed"] == seed, "case_identity"
        )
        events = [json.loads(line) for line in read(folder, "events.jsonl").splitlines()]
        connections = {}
        pending = []
        attempts = 0
        queries = 1
        nodes = {tuple([*case["geometry"]["reset"], 0])}
        native = []
        for row in events:
            require(time.monotonic() - started < plan["search_checker_seconds"], "checker_deadline")
            if row["kind"] == "native_path":
                native.append(row)
                continue
            require(row["call"] == len(connections) + 1, "connection_order")
            if row["kind"] != "connection":
                pending.append(row)
                continue
            require(tuple(row["before"]) in nodes, "tree_parent")
            n, q = connection_check(
                row, pending, case, old, plan, plan["attempt_budget"] - attempts
            )
            attempts += n
            queries += q
            pending = []
            connections[row["call"]] = row
            if row["result"] is not None and len(row["trace"]) > 1:
                last = row["trace"][-1]
                nodes.add(tuple([*last["state"], last["frame"]]))
        require(not pending and len(native) == 1 and events[-1] is native[0], "event_finalization")
        require(
            attempts == result["attempts"] <= plan["attempt_budget"]
            and result["unused_attempt_budget"] == plan["attempt_budget"] - attempts,
            "outer_budget",
        )
        require(
            queries == result["queries"] and len(connections) == result["directed_calls"],
            "outer_counts",
        )
        accepted = sum(
            c["result"] is not None and len(c["trace"]) > 1 for c in connections.values()
        )
        require(result["accepted_connections"] == accepted, "accepted_count")
        trace = json.loads(read(folder / "selected", "trace.json"))
        require(
            len(trace) <= plan["max_actions"] + 1
            and result["path_queries"] == result["materialization_queries"] == len(trace),
            "path_queries",
        )
        require(
            native[0]["selected_connections"] == result["selected_connections"]
            and native[0]["status"] == result["native_status"],
            "native_status_binding",
        )
        path_tokens(native[0], connections, trace, old, case["geometry"]["reset"])
        require(
            type(result["complete"]) is bool
            and result["complete"] == (result["native_status"] == 2),
            "exact_status",
        )
        require(
            0 < result["elapsed_seconds"] <= plan["per_run_seconds"] + 5
            and 0 < result["peak_rss_bytes"] <= plan["max_rss_bytes"],
            "worker_resources",
        )
        if result["complete"]:
            require(result["stop"] == "model_complete", "complete_stop")
        elif result["stop"] == "attempt_budget":
            require(
                attempts == plan["attempt_budget"]
                or list(connections.values())[-1]["stop"] == "attempt_reservation",
                "outer_reservation",
            )
        else:
            require(
                result["stop"] == "time_budget"
                and result["elapsed_seconds"] >= plan["per_run_seconds"],
                "outer_time",
            )
        metrics = verify_path(
            trace,
            case["geometry"],
            old,
            case["points"],
            case["ground"],
            lambda i: read(folder / "selected", f"mask_{i:03d}.bin", 40000),
            result["complete"],
            started + plan["search_checker_seconds"],
        )
        completion_check(metrics, result["complete"], len(case["geometry"]["comparators"]))
        records.append(dict(**result, **metrics, final_progress=trace[-1]["route"]["rc"]))
    passes = sum(r["complete"] for r in records)
    require(
        rss() <= plan["max_rss_bytes"]
        and time.monotonic() - started <= plan["search_checker_seconds"],
        "checker_resources",
    )
    return dict(
        iteration=172,
        phase="closed",
        status="supported" if passes == 4 else "contradicted",
        claim="The integrated released control-RRT and centered shooting connector complete the four original qualification cases under unchanged outer constraints and budgets.",
        source_commit=execution["source_commit"],
        raw_commit=commit,
        total_cases=4,
        complete_cases=passes,
        total_attempts=sum(r["attempts"] for r in records),
        total_directed_calls=sum(r["directed_calls"] for r in records),
        accepted_connections=sum(r["accepted_connections"] for r in records),
        verified_states=sum(r["verified_states"] for r in records),
        point_state_classifications=sum(
            r["verified_states"] * len(next(c for c in cases if c["id"] == r["case"])["points"])
            for r in records
        ),
        qualified_for_source_comparison=passes == 4,
        records=records,
        elapsed_seconds=time.monotonic() - started,
        peak_rss_bytes=rss(),
        source_recovery=None,
        superiority=None,
        transfer=None,
        new_driving_episodes=0,
        provider_spend=0,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--raw-commit", required=True)
    a = p.parse_args()
    result = check(a.root.resolve(), a.raw_commit)
    write(a.root.resolve() / BASE / "proof/admission.json", result)
    print(json.dumps({k: v for k, v in result.items() if k != "records"}), flush=True)
