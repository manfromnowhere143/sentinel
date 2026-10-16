"""Immutable population and conservative original-work accounting."""

import copy

from .common import document, read, git, require, sha

PARENT = "59ab3974b061422434443e4ba45a788b968868e1"
RAW = "172cf0f5449e4171c3f9a25bc45d6e6cb7f03bd5"
PREVIOUS = "experiments/iter183_timing_eligibility/"
CASES = "experiments/iter161_grouping_width_ablation/CASES.json"
OLD = "experiments/iter153_action_feasibility/PLAN.json"
ROOTS = [(83, 8, 7), (98, 8, 6), (110, 2, 1)]


def identity(row):
    return row["call"], row["evaluation"], row["prefix"]


def population(connections, trials):
    accepted = [c for c in connections if c["result"] is not None and len(c["trace"]) > 1]
    highest = max(c["trace"][-1]["route"]["nearest"] for c in accepted)
    table = {c["call"]: c for c in connections}
    records = []
    for trial in trials:
        for k in range(1, trial["eligibility"]["eligible_prefix"] + 1):
            row = trial["trace"][k]
            if row["route"]["nearest"] > highest:
                selected = table[trial["call"]]["result"]
                require(
                    selected is None
                    or selected["selected_evaluation"] != trial["id"]
                    or k > selected["selected_prefix"],
                    "population_selected_edge",
                )
                records.append(
                    dict(
                        call=trial["call"],
                        evaluation=trial["id"],
                        prefix=k,
                        frame=row["frame"],
                        state=row["state"],
                        route=row["route"],
                    )
                )
    maxima = []
    for call in sorted({r["call"] for r in records}):
        group = [r for r in records if r["call"] == call]
        maxima.append(
            min(
                group,
                key=lambda r: (-r["route"]["nearest"], r["frame"], r["evaluation"], r["prefix"]),
            )
        )
    return highest, records, maxima


def remaining(connections, call, total=18000):
    consumed = sum(
        c["result"]["attempts"]
        for c in connections
        if c["call"] <= call and c["result"] is not None
    )
    require(0 < consumed < total, "remaining_work_domain")
    return total - consumed


def input_names():
    return [
        CASES,
        OLD,
        PREVIOUS + "PLAN.json",
        PREVIOUS + "proof/admission.json",
        PREVIOUS + "proof/frontier_notes.json",
        PREVIOUS + "proof/search_raw/bend_right/events.jsonl",
        PREVIOUS + "proof/search_raw/bend_right/result.json",
    ]


def load(root, plan):
    require(
        plan["parent_commit"] == PARENT and plan["retained_raw_commit"] == RAW, "parent_identity"
    )
    require(set(plan["input_files"]) == set(input_names()), "input_inventory")
    for name in input_names():
        data = read(root, name)
        require(sha(data) == plan["input_files"][name], "input_hash")
        require(data == git(root, "show", PARENT + ":" + name), "input_commit")
        if "/search_raw/" in name:
            require(data == git(root, "show", RAW + ":" + name), "raw_binding")
    admission = document(root, PREVIOUS + "proof/admission.json")
    require(
        admission["raw_commit"] == RAW
        and admission["complete_cases"] == 3
        and admission["qualified_for_source_comparison"] is False,
        "parent_admission",
    )
    from experiments.iter150_cloud_observation.native import parse

    events = [
        parse(line)
        for line in read(root, PREVIOUS + "proof/search_raw/bend_right/events.jsonl").splitlines()
    ]
    connections = [r for r in events if r["kind"] == "connection"]
    trials = [r for r in events if r["kind"] == "evaluation"]
    require([c["call"] for c in connections] == list(range(1, 143)), "connection_inventory")
    high, records, maxima = population(connections, trials)
    require(
        high == 117 and len(records) == 15 and [identity(r) for r in maxima] == ROOTS,
        "population_inventory",
    )
    notes = document(root, PREVIOUS + "proof/frontier_notes.json")
    require(
        [identity(r) for r in records] == [identity(r) for r in notes["records"]],
        "descriptive_population",
    )
    require(
        [remaining(connections, r["call"]) for r in maxima] == plan["remaining_attempts"],
        "remaining_attempts",
    )
    result = document(root, PREVIOUS + "proof/search_raw/bend_right/result.json")
    require(
        result["elapsed_seconds"] == plan["original_wall_seconds"] and result["complete"] is False,
        "original_wall",
    )
    case = next(c for c in document(root, CASES) if c["id"] == "bend_right")
    return case, connections, trials, records, maxima


def conditional_plan(parent, remaining_attempts, original_wall):
    require(
        type(remaining_attempts) is int and 0 < remaining_attempts < parent["attempt_budget"],
        "conditional_attempts",
    )
    require(0 < original_wall < parent["per_run_seconds"], "conditional_wall")
    result = copy.deepcopy(parent)
    result.update(
        attempt_budget=remaining_attempts, per_run_seconds=parent["per_run_seconds"] - original_wall
    )
    return result
