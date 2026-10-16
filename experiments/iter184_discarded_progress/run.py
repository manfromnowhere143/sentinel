"""One fixed three-root schedule after committed independent prefix admission."""

import argparse
from pathlib import Path
import subprocess
import sys
import time

from .common import BASE, document, require
from .records import initialize, finish, failure
from .runtime import verify
from .contract import check_plan
from .audit_check import admitted


def run(root, source, library, audit_commit):
    started = time.monotonic()
    verify(root, library)
    plan = document(root, BASE / "PLAN.json")
    check_plan(root, plan)
    audit, audit_hash = admitted(root, audit_commit, plan)
    require(audit["source_commit"] == source, "same_frozen_source")
    raw = root / BASE / "proof/search_raw"
    plan = initialize(root, raw, source, "search")
    records = []
    try:
        for index, root_id in enumerate(plan["probe_roots"]):
            folder = raw / f"probe_{index}"
            folder.mkdir()
            command = [
                sys.executable,
                "-m",
                "experiments.iter184_discarded_progress.worker",
                "--root",
                str(root),
                "--output",
                str(folder),
                "--index",
                str(index),
                "--library",
                str(library),
            ]
            with (
                (folder / "stdout.txt").open("xb") as out,
                (folder / "stderr.txt").open("xb") as err,
            ):
                process = subprocess.Popen(command, cwd=root, stdout=out, stderr=err)
                try:
                    code = process.wait(timeout=180)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                    raise ValueError("worker_deadline") from None
            require(code == 0, "worker_failed:" + str(root_id))
            records.append(document(folder, "result.json"))
            print(
                {k: records[-1][k] for k in ["root_identity", "complete", "attempts", "stop"]},
                flush=True,
            )
        finish(
            raw,
            source,
            plan,
            "search",
            started,
            records=records,
            children_reaped=True,
            audit_admission_commit=audit_commit,
            audit_admission_sha256=audit_hash,
            new_integrated_schedules=0,
            conditional_searches=3,
        )
    except Exception as error:
        failure(raw, started, error)
        raise


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--source", required=True)
    p.add_argument("--library", type=Path, required=True)
    p.add_argument("--audit-commit", required=True)
    a = p.parse_args()
    run(a.root.resolve(), a.source, a.library.resolve(), a.audit_commit)
