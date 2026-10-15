"""Case-scoped immutable inputs and complete late accepted endpoint population."""

import json
import struct

from .common import read, require, sha, git

REFERENCE = "be4de1c115f781617ae40648118a267787ed28a6"
RAW = "36383c3dd420ab7a8d7efad4c4808c3bae37c09b"
PREVIOUS = "experiments/iter181_checkpoint_prefix_selection/"
CASES = "experiments/iter161_grouping_width_ablation/CASES.json"
OLD = "experiments/iter153_action_feasibility/PLAN.json"
CALLS = {"bend_left": [91, 104, 110, 128, 134], "bend_right": [102, 138]}
CONNECTIONS = {"bend_left": 141, "bend_right": 142}
EVALUATIONS = {"bend_left": 454, "bend_right": 128}
REQUESTS = {"bend_left": 13, "bend_right": 1}


def state_key(state):
    return sha(struct.pack(">5d", *state))


def input_names():
    return [CASES, OLD, PREVIOUS + "PLAN.json", PREVIOUS + "proof/admission.json"] + [
        PREVIOUS + f"proof/search_raw/{case}/events.jsonl" for case in CALLS
    ]


def load(root, plan):
    require(
        plan["parent_commit"] == REFERENCE and plan["retained_raw_commit"] == RAW,
        "reference_identity",
    )
    require(set(plan["input_files"]) == set(input_names()), "input_inventory")
    for name in input_names():
        data = read(root, name)
        require(sha(data) == plan["input_files"][name], "input_hash:" + name)
        require(data == git(root, "show", REFERENCE + ":" + name), "input_reference")
    admitted = json.loads(read(root, PREVIOUS + "proof/admission.json"))
    require(
        admitted["iteration"] == 181
        and admitted["phase"] == "closed"
        and admitted["raw_commit"] == RAW
        and admitted["complete_cases"] == 2
        and admitted["qualified_for_source_comparison"] is False,
        "reference_admission",
    )
    cases = {c["id"]: c for c in json.loads(read(root, CASES))}
    result = []
    for name, calls in CALLS.items():
        event_path = PREVIOUS + f"proof/search_raw/{name}/events.jsonl"
        data = read(root, event_path)
        require(data == git(root, "show", RAW + ":" + event_path), "raw_identity")
        events = [json.loads(line) for line in data.splitlines()]
        connections = [r for r in events if r["kind"] == "connection"]
        require(
            [r["call"] for r in connections] == list(range(1, CONNECTIONS[name] + 1)),
            "connection_order",
        )
        selected = [
            r
            for r in connections
            if r["result"] is not None
            and len(r["trace"]) > 1
            and r["trace"][-1]["frame"] >= plan["minimum_frame"]
        ]
        require(
            [r["call"] for r in selected] == plan["endpoint_calls"][name] == calls,
            "endpoint_population",
        )
        endpoints = {tuple([*r["trace"][-1]["state"], r["trace"][-1]["frame"]]) for r in selected}
        outgoing = [r["call"] for r in connections if tuple(r["before"]) in endpoints]
        trials = [r for r in events if r["kind"] == "evaluation" and r["call"] in outgoing]
        require(
            len(outgoing) == REQUESTS[name] and len(trials) == EVALUATIONS[name],
            "request_population",
        )
        result.append((cases[name], connections, selected, trials))
    return result


def through_first_rejection(trial):
    for row in trial["trace"]:
        yield row
        if row["reason"] != "clear":
            break
