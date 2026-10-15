"""Immutable retained inputs and chronological inventory; no search or geometry."""

import json
import struct

from .common import read, require, sha, git

REFERENCE = "82d93e69d6cfc3e1548d039f607bfa552a60ee0b"
RAW = "1ba6a4e90db895fe2991eeb2df26fc3b48ccdeba"
PREVIOUS = "experiments/iter178_root_domain_consistency/"
EVENTS = PREVIOUS + "proof/search_raw/bend_right/events.jsonl"
CASES = "experiments/iter161_grouping_width_ablation/CASES.json"
OLD = "experiments/iter153_action_feasibility/PLAN.json"
CALLS = [3, 51, 59, 63, 64, 67, 69, 84, 85, 88, 91, 92, 94, 99, 110, 112, 121, 131, 132]


def state_key(state):
    return sha(struct.pack(">5d", *state))


def load(root, plan):
    require(
        plan["parent_commit"] == REFERENCE and plan["retained_raw_commit"] == RAW,
        "reference_identity",
    )
    names = [EVENTS, CASES, OLD, PREVIOUS + "PLAN.json", PREVIOUS + "proof/admission.json"]
    require(set(plan["input_files"]) == set(names), "input_inventory")
    for name in names:
        data = read(root, name)
        require(sha(data) == plan["input_files"][name], "input_hash:" + name)
        require(data == git(root, "show", REFERENCE + ":" + name), "input_reference")
    require(read(root, EVENTS) == git(root, "show", RAW + ":" + EVENTS), "raw_identity")
    admission = json.loads(read(root, PREVIOUS + "proof/admission.json"))
    require(
        admission["iteration"] == 178
        and admission["phase"] == "closed"
        and admission["raw_commit"] == RAW
        and admission["complete_cases"] == 3
        and admission["qualified_for_source_comparison"] is False,
        "reference_admission",
    )
    case = next(c for c in json.loads(read(root, CASES)) if c["id"] == "bend_right")
    events = [json.loads(line) for line in read(root, EVENTS).splitlines()]
    connections = [r for r in events if r["kind"] == "connection"]
    require([r["call"] for r in connections] == list(range(1, 142)), "connection_order")
    selected = [
        r
        for r in connections
        if r["result"] is not None
        and len(r["trace"]) > 1
        and r["trace"][-1]["frame"] >= plan["minimum_frame"]
    ]
    require([r["call"] for r in selected] == plan["endpoint_calls"] == CALLS, "endpoint_population")
    late_calls = [r["call"] for r in connections if r["before"][5] >= plan["minimum_frame"]]
    trials = [r for r in events if r["kind"] == "evaluation" and r["call"] in late_calls]
    require(len(late_calls) == 76 and len(trials) == 2609, "request_population")
    return case, connections, selected, trials


def through_first_rejection(trial):
    for row in trial["trace"]:
        yield row
        if row["reason"] != "clear":
            break
