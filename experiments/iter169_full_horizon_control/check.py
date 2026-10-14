"""Scalar task/physics replay and independent shooting work accounting.

No optimizer, producer dynamics or parameterization imports. All attempted motion
and actuator slacks are replayed. Full scalar masks cover witnesses, selected
shooting paths and retained two-step comparator paths, not unselected candidates.
"""

import argparse
import json
import math
from pathlib import Path
import struct
import time

from experiments.iter153_action_feasibility.check import near
from experiments.iter168_control_connector.check import completed, physical, verify_trace
from .common import BASE, OLD, read, require, rss, write
from .records import committed


def variables(task):
    output = []
    for frame in range(1, task["terminal_frame"] + 1):
        if frame <= task["wait_until"]:
            continue
        if task["stop_from"] is None or frame < task["stop_from"]:
            output.append((frame, 0))
        output.append((frame, 1))
    return output


def objective(state, task):
    difference = [state[i] - task["target"][i] for i in range(5)]
    difference[2] = math.remainder(difference[2], 2 * math.pi)
    return sum((difference[i] / task["tolerance"][i]) ** 2 for i in range(5))


def evaluation_check(row, case, old, root):
    trace = row["trace"]
    task = case["task"]
    horizon = task["terminal_frame"]
    require(0 < len(trace) <= horizon + 1 and trace[0] == root, "evaluation_root")
    values = row["values"]
    keys = variables(task)
    require(
        len(values) == len(keys)
        and all(type(v) in (int, float) and math.isfinite(v) for v in values),
        "parameter_domain",
    )
    control = dict(zip(keys, values))
    slacks = []
    for frame, state_row in enumerate(trace[1:], 1):
        require(
            type(state_row["frame"]) is int
            and state_row["frame"] == frame
            and state_row["id"] == frame
            and state_row["parent"] == frame - 1,
            "evaluation_clock",
        )
        before = trace[frame - 1]["state"]
        state = state_row["state"]
        action = state_row["action"]
        expected = [
            -4 * before[3] if frame == task["stop_from"] else 2 * control.get((frame, 0), 0.0),
            math.pi / 12 * control.get((frame, 1), 0.0),
        ]
        near(action, expected, 1e-12)
        reason = physical(before, state, action, frame, case, old)
        background = state_row["background"]
        if reason is not None:
            require(state_row["reason"] == reason and background is None, "attempt_physics")
        else:
            require(isinstance(background, dict), "attempt_background")
            certain, count, possible = (
                background[k] for k in ("certain_inside", "count", "possible_inside")
            )
            require(
                all(type(v) is int for v in (certain, count, possible))
                and 0 <= certain <= count <= possible <= len(case["points"]),
                "background_counts",
            )
            label = (
                "clear"
                if possible <= 100
                else ("collision" if certain > 100 else "numerically_ambiguous")
            )
            require(background["decision"] == state_row["reason"] == label, "background_label")
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
    require(type(row["full"]) is bool and row["full"] == full, "evaluation_full")
    require(row["interrupted"] == (None if full else "time_budget"), "partial_reason")
    eligible = full and all(r["reason"] == "clear" for r in trace)
    require(type(row["eligible"]) is bool and row["eligible"] == eligible, "evaluation_eligible")
    require(
        type(row["complete"]) is bool
        and row["complete"] == (eligible and completed(trace[-1]["state"], len(trace) - 1, task)),
        "evaluation_complete",
    )
    if full:
        near(row["objective"], objective(trace[-1]["state"], task))
    else:
        require(row["objective"] is None, "partial_objective")


def accounting(evaluations, requests, trace, result, case, old, plan):
    require(
        [r["id"] for r in evaluations] == list(range(1, len(evaluations) + 1))
        and len(evaluations) == result["evaluations"],
        "evaluation_order",
    )
    require(
        [r["id"] for r in requests] == list(range(1, len(requests) + 1))
        and len(requests) == result["requests"],
        "request_order",
    )
    require(
        result["attempts"] == sum(len(r["trace"]) - 1 for r in evaluations)
        and result["attempts"] <= plan["attempt_budget"],
        "transition_budget",
    )
    require(
        result["queries"]
        == 1 + sum(s["background"] is not None for r in evaluations for s in r["trace"][1:]),
        "query_count",
    )
    require(
        result["unused_attempt_budget"] == plan["attempt_budget"] - result["attempts"],
        "unused_budget",
    )
    require(result["materialization_queries"] == len(trace), "materialization_queries")
    nodes = {r["id"]: r for r in evaluations}
    seen = {}
    new = []
    hits = 0
    for req in requests:
        require(
            req["caller"] in ("initial", "residual", "returned_point"),
            "request_caller",
        )
        key = struct.pack(">" + "d" * len(req["values"]), *req["values"])
        if req["stopped"] is not None:
            require(
                req["id"] == len(requests)
                and req["evaluation"] is None
                and not req["cached"]
                and req["stopped"] == result["stop"]
                and result["stop"] in ("attempt_budget", "time_budget"),
                "stopped_request",
            )
        elif req["cached"]:
            hits += 1
            require(key in seen and req["evaluation"] == seen[key], "cache_identity")
        else:
            require(key not in seen and req["evaluation"] in nodes, "new_evaluation")
            ev = nodes[req["evaluation"]]
            require(ev["values"] == req["values"], "evaluation_parameters")
            new.append(ev["id"])
            if ev["full"]:
                seen[key] = ev["id"]
    require(
        new == list(range(1, len(evaluations) + 1)) and hits == result["cache_hits"],
        "cache_accounting",
    )
    for ev in evaluations:
        evaluation_check(ev, case, old, trace[0])
    qualified = [ev for ev in evaluations if ev["complete"]]
    eligible = [ev for ev in evaluations if ev["eligible"]]
    if qualified:
        require(
            len(qualified) == 1 and qualified[0]["id"] == len(evaluations), "first_qualified_stop"
        )
        best = qualified[0]
    else:
        best = min(eligible, key=lambda r: (r["objective"], r["id"])) if eligible else None
    require(
        result["selected_evaluation"] == (None if best is None else best["id"]),
        "selected_evaluation",
    )
    require(trace == ([trace[0]] if best is None else best["trace"]), "selected_trace")
    require(
        type(result["complete"]) is bool and result["complete"] == bool(qualified),
        "result_complete",
    )
    optimizer = result["optimizer"]
    require(
        type(optimizer["started"]) is bool and type(optimizer["returned"]) is bool,
        "optimizer_flags",
    )
    if optimizer["returned"]:
        require(
            optimizer["started"]
            and type(optimizer["status"]) is int
            and type(optimizer["success"]) is bool
            and optimizer["success"] == (optimizer["status"] > 0),
            "optimizer_return",
        )
    else:
        require(
            all(
                optimizer[k] is None
                for k in (
                    "status",
                    "success",
                    "message",
                    "iterations",
                    "function_evaluations",
                    "gradient_evaluations",
                )
            ),
            "unobserved_optimizer_status",
        )
    stop = result["stop"]
    horizon = case["task"]["terminal_frame"]
    if stop == "qualified_candidate":
        require(bool(qualified), "false_qualification")
    elif stop == "attempt_budget":
        require(
            not qualified
            and result["unused_attempt_budget"] < horizon
            and requests[-1]["stopped"] == stop,
            "attempt_stopping",
        )
    elif stop == "time_budget":
        require(
            not qualified and result["elapsed_seconds"] >= plan["per_run_seconds"], "time_stopping"
        )
    elif stop == "optimizer_return":
        require(
            not qualified and optimizer["returned"] and requests[-1]["caller"] == "returned_point",
            "optimizer_stopping",
        )
    else:
        require(
            stop == "no_free_controls"
            and not variables(case["task"])
            and not optimizer["started"]
            and not qualified,
            "stopping_reason",
        )


def check(root, commit):
    started = time.monotonic()
    plan = json.loads(read(root, BASE / "PLAN.json"))
    raw = root / BASE / "proof/search_raw"
    execution = committed(root, raw, commit, plan)
    require(
        json.loads(read(raw, "runtime.json")) == json.loads(read(root, BASE / "RUNTIME.json")),
        "runtime_record",
    )
    cases = json.loads(read(root, "experiments/iter168_control_connector/CASES.json"))
    old = json.loads(read(root, OLD))
    require(
        [c["id"] for c in cases] == plan["cases"] and len(execution["records"]) == len(cases),
        "case_population",
    )
    prior = json.loads(read(root, "experiments/iter168_control_connector/proof/admission.json"))
    require(
        prior["source_commit"] == plan["comparator_source_commit"]
        and prior["raw_commit"] == plan["comparator_raw_commit"],
        "comparator_identity",
    )
    baseline = [r for r in prior["records"] if r["depth"] == 2]
    require([r["case"] for r in baseline] == plan["cases"], "comparator_population")
    records = []
    states = points = 0
    for i, case in enumerate(cases):
        require(time.monotonic() - started < plan["search_checker_seconds"], "checker_deadline")
        witness = raw / (case["id"] + "_witness")
        wt = json.loads(read(witness, "trace.json"))
        require([r["action"] for r in wt[1:]] == case["witness_actions"], "witness_actions")
        counts = verify_trace(wt, case, old, lambda f: read(witness, f"mask_{f:03d}.bin"), True)
        states += counts["verified_states"]
        points += counts["verified_states"] * len(case["points"])
        folder = raw / case["id"]
        result = json.loads(read(folder, "result.json"))
        require(result == execution["records"][i] and result["case"] == case["id"], "case_result")
        require(0 < result["elapsed_seconds"] <= plan["per_run_seconds"] + 2, "run_time")
        require(0 < result["peak_rss_bytes"] <= plan["max_rss_bytes"], "run_memory")
        ev = [json.loads(line) for line in read(folder, "evaluations.jsonl").splitlines()]
        req = [json.loads(line) for line in read(folder, "requests.jsonl").splitlines()]
        trace = json.loads(read(folder / "selected", "trace.json"))
        accounting(ev, req, trace, result, case, old, plan)
        metrics = verify_trace(
            trace,
            case,
            old,
            lambda f: read(folder / "selected", f"mask_{f:03d}.bin"),
            result["complete"],
        )
        states += metrics["verified_states"]
        points += metrics["verified_states"] * len(case["points"])
        comparator = (
            root
            / "experiments/iter168_control_connector/proof/search_raw"
            / (case["id"] + "_depth2")
            / "selected"
        )
        ct = json.loads(read(comparator, "trace.json"))
        cm = verify_trace(
            ct, case, old, lambda f: read(comparator, f"mask_{f:03d}.bin"), baseline[i]["complete"]
        )
        states += cm["verified_states"]
        points += cm["verified_states"] * len(case["points"])
        records.append(
            dict(
                **result,
                **metrics,
                final_state=trace[-1]["state"],
                baseline_complete=baseline[i]["complete"],
                baseline_attempts=baseline[i]["attempts"],
            )
        )
    passes = sum(r["complete"] for r in records)
    require(
        time.monotonic() - started <= plan["search_checker_seconds"]
        and rss() <= plan["max_rss_bytes"],
        "checker_resources",
    )
    return dict(
        iteration=169,
        phase="closed",
        status="supported" if passes == len(cases) else "contradicted",
        claim="The full-horizon shooting controller completes all twelve unchanged constructed temporal tasks within the frozen envelope.",
        source_commit=execution["source_commit"],
        raw_commit=commit,
        total_cases=len(cases),
        complete_cases=passes,
        baseline_complete_cases=sum(r["complete"] for r in baseline),
        total_attempts=sum(r["attempts"] for r in records),
        baseline_attempts=sum(r["attempts"] for r in baseline),
        total_evaluations=sum(r["evaluations"] for r in records),
        cache_hits=sum(r["cache_hits"] for r in records),
        verified_states=states,
        point_state_classifications=points,
        qualified_for_local_tasks=passes == len(cases),
        qualified_for_source_comparison=False,
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
