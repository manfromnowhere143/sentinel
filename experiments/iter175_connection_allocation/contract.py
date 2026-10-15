"""Admit one connection-cap change against the retained Iter174 contract."""

import json

from .common import BASE, git, read, require

REFERENCE = "c3320124da21d9407e268d81cf0eb3630044d3dd"
PREVIOUS = "experiments/iter174_forward_integrated_rrt/"


def check_contract(root, plan):
    old = json.loads(read(root, PREVIOUS + "PLAN.json"))
    require(set(plan) == set(old), "plan_fields")
    metadata = {"iteration", "schema", "parent_commit", "scope", "source_files"}
    for key, value in old.items():
        if key not in metadata | {"connection_attempt_budget"}:
            require(plan[key] == value, "changed_contract:" + key)
    require(type(plan["connection_attempt_budget"]) is int
            and plan["connection_attempt_budget"] == 128, "connection_cap")
    require(old["connection_attempt_budget"] == 1024, "reference_cap")
    require(plan["parent_commit"] == REFERENCE, "reference_identity")
    require(plan["iteration"] == 175 and plan["schema"] == "sentinel.iter175.plan.v1",
            "study_identity")
    for name in ["adapter.py", "RUNTIME.json"]:
        require(read(root, BASE / name) == read(root, PREVIOUS + name), "unchanged:" + name)
    for name in ["PLAN.json", "adapter.py", "RUNTIME.json", "proof/admission.json"]:
        path = PREVIOUS + name
        require(read(root, path) == git(root, "show", REFERENCE + ":" + path),
                "reference_changed:" + name)


def reference(root):
    return json.loads(read(root, PREVIOUS + "proof/admission.json"))
