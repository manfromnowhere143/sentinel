"""Gate the source test on admitted all-four integration and a fixed six-row design."""

import json
from .common import BASE, HISTORY, PREVIOUS, git, read, require

PARENT = "3c0bed93455282ace9f944d408185a1d4e2c4113"
FILES = (
    "__init__.py",
    "common.py",
    "contract.py",
    "clock.py",
    "records.py",
    "worker.py",
    "produce.py",
    "check.py",
    "run.py",
    "PROTOCOL.md",
    "QUALIFICATION.json",
    "qualification/initial.txt",
    "qualification/gates.txt",
    "qualification/final.txt",
)
TEST = "tests/test_iter193_history_delay.py"


def fixed():
    return dict(
        schema="sentinel.iter193.plan.v1",
        iteration=193,
        status="preregistered",
        parent_commit=PARENT,
        conditions=[
            dict(id=f"origin_{o}_delay_{d}", origin=o, delay=d, seed=20261014)
            for o in (23, 25)
            for d in (0, 1, 2)
        ],
        search_producer_seconds=1800,
        search_checker_seconds=7200,
        worker_supervisor_seconds=180,
        max_rss_bytes=1073741824,
        max_output_bytes=536870912,
        minimum_free_bytes=4294967296,
    )


def inventory(root):
    previous = json.loads(read(root, PREVIOUS / "PLAN.json"))
    history = json.loads(read(root, HISTORY / "PLAN.json"))
    return (
        set(previous["source_files"])
        | set(history["source_files"])
        | set(history["inputs"])
        | {
            str(PREVIOUS / "PLAN.json"),
            str(PREVIOUS / "proof/admission.json"),
            str(HISTORY / "PLAN.json"),
            str(HISTORY / "proof/prefix_admission.json"),
            str(HISTORY / "proof/prefix_raw/replica_0/trace.json"),
            str(HISTORY / "proof/prefix_raw/replica_1/trace.json"),
            TEST,
            *(str(BASE / n) for n in FILES),
        }
    )


def integration_gate(admission):
    require(
        admission["status"] == "supported" and admission["complete_cases"] == 4,
        "integration_unqualified",
    )


def check_contract(root, plan):
    require(set(plan) == set(fixed()) | {"source_files"}, "plan_fields")
    for k, v in fixed().items():
        require(plan[k] == v, "plan_changed:" + k)
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
    admission = json.loads(read(root, PREVIOUS / "proof/admission.json"))
    integration_gate(admission)
    qualification = json.loads(read(root, BASE / "QUALIFICATION.json"))
    require(qualification["status"] == "supported", "clock_adapter_unqualified")
    return True
