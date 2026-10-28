"""One frozen six-condition source acquisition; no native driving episodes."""

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
    results = []
    try:
        for condition in plan["conditions"]:
            folder = output / condition["id"]
            folder.mkdir()
            with (
                (folder / "stdout.txt").open("xb") as out,
                (folder / "stderr.txt").open("xb") as err,
            ):
                command = [
                    sys.executable,
                    "-m",
                    "experiments.iter193_history_delay.worker",
                    "--output",
                    str(folder),
                    "--condition",
                    condition["id"],
                ]
                process = subprocess.Popen(command, cwd=root, stdout=out, stderr=err)
                try:
                    code = process.wait(timeout=plan["worker_supervisor_seconds"])
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                    raise ValueError("worker_deadline:" + condition["id"])
            require(code == 0, "worker_failed:" + condition["id"])
            result = json.loads(read(folder, "result.json"))
            results.append(result)
            print(json.dumps(result), flush=True)
        finish(output, source, plan, "search", started, records=results, children_reaped=True)
    except Exception as exc:
        failure(output, started, exc)
        raise


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True)
    a = p.parse_args()
    run(Path.cwd(), a.source)
