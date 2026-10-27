"""Frozen constructed worker acquisition and separately committed admission."""

import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

from .common import BASE, read, write, require, git
from .records import initialize, finish, failure, committed
from .contract import check_contract
from .runtime import verify
from .check import case_check


def acquire(root, source, library, prefix):
    started = time.monotonic()
    output = root / BASE / "proof/qualification_raw"
    output.parent.mkdir(exist_ok=True)
    plan = initialize(root, output, source, "qualification")
    try:
        check_contract(root, plan)
        verify(root, library, prefix)
        with (output / "stdout.txt").open("xb") as out, (output / "stderr.txt").open("xb") as err:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "experiments.iter187_integrated_branch_retention.fixtures",
                    "--root",
                    str(root),
                    "--library",
                    str(library),
                    "--output",
                    str(output / "constructed"),
                ],
                cwd=root,
                stdout=out,
                stderr=err,
                check=True,
                timeout=30,
            )
        verify(root, library, prefix)
        finish(
            output,
            source,
            plan,
            "qualification",
            started,
            children_reaped=True,
            constructed_runs=1,
            integrated_development_runs=0,
        )
    except Exception as exc:
        failure(output, started, exc)
        raise


def admit(root, raw_commit):
    started = time.monotonic()
    plan = json.loads(read(root, BASE / "PLAN.json"))
    check_contract(root, plan)
    raw = root / BASE / "proof/qualification_raw"
    execution = committed(root, raw, raw_commit, plan)
    require(
        execution["children_reaped"] is True
        and execution["constructed_runs"] == 1
        and execution["integrated_development_runs"] == 0,
        "qualification_scope",
    )
    folder = raw / "constructed"
    inputs = json.loads(read(folder, "inputs.json"))
    require(inputs["case"]["id"] == "constructed_straight", "qualification_case")
    result = case_check(
        folder,
        inputs["case"],
        inputs["old"],
        inputs["plan"],
        json.loads(read(folder, "result.json")),
        started + plan["qualification_checker_seconds"],
    )
    require(
        result["attempts"] == 510
        and result["registered_extra"] == 3
        and result["selected_extra"] == 2
        and result["distinct_registered_states"] == 27,
        "constructed_expected",
    )
    receipt = dict(
        status="supported",
        source_commit=execution["source_commit"],
        raw_commit=raw_commit,
        result=result,
        elapsed_seconds=time.monotonic() - started,
    )
    write(root / BASE / "proof/qualification_admission.json", receipt)
    return receipt


def admitted(root, source, commit):
    path = BASE / "proof/qualification_admission.json"
    data = read(root, path)
    require(git(root, "show", commit + ":" + str(path)) == data, "qualification_commit")
    value = json.loads(data)
    require(
        value["status"] == "supported" and value["source_commit"] == source, "qualification_source"
    )
    git(root, "merge-base", "--is-ancestor", value["raw_commit"], commit)
    git(root, "merge-base", "--is-ancestor", commit, "HEAD")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--source")
    p.add_argument("--raw-commit")
    p.add_argument("--library", type=Path)
    p.add_argument("--prefix", type=Path)
    a = p.parse_args()
    if a.raw_commit:
        print(json.dumps(admit(a.root.resolve(), a.raw_commit)))
    else:
        acquire(a.root.resolve(), a.source, a.library.resolve(), a.prefix.resolve())
