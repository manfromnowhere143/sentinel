"""Separate proposal, scalar mask, physics, ancestry and comparison admission."""

import argparse
import json
from pathlib import Path
import time
from experiments.iter182_late_frontier_timing.retained import state_key
from experiments.iter183_timing_eligibility.comparison import compare
from experiments.iter164_monitor_time_continuation.path_check import verify_path
from experiments.iter162_source_grouping_qualification.check import completion_check
from experiments.iter190_late_continuation_audit.masks import verify as scalar_masks
from experiments.iter191_stop_wait_release.callback_check import query_rows
from experiments.iter191_stop_wait_release.wiring import wiring
from experiments.iter191_stop_wait_release.runtime import verify
from .common import BASE, CASES, OLD, PREVIOUS, read, require, rss, write
from .contract import check_contract
from .records import committed


def population(plan, records):
    require(len(records) == len(plan["cases"]) == len(plan["seeds"]) == 4, "execution_population")
    require(
        [(r["case"], r["seed"]) for r in records] == list(zip(plan["cases"], plan["seeds"])),
        "case_identity",
    )


def classify(records, comparisons):
    require(all(type(r["complete"]) is bool for r in records), "completion_type")
    if any(r["stop"] == "time_budget" for r in records):
        return "inconclusive"
    return (
        "supported"
        if all(r["complete"] for r in records)
        and all(c["lost_cases"] == 0 for c in comparisons.values())
        else "contradicted"
    )


def case_check(folder, case, old, planner, result, deadline):
    require(json.loads(read(folder, "result.json")) == result, "result_binding")
    trace = json.loads(read(folder, "trace.json"))
    sequences = json.loads(read(folder, "sequences.json"))
    events = [json.loads(line) for line in read(folder, "events.jsonl").splitlines()]
    details = wiring(events, sequences, result, trace, case, old, planner, deadline, True)
    masks = scalar_masks(folder, case, deadline)
    used = query_rows(trace, masks)
    for event in events:
        if (
            event["kind"] == "evaluation"
            or event["kind"] == "connection"
            and event["result"] is not None
        ):
            used |= query_rows(event["trace"], masks)
    for sequence in sequences.values():
        used |= query_rows(sequence["trace"], masks)
    require(
        used == set(masks) and len(masks) == result["distinct_queried_states"],
        "all_query_inventory",
    )
    require(result["queries"] == result["recorded_queries"], "query_accounting")
    metrics = verify_path(
        trace,
        case["geometry"],
        old,
        case["points"],
        case["ground"],
        lambda i: read(folder / "masks", state_key(trace[i]["state"]) + ".bin", 40000),
        result["complete"],
        deadline,
    )
    completion_check(metrics, result["complete"], len(case["geometry"]["comparators"]))
    require(
        0 < result["elapsed_seconds"] <= result["collection_seconds"] <= result["worker_seconds"]
        and 0
        < result["peak_rss_bytes"]
        <= result["collection_peak_rss_bytes"]
        <= result["worker_peak_rss_bytes"],
        "worker_accounting",
    )
    return dict(
        **result,
        **details,
        **metrics,
        returned_frame=trace[-1]["frame"],
        final_progress=trace[-1]["route"]["rc"],
        feedback_requests=sum(
            e["kind"] == "request" and e["caller"] == "stop_wait_release" for e in events
        ),
        scalar_classifications=len(masks) * len(case["points"]),
    )


def comparisons_for(root, records):
    comparisons = {}
    for iteration, name in [
        (189, "iter189_uniform_timing_eligibility"),
        (183, "iter183_timing_eligibility"),
    ]:
        baseline = json.loads(read(root, f"experiments/{name}/proof/admission.json"))
        comparison = compare(records, baseline, iteration)
        for pair, new, old in zip(comparison["pairs"], records, baseline["records"]):
            for key in (
                "queries",
                "registered_primary",
                "registered_extra",
                "elapsed_seconds",
                "peak_rss_bytes",
                "final_progress",
            ):
                pair[key] = new.get(key)
                pair["reference_" + key] = old.get(key)
        comparison["boundary"] = (
            "Retained controls; four exposed development cases. Candidate all-query recording is charged; reference materialization differed. No population or wall-time speedup claim."
        )
        comparisons[str(iteration)] = comparison
    return comparisons


def check(root, commit):
    started = time.monotonic()
    verify(root)
    plan = json.loads(read(root, BASE / "PLAN.json"))
    check_contract(root, plan)
    raw = root / BASE / "proof/search_raw"
    execution = committed(root, raw, commit, plan)
    require(
        execution["children_reaped"] is True and execution["new_integrated_runs"] == 4,
        "execution_scope",
    )
    population(plan, execution["records"])
    old = json.loads(read(root, OLD))
    planner = json.loads(read(root, PREVIOUS / "PLAN.json"))
    cases = {c["id"]: c for c in json.loads(read(root, CASES))}
    records = []
    for result in execution["records"]:
        require(
            result["worker_seconds"] <= plan["worker_supervisor_seconds"]
            and result["worker_peak_rss_bytes"] <= plan["max_rss_bytes"],
            "worker_resources",
        )
        records.append(
            case_check(
                raw / result["case"],
                cases[result["case"]],
                old,
                planner,
                result,
                started + plan["search_checker_seconds"],
            )
        )
        print(
            json.dumps(dict(checked_case=result["case"], complete=result["complete"])), flush=True
        )
    comparisons = comparisons_for(root, records)
    require(
        rss() <= plan["max_rss_bytes"]
        and time.monotonic() - started <= plan["search_checker_seconds"],
        "checker_resources",
    )
    return dict(
        iteration=192,
        phase="closed",
        status=classify(records, comparisons),
        source_commit=execution["source_commit"],
        raw_commit=commit,
        complete_cases=sum(r["complete"] for r in records),
        total_cases=4,
        comparisons=comparisons,
        records=records,
        total_attempts=sum(r["attempts"] for r in records),
        total_queries=sum(r["queries"] for r in records),
        scalar_classifications=sum(r["scalar_classifications"] for r in records),
        elapsed_seconds=time.monotonic() - started,
        peak_rss_bytes=rss(),
        actual_history_intervention=None,
        response_delay=None,
        superiority=None,
        new_driving_episodes=0,
        provider_spend=0,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--raw-commit", required=True)
    a = p.parse_args()
    value = check(Path.cwd(), a.raw_commit)
    write(Path.cwd() / BASE / "proof/admission.json", value)
    print(json.dumps({k: v for k, v in value.items() if k not in ("records", "comparisons")}))
