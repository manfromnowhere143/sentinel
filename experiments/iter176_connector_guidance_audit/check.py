"""Independent proposal arithmetic, retained-path binding and full scalar replay.

No producer generator, Controls, path extractor or vector geometry imports.
Nominal program availability is not a mirrored solver outcome.
"""

import argparse
import copy
import json
import math
from pathlib import Path
import struct
import time

from experiments.iter153_action_feasibility.check import near
from experiments.iter164_monitor_time_continuation.path_check import verify_path
from experiments.iter169_full_horizon_control.check import variables
from experiments.iter173_matched_connector_cost.check import expected_proposal
from .common import BASE, document, encode, read, require, rss, write
from .records import committed
from .retained import OLD, case_records, request_identity, verify_inputs


def check_nominal(record, reset, task, budget, limit):
    require(all(type(record[k]) is int and record[k] >= 0
                for k in ("nominal_transitions", "unique_evaluations", "cache_hits")), "count_type")
    rows = record["requests"]
    require(1 <= len(rows) <= limit, "request_limit")
    seen, evaluations, hits, programs = {}, 0, 0, []
    horizon = task["terminal_frame"]
    for index, row in enumerate(rows):
        require(set(row) == {"index", "values", "cached", "evaluation", "stop"}
                and type(row["index"]) is int and row["index"] == index
                and type(row["cached"]) is bool
                and (row["evaluation"] is None or type(row["evaluation"]) is int), "request_schema")
        expected = expected_proposal(reset, task, index)
        near(row["values"], expected, 2e-15)
        require(all(a != 0 or b != 0 or math.copysign(1, a) == math.copysign(1, b)
                    for a, b in zip(row["values"], expected)), "zero_sign")
        key = struct.pack(">" + "d" * len(row["values"]), *row["values"])
        if key in seen:
            require(row["cached"] is True and row["evaluation"] == seen[key]
                    and row["stop"] is None, "cache_entry")
            hits += 1
        elif (evaluations+1)*horizon > budget:
            require(index == len(rows)-1 and row["stop"] == "budget"
                    and row["evaluation"] is None and not row["cached"], "budget_stop")
        else:
            evaluations += 1
            require(row["evaluation"] == evaluations and not row["cached"]
                    and row["stop"] is None, "evaluation_entry")
            seen[key] = evaluations
            programs.append(tuple(row["values"]))
    require(rows[-1]["stop"] == "budget", "missing_budget_stop")
    require(record["nominal_transitions"] == evaluations*horizon <= budget
            and record["unique_evaluations"] == evaluations and record["cache_hits"] == hits,
            "nominal_accounting")
    return set(programs), evaluations-len(set(programs))


def coverage(original, mirrored, keys):
    transformed = {tuple(-value if keys[i][1] == 1 else value for i, value in enumerate(vector))
                   for vector in original}
    missing, extra = transformed-mirrored, mirrored-transformed
    return dict(reflection_closed=not missing and not extra,
                original_programs=len(original), mirrored_programs=len(mirrored),
                missing_reflected=len(missing), extra_mirrored=len(extra))


def check_binding(trace, record, connections, trial, reset):
    table = {row["call"]: row for row in connections}
    edge = table[record["call"]]
    target, cutoff, ambiguous = edge["before"], record["call"], 0
    for chosen in reversed(record["ancestor_calls"]):
        options = [number for number, row in table.items()
                   if number < cutoff and row["result"] is not None and len(row["trace"]) > 1
                   and [*row["trace"][-1]["state"], row["trace"][-1]["frame"]] == target]
        require(bool(options) and chosen == min(options), "ancestor_selection")
        ambiguous += len(options) > 1
        require(table[chosen]["before"][5] < target[5], "ancestor_clock")
        target, cutoff = table[chosen]["before"], chosen
    require(target == [*reset, 0] and record["ambiguous_joins"] == ambiguous, "ancestor_root")
    expected = []
    for number in record["ancestor_calls"]:
        edge_trace = table[number]["trace"]
        if not expected:
            expected.append(edge_trace[0])
        require([*expected[-1]["state"], expected[-1]["frame"]] == table[number]["before"],
                "ancestor_join")
        expected.extend(edge_trace[1:])
    if not expected:
        expected.append(trial["trace"][0])
    require([*expected[-1]["state"], expected[-1]["frame"]] == edge["before"]
            == [*trial["trace"][0]["state"], trial["trace"][0]["frame"]], "prefix_join")
    require(trial["interrupted"] is None and trial["valid_prefix"] > trial["selected_prefix"],
            "discarded_prefix")
    expected.extend(trial["trace"][1:trial["valid_prefix"]+1])
    require(encode(trace) == encode(expected), "path_source")


def check(root, commit):
    started = time.monotonic()
    plan = document(root, BASE / "PLAN.json")
    raw = root / BASE / "proof/audit_raw"
    execution = committed(root, raw, commit, plan)
    require(execution["new_motion_searches"] == execution["new_integrated_schedules"] == 0,
            "audit_scope")
    cases = verify_inputs(root, plan)
    old = json.loads(read(root, OLD))
    submitted = document(raw, "proposals.json")
    paths = document(raw, "paths.json")
    require([(p["case"], p["call"], p["evaluation"], p["folder"]) for p in paths]
            == [(plan["selected_case"], plan["selected_call"], n, f"path_{n:03}")
                for n in plan["selected_evaluations"]], "path_population")
    require(len(submitted["requests"]) == execution["request_count"] == plan["executed_count"]
            and len(paths) == execution["path_count"] == 4, "submitted_population")
    records, verified, excluded = [], [], []
    deadline = started + plan["audit_checker_seconds"]
    for case in cases:
        connections, trials = case_records(root, case["id"], plan)
        for row in connections:
            require(time.monotonic() < deadline, "checker_deadline")
            if row["result"] is None:
                excluded.append(dict(case=case["id"], call=row["call"], reason=row["stop"]))
                continue
            actual = submitted["requests"][len(records)]
            require({k: actual[k] for k in request_identity(case["id"], row)}
                    == request_identity(case["id"], row), "request_identity")
            state = [v if i in (0, 3) else -v for i, v in enumerate(row["before"][:5])]
            task = copy.deepcopy(row["task"])
            task["target"] = [v if i in (0, 3) else -v for i, v in enumerate(task["target"])]
            a, duplicate_a = check_nominal(actual["original"], row["before"][:5], row["task"],
                                           row["budget"], plan["max_proposals"])
            b, duplicate_b = check_nominal(actual["mirrored"], state, task, row["budget"],
                                           plan["max_proposals"])
            records.append(dict(case=case["id"], call=row["call"],
                                horizon=row["task"]["terminal_frame"], budget=row["budget"],
                                original_physical_duplicates=duplicate_a,
                                mirrored_physical_duplicates=duplicate_b,
                                **coverage(a, b, variables(row["task"]))))
        if case["id"] == plan["selected_case"]:
            require(sorted(trials) == plan["selected_evaluations"], "selected_population")
            for path in paths:
                folder = raw / path["folder"]
                trace = document(folder, "trace.json")
                check_binding(trace, path, connections, trials[path["evaluation"]],
                              case["geometry"]["reset"])
                metrics = verify_path(trace, case["geometry"], old, case["points"], case["ground"],
                                      lambda f: read(folder, f"mask_{f:03}.bin", 40000), False, deadline)
                require(trace[-1]["frame"] == 32 and metrics["progress_checks"] == 2,
                        "path_checkpoint_scope")
                verified.append(dict(**path, **metrics, complete=False, final_frame=32,
                                     final_progress=trace[-1]["route"]["rc"],
                                     point_state_classifications=len(trace)*len(case["points"])))
    require(excluded == submitted["excluded"] and len(excluded) == plan["excluded_count"]
            and len(records)+len(excluded) == plan["connection_count"], "excluded_population")
    require(rss() <= plan["max_rss_bytes"] and time.monotonic() < deadline, "checker_resources")
    closed = sum(row["reflection_closed"] for row in records)
    return dict(
        iteration=176, phase="closed", analysis_status="exploratory",
        status="supported" if closed == len(records) else "contradicted",
        claim="Nominal full-rollout proposal availability is reflection-closed for every retained executed Iter175 connection request.",
        source_commit=execution["source_commit"], raw_commit=commit,
        request_count=len(records), reflection_closed_requests=closed,
        reflection_open_requests=len(records)-closed, excluded_requests=len(excluded),
        partial_paths_verified=len(verified), verified_states=sum(p["verified_states"] for p in verified),
        point_state_classifications=sum(p["point_state_classifications"] for p in verified),
        retained_complete_cases=2, retained_total_cases=4, qualified_for_source_comparison=False,
        records=records, paths=verified, elapsed_seconds=time.monotonic()-started,
        peak_rss_bytes=rss(), new_motion_searches=0, new_integrated_schedules=0,
        new_driving_episodes=0, provider_spend=0, source_recovery=None, superiority=None, transfer=None,
        boundary="Exposed diagnostic inputs, nominal full rollouts and exact numeric program sets with signed zero identified. Not a mirrored solver execution, causal directional-bias finding or repaired planner qualification. Four partial paths are not completions.",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--raw-commit", required=True)
    args = parser.parse_args()
    result = check(args.root.resolve(), args.raw_commit)
    write(args.root.resolve() / BASE / "proof/admission.json", result)
    print(json.dumps({k: v for k, v in result.items() if k not in ("records", "paths")}), flush=True)
