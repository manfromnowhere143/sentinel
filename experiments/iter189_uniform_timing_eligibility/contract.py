"""Freeze the composed intervention, retained population and unchanged ceilings."""

import json

from .common import BASE, git, read, require

PARENT = "f17402aa56c67cdbf215f9c977a033b8971acabe"
PREVIOUS = "experiments/iter187_integrated_branch_retention/"
BOUND = "experiments/iter188_early_timing_feasibility/"
NEW_FILES = (
    "__init__.py",
    "adapter.py",
    "check.py",
    "common.py",
    "contract.py",
    "eligibility.py",
    "eligibility_check.py",
    "fixtures.py",
    "records.py",
    "retained.py",
    "retained_check.py",
    "run.py",
    "runtime.py",
    "worker.py",
    "qualify.py",
    "PROTOCOL.md",
    "DECISION_PACKET.md",
    "RESEARCH.md",
    "RUNTIME.json",
    "QUALIFICATION.md",
)
TEST = "tests/test_iter189_uniform_timing.py"


def inventory(root):
    parent = json.loads(read(root, PREVIOUS + "PLAN.json"))
    bound = json.loads(read(root, BOUND + "PLAN.json"))
    return (
        set(parent["source_files"])
        | set(bound["source_files"])
        | set(bound["inputs"])
        | {str(BASE / name) for name in NEW_FILES}
        | {
            TEST,
            PREVIOUS + "PLAN.json",
            PREVIOUS + "proof/admission.json",
            BOUND + "PLAN.json",
            BOUND + "proof/admission.json",
        }
    )


def check_contract(root, plan):
    old = json.loads(read(root, PREVIOUS + "PLAN.json"))
    require(set(plan) == set(old), "plan_fields")
    expected = inventory(root)
    require(
        set(plan["source_files"]) == expected and len(plan["source_files"]) == len(expected),
        "source_inventory",
    )
    for key, value in old.items():
        if key not in {"iteration", "schema", "parent_commit", "scope", "source_files", "arms"}:
            require(plan[key] == value, "changed_contract:" + key)
    require(
        plan["iteration"] == 189
        and plan["schema"] == "sentinel.iter189.plan.v1"
        and plan["parent_commit"] == PARENT,
        "plan_identity",
    )
    require(plan["arms"] == ["modified_rrt_uniform_timing"], "named_modified_planner")
    require(
        read(root, BASE / "RUNTIME.json") == read(root, PREVIOUS + "RUNTIME.json"),
        "qualified_runtime",
    )
    for name in sorted(expected):
        if not name.startswith(str(BASE) + "/") and name != TEST:
            require(
                read(root, name) == git(root, "show", PARENT + ":" + name), "parent_changed:" + name
            )
    return True
