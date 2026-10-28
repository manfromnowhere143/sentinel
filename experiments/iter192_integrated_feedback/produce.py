"""One prospective, ordered all-four acquisition with isolated native RNGs."""

import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
from experiments.iter191_stop_wait_release.runtime import verify
from .common import BASE, read, require
from .contract import check_contract
from .records import initialize, finish, failure


def run(root, source):
    started = time.monotonic()
    verify(root)
    check_contract(root, json.loads(read(root, BASE / "PLAN.json")))
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
                    "experiments.iter192_integrated_feedback.worker",
                    "--output",
                    str(folder),
                    "--case",
                    name,
                    "--seed",
                    str(seed),
                ]
                process = subprocess.Popen(command, cwd=root, stdout=out, stderr=err)
                try:
                    code = process.wait(timeout=plan["worker_supervisor_seconds"])
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                    raise ValueError("worker_deadline:" + name)
            require(code == 0, "worker_failed:" + name)
            record = json.loads(read(folder, "result.json"))
            records.append(record)
            print(json.dumps(record), flush=True)
        finish(
            output,
            source,
            plan,
            "search",
            started,
            records=records,
            children_reaped=True,
            new_integrated_runs=4,
        )
    except Exception as exc:
        failure(output, started, exc)
        raise


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True)
    a = p.parse_args()
    run(Path.cwd(), a.source)
