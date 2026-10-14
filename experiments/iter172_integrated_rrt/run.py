"""Bounded four-case prospective qualification; subprocesses isolate native RNGs."""

import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

from .common import BASE, read, require
from .records import initialize, finish, failure
from .runtime import verify


def run(root, source, library):
    started = time.monotonic()
    verify(root, library)
    output = root / BASE / "proof/search_raw"
    output.parent.mkdir(exist_ok=True)
    plan = initialize(root, output, source, "search")
    records = []
    try:
        for name, seed in zip(plan["cases"], plan["seeds"]):
            folder = output / name
            folder.mkdir()
            with (
                (folder / "stdout.txt").open("xb") as out,
                (folder / "stderr.txt").open("xb") as err,
            ):
                command = [
                    sys.executable,
                    "-m",
                    "experiments.iter172_integrated_rrt.worker",
                    "--root",
                    str(root),
                    "--output",
                    str(folder),
                    "--case",
                    name,
                    "--seed",
                    str(seed),
                    "--library",
                    str(library),
                ]
                process = subprocess.Popen(command, cwd=root, stdout=out, stderr=err)
                try:
                    code = process.wait(timeout=plan["per_run_seconds"] + 60)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                    raise ValueError("worker_deadline")
            require(code == 0, "worker_failed:" + name)
            record = json.loads(read(folder, "result.json"))
            records.append(record)
            print(json.dumps(record), flush=True)
        finish(output, source, plan, "search", started, records=records, children_reaped=True)
    except Exception as exc:
        failure(output, started, exc)
        raise


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--source", required=True)
    p.add_argument("--library", type=Path, required=True)
    a = p.parse_args()
    run(a.root.resolve(), a.source, a.library.resolve())
