"""Independent scalar physics, temporal tasks, masks and connector accounting.

Does not import the control generator, connector, vector geometry or fixture builder.
All attempts receive scalar motion/physical/task checks; full scalar background masks
are reconstructed for witnesses and selected paths, not unselected alternatives.
"""

import argparse
import json
import math
from pathlib import Path
import time

import numpy as np

from experiments.iter153_action_feasibility.check import gap, motion, near, swept
from experiments.iter155_background_witness.geometry import count_points, ground_height, vertices
from .common import BASE, OLD, read, require, rss, sha, write
from .records import committed


def physical(before, state, action, frame, case, old):
    require(
        len(state) == 5 and all(type(v) in (int, float) and math.isfinite(v) for v in state),
        "state_domain",
    )
    if action is not None:
        require(
            len(action) == 2 and all(type(v) in (int, float) and math.isfinite(v) for v in action),
            "action_domain",
        )
        near(state, motion(before, action))
    x, y, h, v, d = state
    yaw = v * math.tan(d) / 2.7
    if action is not None and not (
        abs(action[0]) <= 2 + 1e-12
        and abs(action[1]) <= math.pi / 12 + 1e-12
        and abs(d) <= math.pi / 3 + 1e-12
        and -1e-12 <= v <= 6 + 1e-12
        and abs(yaw) <= 0.95 + 1e-12
        and abs(v * yaw) <= 4.89 + 1e-12
    ):
        return "controls"
    g, task = case["geometry"], case["task"]
    objects = [[o[0], -o[1], o[3], o[4], -o[6]] for o in g["obstacles"]]
    if not all(gap([x, y, *g["ego_dimensions"][:2], h], obj) > 0 for obj in objects):
        return "foreground"
    if not swept(before, state, g["ego_dimensions"], objects, old):
        return "foreground_sweep"
    distances = [math.hypot(p[0] - y, p[1] - x) for p in g["route"]]
    nearest = min(range(len(distances)), key=lambda i: (distances[i], i))
    rc = (nearest + 1) / (0.9 * len(distances))
    if distances[nearest] > 10:
        return "route_distance"
    for checkpoint in g["comparators"].values():
        if frame / 4 == checkpoint["hazard_time"] and rc < checkpoint["rc"] - 0.05:
            return "progress"
    if frame <= task["wait_until"] and any(abs(state[k] - g["reset"][k]) > 1e-10 for k in range(5)):
        return "wait_contract"
    if task["stop_from"] is not None and frame >= task["stop_from"] and abs(v) > 1e-10:
        return "stop_contract"
    return None


def completed(state, frame, task):
    errors = [abs(state[k] - task["target"][k]) for k in range(5)]
    errors[2] = abs(math.remainder(state[2] - task["target"][2], 2 * math.pi))
    return frame == task["terminal_frame"] and all(
        errors[k] <= task["tolerance"][k] for k in range(5)
    )


def verify_trace(trace, case, old, mask, claimed_complete):
    task, geometry = case["task"], case["geometry"]
    require(0 < len(trace) <= task["terminal_frame"] + 1, "trace_length")
    near(trace[0]["state"], geometry["reset"], 0)
    require(
        trace[0]["id"] == 0 and trace[0]["parent"] is None and trace[0]["action"] is None,
        "reset_identity",
    )
    checkpoints = 0
    for frame, row in enumerate(trace):
        require(type(row["frame"]) is int and row["frame"] == frame, "frame_sequence")
        previous = trace[frame - 1] if frame else row
        if frame:
            require(row["parent"] == previous["id"], "parent_chain")
        require(
            physical(previous["state"], row["state"], row["action"], frame, case, old) is None,
            "path_rejected",
        )
        state = row["state"]
        distances = [math.hypot(p[0] - state[1], p[1] - state[0]) for p in geometry["route"]]
        nearest = min(range(len(distances)), key=lambda i: (distances[i], i))
        require(row["route"]["nearest"] == nearest, "route_index")
        near(
            [row["route"]["distance"], row["route"]["rc"]],
            [distances[nearest], (nearest + 1) / (0.9 * len(distances))],
        )
        checkpoints += sum(frame / 4 == c["hazard_time"] for c in geometry["comparators"].values())
        height, _ = ground_height(case["ground"], state[1], state[0])
        actual = count_points(case["points"], vertices([state[1], height, state[0]], state[2]))
        packed = np.packbits(np.asarray(actual["mask"], dtype=bool), bitorder="little").tobytes()
        require(mask(frame) == packed, "scalar_mask")
        require(
            all(
                type(row["background"][k]) is int and row["background"][k] == actual[k]
                for k in ("count", "certain_inside", "possible_inside")
            ),
            "scalar_counts",
        )
        require(row["background"]["mask_sha256"] == sha(packed), "mask_identity")
        require(
            actual["possible_inside"] <= 100
            and row["background"]["decision"] == "clear"
            and row["reason"] == "clear",
            "background_rejected",
        )
    require(
        type(claimed_complete) is bool
        and claimed_complete == completed(trace[-1]["state"], trace[-1]["frame"], task),
        "false_completion",
    )
    if claimed_complete:
        require(checkpoints == len(geometry["comparators"]), "missing_checkpoint")
    return dict(verified_states=len(trace), progress_checks=checkpoints)


def metric(row, task):
    delta = [
        a - b
        for a, b in zip([*row["state"], row["frame"]], [*task["target"], task["terminal_frame"]])
    ]
    delta[2] = math.remainder(delta[2], 2 * math.pi)
    return math.sqrt(sum((v * w) ** 2 for v, w in zip(delta, (1, 1, 2, 0.5, 2, 0.01))))


def accounting(attempts, calls, trace, result, case, old, plan):
    require(len(attempts) == result["attempts"] <= plan["attempt_budget"], "attempt_budget")
    require([r["id"] for r in attempts] == list(range(1, len(attempts) + 1)), "attempt_order")
    require(
        len(calls) == result["calls"]
        and [r["call"] for r in calls] == list(range(1, len(calls) + 1)),
        "call_order",
    )
    require(
        result["queries"] == 1 + sum(r["background"] is not None for r in attempts), "query_count"
    )
    require(result["materialization_queries"] == len(trace), "materialization_count")
    nodes = {0: trace[0]}
    for row in attempts:
        require(row["parent"] in nodes, "attempt_parent")
        parent = nodes[row["parent"]]
        require(parent["reason"] == "clear", "rejected_parent")
        require(
            row["before"] == parent["state"] and row["frame"] == parent["frame"] + 1,
            "attempt_clock",
        )
        require(1 <= row["call"] <= len(calls), "attempt_call")
        call = calls[row["call"] - 1]
        require(parent["id"] == call["root"] or parent.get("call") == row["call"], "foreign_parent")
        reason = physical(parent["state"], row["state"], row["action"], row["frame"], case, old)
        if reason is not None:
            require(row["reason"] == reason and row["background"] is None, "attempt_physics")
        else:
            require(
                row["background"] is not None and row["reason"] == row["background"]["decision"],
                "attempt_background",
            )
        nodes[row["id"]] = row
    selected = [0]
    for call in calls:
        require(call["root"] == selected[-1], "call_root")
        level = min(result["depth"], case["task"]["terminal_frame"] - nodes[call["root"]]["frame"])
        require(call["depth"] == level, "lookahead_depth")
        candidates = [
            r
            for r in attempts
            if r["call"] == call["call"]
            and r["reason"] == "clear"
            and r["frame"] == nodes[call["root"]]["frame"] + level
        ]
        if call["interrupted"]:
            require(
                call["call"] == len(calls) and call["selected"] is None and call["leaf"] is None,
                "partial_expansion_used",
            )
            require(call["interrupted"] in ("attempt_budget", "time_budget"), "interrupt_reason")
        elif candidates:
            best = min(candidates, key=lambda r: (metric(r, case["task"]), r["id"]))
            require(call["leaf"] == best["id"], "selection_rank")
            while best["parent"] != call["root"]:
                best = nodes[best["parent"]]
            require(call["selected"] == best["id"], "selected_first_edge")
            selected.append(best["id"])
        else:
            require(
                call["selected"] is None and call["leaf"] is None and call["call"] == len(calls),
                "empty_expansion",
            )
    require(
        [r["id"] for r in trace] == selected and all(r == nodes[r["id"]] for r in trace),
        "selected_trace_binding",
    )
    if result["stop"] == "attempt_budget":
        require(
            len(attempts) == plan["attempt_budget"]
            and calls[-1]["interrupted"] == "attempt_budget",
            "budget_stopping",
        )
    elif result["stop"] == "time_budget":
        require(
            result["elapsed_seconds"] >= plan["per_run_seconds"]
            and calls[-1]["interrupted"] == "time_budget",
            "time_stopping",
        )
    elif result["stop"] == "no_valid_rollout":
        require(calls[-1]["selected"] is None and calls[-1]["interrupted"] is None, "empty_stop")
    else:
        require(
            result["stop"] == "terminal_frame"
            and trace[-1]["frame"] == case["task"]["terminal_frame"],
            "terminal_stopping",
        )


def coverage_check(rows, plan):
    require([r["speed"] for r in rows] == plan["coverage_speeds"], "coverage_population")
    missing = 0
    for row in rows:
        v = row["speed"]
        expected = {(a, r * math.pi / 12) for a in (-2.0, 0.0, 2.0) for r in (-1, -0.5, 0, 0.5, 1)}
        expected.update((max(-2.0, min(2.0, (target - v) * 4)), 0.0) for target in (2.0, 4.0, 6.0))
        require({tuple(a) for a in row["legacy"]} == expected, "legacy_population")
        successor = {tuple(r["action"]) for r in row["successor"]}
        braking = {(-min(2.0, v * 4), r * math.pi / 12) for r in (-1, -0.5, 0, 0.5, 1)}
        require(
            successor == expected | braking and len(successor) == len(row["successor"]),
            "successor_population",
        )
        for r in row["successor"]:
            near(r["state"], motion([0.0, 0.0, 0.0, v, 0.0], r["action"]))
        if v <= 0.5 and (-v * 4, 0.0) not in expected:
            missing += 1
        for a in braking:
            state = motion([0.0, 0.0, 0.0, v, 0.0], a)
            near(state[3], max(0.0, v - 0.5), 0)
            require(abs(a[0]) <= 2 and abs(a[1]) <= math.pi / 12, "braking_bound")
    return missing


def check(root, raw_commit):
    started = time.monotonic()
    plan = json.loads(read(root, BASE / "PLAN.json"))
    raw = root / BASE / "proof/search_raw"
    execution = committed(root, raw, raw_commit, plan)
    old = json.loads(read(root, OLD))
    cases = json.loads(read(root, BASE / "CASES.json"))
    require([c["id"] for c in cases] == plan["cases"], "case_population")
    missing = coverage_check(json.loads(read(raw, "coverage.json")), plan)
    require(len(execution["records"]) == len(cases) * len(plan["lookaheads"]), "result_population")
    records, states, classifications = [], 0, 0
    for i, case in enumerate(cases):
        witness = raw / (case["id"] + "_witness")
        trace = json.loads(read(witness, "trace.json"))
        require([r["action"] for r in trace[1:]] == case["witness_actions"], "witness_binding")
        metrics = verify_trace(trace, case, old, lambda f: read(witness, f"mask_{f:03d}.bin"), True)
        states += metrics["verified_states"]
        classifications += metrics["verified_states"] * len(case["points"])
        for j, depth in enumerate(plan["lookaheads"]):
            require(time.monotonic() - started < plan["search_checker_seconds"], "checker_deadline")
            folder = raw / (case["id"] + "_depth" + str(depth))
            result = json.loads(read(folder, "result.json"))
            require(
                result == execution["records"][i * len(plan["lookaheads"]) + j]
                and result["case"] == case["id"]
                and result["depth"] == depth,
                "case_binding",
            )
            require(0 < result["elapsed_seconds"] <= plan["per_run_seconds"] + 2, "run_time")
            require(0 < result["peak_rss_bytes"] <= plan["max_rss_bytes"], "worker_memory")
            attempts = [json.loads(line) for line in read(folder, "attempts.jsonl").splitlines()]
            calls = [json.loads(line) for line in read(folder, "calls.jsonl").splitlines()]
            trace = json.loads(read(folder / "selected", "trace.json"))
            accounting(attempts, calls, trace, result, case, old, plan)
            metrics = verify_trace(
                trace,
                case,
                old,
                lambda f: read(folder / "selected", f"mask_{f:03d}.bin"),
                result["complete"],
            )
            states += metrics["verified_states"]
            classifications += metrics["verified_states"] * len(case["points"])
            records.append(dict(**result, **metrics, final_state=trace[-1]["state"]))
    successes = {
        str(d): sum(r["complete"] for r in records if r["depth"] == d) for d in plan["lookaheads"]
    }
    require(
        rss() <= plan["max_rss_bytes"]
        and time.monotonic() - started < plan["search_checker_seconds"],
        "checker_resources",
    )
    return dict(
        iteration=168,
        phase="closed",
        status="supported" if successes["2"] == len(cases) else "contradicted",
        claim="The two-step connector completes all twelve disclosed stopping, waiting and turning tasks within the frozen envelope.",
        source_commit=execution["source_commit"],
        raw_commit=raw_commit,
        total_cases=len(cases),
        coverage_speeds=len(plan["coverage_speeds"]),
        legacy_missing_stops=missing,
        witness_passes=len(cases),
        one_step_passes=successes["1"],
        two_step_passes=successes["2"],
        total_attempts=sum(r["attempts"] for r in records),
        verified_states=states,
        point_state_classifications=classifications,
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
    args = p.parse_args()
    result = check(args.root.resolve(), args.raw_commit)
    write(args.root.resolve() / BASE / "proof/admission.json", result)
    print(json.dumps({k: v for k, v in result.items() if k != "records"}), flush=True)
