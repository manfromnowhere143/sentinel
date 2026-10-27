"""Retain all scientific budgets, populations and parent implementations."""

import json

from .common import BASE, git, read, require

PARENT = "d88b71637320bc482b24a6c8151505d8edcc74dc"
PREVIOUS = "experiments/iter183_timing_eligibility/"
NATIVE = "experiments/iter186_native_branch/"
NEW_FILES = (
    "__init__.py",
    "adapter.py",
    "check.py",
    "common.py",
    "contract.py",
    "fixtures.py",
    "records.py",
    "run.py",
    "runtime.py",
    "selection_check.py",
    "worker.py",
    "qualify.py",
    "PROTOCOL.md",
    "DECISION_PACKET.md",
    "RESEARCH.md",
    "RUNTIME.json",
)


def check_contract(root, plan):
    old = json.loads(read(root, PREVIOUS + "PLAN.json"))
    require(
        set(plan) == set(old) | {"qualification_producer_seconds", "qualification_checker_seconds"},
        "plan_fields",
    )
    native = json.loads(read(root, NATIVE + "PLAN.json"))
    expected = set(old["source_files"]) | set(native["source_files"])
    expected |= {str(BASE / name) for name in NEW_FILES}
    expected |= {
        "tests/test_iter187_branch_retention.py",
        PREVIOUS + "PLAN.json",
        NATIVE + "PLAN.json",
        PREVIOUS + "proof/admission.json",
        NATIVE + "proof/admission.json",
    }
    require(
        set(plan["source_files"]) == expected and len(plan["source_files"]) == len(expected),
        "source_inventory",
    )
    require(
        plan["qualification_producer_seconds"] == plan["qualification_checker_seconds"] == 120,
        "qualification_budget",
    )
    for key, value in old.items():
        if key not in {"iteration", "schema", "parent_commit", "scope", "source_files", "arms"}:
            require(plan[key] == value, "changed_contract:" + key)
    require(plan["iteration"] == 187 and plan["parent_commit"] == PARENT, "plan_identity")
    require(plan["arms"] == ["modified_rrt_one_extra"], "named_modified_planner")
    require(
        read(root, BASE / "RUNTIME.json") == read(root, NATIVE + "RUNTIME.json"),
        "qualified_runtime",
    )
    # Any imported historical implementation, comparator or evidence is frozen.
    for name in plan["source_files"]:
        if (
            not name.startswith(str(BASE) + "/")
            and name != "tests/test_iter187_branch_retention.py"
        ):
            require(
                read(root, name) == git(root, "show", PARENT + ":" + name), "parent_changed:" + name
            )
    return True
