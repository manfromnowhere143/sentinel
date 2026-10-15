"""Bind the complete admitted frontier without selecting on its outcome labels."""

import json
from experiments.iter179_frontier_continuation_audit.retained import load as old_load
from .common import document, read, git, require, sha
from .contract import PARENT

PREVIOUS = "experiments/iter179_frontier_continuation_audit/"
RAW = "16aedc124eeaddc72d8cafc326bf979ab404c90b"
PATHS = PREVIOUS + "proof/audit_raw/paths.json"
INPUTS = [PREVIOUS + "PLAN.json", PREVIOUS + "proof/admission.json", PATHS]


def load(root, plan):
    require(
        plan["parent_commit"] == PARENT and set(plan["input_files"]) == set(INPUTS),
        "input_identity",
    )
    for name in INPUTS:
        data = read(root, name)
        require(
            sha(data) == plan["input_files"][name]
            and data == git(root, "show", PARENT + ":" + name),
            "input_binding",
        )
    require(read(root, PATHS) == git(root, "show", RAW + ":" + PATHS), "frontier_raw_binding")
    prior = json.loads(read(root, PREVIOUS + "proof/admission.json"))
    require(
        prior["phase"] == "closed"
        and prior["iteration"] == 179
        and prior["retained_complete_cases"] == 3
        and prior["qualified_for_source_comparison"] is False,
        "retained_admission",
    )
    case, connections, selected, _ = old_load(root, document(root, PREVIOUS + "PLAN.json"))
    paths = document(root, PATHS)
    require(
        [p["call"] for p in paths] == [c["call"] for c in selected] and len(paths) == 19,
        "frontier_population",
    )
    require(len([p for p in paths if p["representative"] == p["call"]]) == 16, "distinct_frontier")
    return case, connections, paths
