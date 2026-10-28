"""Exact proposal, controls, retained comparators and prospective case schedule."""

import json
from .common import BASE, PARENT, PREVIOUS, MECHANISM, git, read, require

FILES = (
    "__init__.py",
    "common.py",
    "contract.py",
    "records.py",
    "worker.py",
    "produce.py",
    "check.py",
    "run.py",
    "PROTOCOL.md",
    "QUALIFICATION.json",
    "qualification/initial.txt",
    "qualification/recheck.txt",
)
TEST = "tests/test_iter192_integrated_feedback.py"


def fixed():
    return dict(
        schema="sentinel.iter192.plan.v1",
        iteration=192,
        status="preregistered",
        parent_commit=PARENT,
        protocol_commit="f3d547eafb3d59afcae728a40c8843d7a5689289",
        cases=["bend_left", "bend_right", "chicane_left", "chicane_right"],
        seeds=[20261014, 20261015, 20261016, 20261017],
        arms=["exact_iter191_feedback"],
        retained_comparators=[189, 183],
        search_producer_seconds=900,
        search_checker_seconds=7200,
        worker_supervisor_seconds=180,
        max_rss_bytes=1073741824,
        max_output_bytes=268435456,
        minimum_free_bytes=2147483648,
    )


def inventory(root):
    mechanism = json.loads(read(root, MECHANISM / "PLAN.json"))
    return set(mechanism["source_files"]) | {
        str(MECHANISM / "PLAN.json"),
        str(MECHANISM / "proof/admission.json"),
        str(PREVIOUS / "proof/admission.json"),
        "experiments/iter183_timing_eligibility/proof/admission.json",
        TEST,
        *(str(BASE / name) for name in FILES),
    }


def check_contract(root, plan):
    require(set(plan) == set(fixed()) | {"source_files"}, "plan_fields")
    for key, value in fixed().items():
        require(plan[key] == value, "plan_changed:" + key)
    expected = inventory(root)
    require(
        set(plan["source_files"]) == expected and len(plan["source_files"]) == len(expected),
        "source_inventory",
    )
    for name in sorted(expected):
        if not name.startswith(str(BASE) + "/") and name != TEST:
            require(
                read(root, name) == git(root, "show", PARENT + ":" + name),
                "historical_change:" + name,
            )
    planner = json.loads(read(root, PREVIOUS / "PLAN.json"))
    require(
        planner["cases"] == plan["cases"] and planner["seeds"] == plan["seeds"],
        "planner_population",
    )
    qualification = json.loads(read(root, MECHANISM / "proof/admission.json"))
    require(
        qualification["iteration"] == 191 and qualification["status"] == "supported",
        "mechanism_unqualified",
    )
    return True
