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
from .fixtures import inputs as fixture_inputs
from .retained import produce as retained_produce
from .retained_check import check as retained_check


def checked_inputs(root, folder, timed):
    value = json.loads(read(folder, "inputs.json"))
    require(value == fixture_inputs(root, timed), "qualification_inputs")
    return value


def acquire(root, source, library, prefix):
    started = time.monotonic()
    output = root / BASE / "proof/qualification_raw"
    output.parent.mkdir(exist_ok=True)
    plan = initialize(root, output, source, "qualification")
    try:
        check_contract(root, plan)
        verify(root, library, prefix)
        retained_produce(root, output / "retained.json")
        for name, timed in (("constructed", False), ("timed", True)):
            with (
                (output / (name + "_stdout.txt")).open("xb") as out,
                (output / (name + "_stderr.txt")).open("xb") as err,
            ):
                subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "experiments.iter189_uniform_timing_eligibility.fixtures",
                        "--root",
                        str(root),
                        "--library",
                        str(library),
                        "--output",
                        str(output / name),
                    ]
                    + (["--timed"] if timed else []),
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
            constructed_runs=2,
            retained_records=264,
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
        and execution["constructed_runs"] == 2
        and execution["retained_records"] == 264
        and execution["integrated_development_runs"] == 0,
        "qualification_scope",
    )
    deadline = started + plan["qualification_checker_seconds"]
    retained = retained_check(root, raw / "retained.json", deadline)
    results = {}
    for name, timed in (("constructed", False), ("timed", True)):
        folder = raw / name
        inputs = checked_inputs(root, folder, timed)
        result = case_check(
            folder,
            inputs["case"],
            inputs["old"],
            inputs["plan"],
            json.loads(read(folder, "result.json")),
            deadline,
        )
        require(result["seed"] == (20261028 if timed else 20261027), "qualification_seed")
        results[name] = result
    result = results["constructed"]
    require(
        result["attempts"] == 510
        and result["registered_extra"] == 3
        and result["selected_extra"] == 2
        and result["distinct_registered_states"] == 27,
        "constructed_expected",
    )
    require(
        results["timed"]["eligibility"]["uniform"].get("early_first_excluded_prefixes", 0) > 0,
        "constructed_timing_not_exercised",
    )
    from .common import rss

    require(
        time.monotonic() < deadline and rss() <= plan["max_rss_bytes"],
        "qualification_checker_resources",
    )
    receipt = dict(
        status="supported",
        source_commit=execution["source_commit"],
        raw_commit=raw_commit,
        results=results,
        retained=retained,
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
