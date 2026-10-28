"""Exact qualification scope and imported historical byte preservation."""

import json
from .common import AUDIT, BASE, PARENT, PREVIOUS, git, read, require

FILES = (
    "__init__.py",
    "common.py",
    "population.py",
    "population_check.py",
    "POPULATION.json",
    "PROTOCOL.md",
    "RESEARCH.md",
    "policy.py",
    "policy_check.py",
    "forward.py",
    "adapter.py",
    "replay.py",
    "wiring.py",
    "callback_check.py",
    "worker.py",
    "fixtures.py",
    "runtime.py",
    "produce.py",
    "check.py",
    "records.py",
    "run.py",
    "contract.py",
    "QUALIFICATION.json",
)
TEST = "tests/test_iter191_stop_wait_release.py"


def inventory(root):
    previous = json.loads(read(root, AUDIT / "PLAN.json"))
    pop = json.loads(read(root, BASE / "POPULATION.json"))
    return (
        set(previous["source_files"])
        | set(pop["inputs"])
        | {str(AUDIT / "PLAN.json"), TEST, *(str(BASE / n) for n in FILES)}
    )


def fixed():
    return dict(
        iteration=191,
        schema="sentinel.iter191.plan.v1",
        parent_commit=PARENT,
        population_commit="c27ee6899e13782696feda76fb0f04c4a3235de3",
        status="preregistered",
        arms=["baseline", "candidate"],
        original_requests=23,
        goal_requests=21,
        native_fixtures=["untimed", "timed_straight", "timed_curve"],
        native_seed=20261028,
        native_attempts=512,
        native_seconds=10,
        native_supervisor_seconds=15,
        qualification_producer_seconds=1200,
        qualification_checker_seconds=5400,
        max_rss_bytes=1073741824,
        max_output_bytes=268435456,
        minimum_free_bytes=2147483648,
    )


def check_contract(root, plan):
    require(set(plan) == set(fixed()) | {"source_files"}, "plan_fields")
    for name, value in fixed().items():
        require(plan[name] == value, "plan_changed:" + name)
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
        (
            planner["connection_horizon"],
            planner["connection_attempt_budget"],
            planner["attempt_budget"],
            planner["per_run_seconds"],
        )
        == (8, 128, 18000, 120),
        "planner_envelope",
    )
    return True
