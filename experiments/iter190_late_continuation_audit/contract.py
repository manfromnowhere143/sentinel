"""Freeze all new code and imported historical evidence without rewriting it."""

import json
from .common import BASE, PARENT, PREVIOUS, read, require, git

FILES = (
    "__init__.py",
    "common.py",
    "population.py",
    "population_check.py",
    "POPULATION.json",
    "PROTOCOL.md",
    "probe.py",
    "probe_check.py",
    "masks.py",
    "produce.py",
    "check.py",
    "records.py",
    "runtime.py",
    "RUNTIME.json",
    "fixtures.py",
    "qualify.py",
    "QUALIFICATION.json",
    "contract.py",
    "run.py",
)
TEST = "tests/test_iter190_late_continuation.py"


def inventory(root):
    old = json.loads(read(root, PREVIOUS / "PLAN.json"))
    pop = json.loads(read(root, BASE / "POPULATION.json"))
    names = set(old["source_files"]) | set(pop["inputs"]) | {str(BASE / f) for f in FILES} | {TEST}
    admission = json.loads(read(root, PREVIOUS / "proof/admission.json"))
    for r in admission["records"]:
        if r["complete"]:
            folder = PREVIOUS / "proof/search_raw" / r["case"] / "selected"
            names |= {str(p.relative_to(root)) for p in (root / folder).glob("mask_*.bin")}
    return names


def check_contract(root, plan):
    expected = dict(
        iteration=190,
        schema="sentinel.iter190.plan.v1",
        parent_commit=PARENT,
        status="preregistered",
        arms=["stop_wait_route", "beam_then_route"],
        per_arm_attempts=2048,
        per_arm_seconds=20,
        audit_producer_seconds=1200,
        audit_checker_seconds=5400,
        max_rss_bytes=1073741824,
        max_output_bytes=268435456,
        minimum_free_bytes=2147483648,
    )
    require(set(plan) == set(expected) | {"source_files"}, "plan_fields")
    for key, value in expected.items():
        require(plan[key] == value, "plan_changed:" + key)
    required = inventory(root)
    require(
        set(plan["source_files"]) == required and len(required) == len(plan["source_files"]),
        "source_inventory",
    )
    for name in sorted(required):
        if not name.startswith(str(BASE) + "/") and name != TEST:
            require(
                read(root, name) == git(root, "show", PARENT + ":" + name),
                "historical_change:" + name,
            )
    return True
