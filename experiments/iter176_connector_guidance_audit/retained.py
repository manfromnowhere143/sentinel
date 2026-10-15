"""Bound retained inputs and chronological extraction; no audit algorithms."""

import json

from experiments.iter161_grouping_width_ablation.reflection import check_cases
from .common import git, read, require, sha

REFERENCE = "20130fd53a35040efa2f48e5019349feaa724233"
RAW = "19233bf7c5215000e289d49111d10b5ed0c5e537"
PREVIOUS = "experiments/iter175_connection_allocation/"
CASES = "experiments/iter161_grouping_width_ablation/CASES.json"
EARLIER = "experiments/iter159_route_search_qualification/CASES.json"
OLD = "experiments/iter153_action_feasibility/PLAN.json"
NAMES = ["bend_left", "bend_right", "chicane_left", "chicane_right"]


def verify_inputs(root, plan):
    require(plan["parent_commit"] == REFERENCE and plan["retained_raw_commit"] == RAW,
            "reference_identity")
    require(plan["cases"] == NAMES, "case_population")
    paths = [PREVIOUS + "PLAN.json", PREVIOUS + "proof/admission.json", CASES, EARLIER, OLD]
    paths += [PREVIOUS + f"proof/search_raw/{case}/events.jsonl" for case in NAMES]
    require(set(plan["input_files"]) == set(paths), "input_inventory")
    for name in paths:
        content = read(root, name)
        require(sha(content) == plan["input_files"][name], "input_hash:" + name)
        require(content == git(root, "show", REFERENCE + ":" + name), "input_reference:" + name)
        if name.endswith("events.jsonl"):
            require(content == git(root, "show", RAW + ":" + name), "retained_raw_identity")
    admission = json.loads(read(root, PREVIOUS + "proof/admission.json"))
    require(admission["iteration"] == 175 and admission["phase"] == "closed"
            and admission["raw_commit"] == RAW and admission["complete_cases"] == 2
            and admission["qualified_for_source_comparison"] is False, "reference_admission")
    cases = json.loads(read(root, CASES))
    check_cases(cases, json.loads(read(root, EARLIER)))
    return cases


def case_records(root, name, plan):
    connections, trials = [], {}
    for line in read(root, PREVIOUS + f"proof/search_raw/{name}/events.jsonl").splitlines():
        row = json.loads(line)
        if row["kind"] == "connection":
            require(row["call"] == len(connections) + 1, "connection_order")
            connections.append(row)
        if (name == plan["selected_case"] and row["kind"] == "evaluation"
                and row["call"] == plan["selected_call"]
                and row["id"] in plan["selected_evaluations"]):
            require(row["id"] not in trials, "duplicate_trial")
            trials[row["id"]] = row
    return connections, trials


def request_identity(case, row):
    return dict(case=case, call=row["call"], before=row["before"], target=row["target"],
                task=row["task"], budget=row["budget"])
