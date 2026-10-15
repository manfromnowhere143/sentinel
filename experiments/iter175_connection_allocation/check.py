"""Scalar integration replay plus independent forward proposal reconstruction.

Reuses Iter172's trajectory/sequence admission and Iter173's separate parameter
checker. No producer generator, adapter, native bridge or vector geometry import.
Full scalar masks cover returned paths; native tree/RNG and unselected background
masks remain producer evidence.
"""

import argparse
import json
from pathlib import Path
import time

from experiments.iter172_integrated_rrt.check import (
    connection_check as previous_connection_check, path_tokens,
)
from experiments.iter173_matched_connector_cost.check import proposal_check
from experiments.iter164_monitor_time_continuation.path_check import verify_path
from experiments.iter162_source_grouping_qualification.check import completion_check
from .common import BASE, read, require, rss, write
from .records import committed
from .contract import check_contract, reference
from .comparison import compare, coverage


def connection_check(c, events, case, old, plan, remaining):
    counts = previous_connection_check(c, events, case, old, plan, remaining)
    if c["result"] is not None:
        result = c["result"]
        require(result["optimizer"]["started"] is False
                and result["optimizer"]["returned"] is False, "forward_optimizer")
        proposal_check(events, c["before"][:5], c["task"], plan["max_proposals"], result)
    return counts


def tree_summary(connections, reset):
    accepted = [c for c in connections.values() if c["result"] is not None and len(c["trace"]) > 1]
    # Every accepted trace has already passed scalar physical/accounting checks.
    return dict(max_tree_frame=max([0] + [c["trace"][-1]["frame"] for c in accepted]),
                checkpoint_crossings=sum(r["frame"] in (16, 32)
                                         for c in accepted for r in c["trace"][1:]),
                root_connections=sum(c["before"] == [*reset, 0] for c in accepted))


def check(root, commit):
    started = time.monotonic()
    plan = json.loads(read(root, BASE / "PLAN.json"))
    check_contract(root, plan)
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
        proposal_coverage = []
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
            proposal_coverage.append(dict(call=row["call"], **coverage(pending)))
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
        records.append(dict(**result, **metrics, final_progress=trace[-1]["route"]["rc"],
                            returned_frame=trace[-1]["frame"],
                            proposal_coverage=proposal_coverage,
                            **tree_summary(connections, case["geometry"]["reset"])))
    passes = sum(r["complete"] for r in records)
    require(
        rss() <= plan["max_rss_bytes"]
        and time.monotonic() - started <= plan["search_checker_seconds"],
        "checker_resources",
    )
    return dict(
        iteration=175,
        phase="closed",
        status="supported" if passes == 4 else "contradicted",
        claim="The integrated released control-RRT with a 128-transition forward-connection allowance completes all four original cases under unchanged outer constraints and budgets.",
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
        comparison=compare(records, reference(root)),
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
