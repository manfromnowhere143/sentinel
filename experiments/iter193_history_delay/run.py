"""External process-group deadline supervisor, exclusive logs and no retry."""

import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
from .common import BASE, read


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--stage", choices=["acquire", "check"], required=True)
    p.add_argument("--source")
    p.add_argument("--raw-commit")
    p.add_argument("--report", type=Path, required=True)
    a = p.parse_args()
    plan = json.loads(read(Path.cwd(), BASE / "PLAN.json"))
    module = "produce" if a.stage == "acquire" else "check"
    command = [sys.executable, "-m", "experiments.iter193_history_delay." + module]
    command += ["--source", a.source] if a.stage == "acquire" else ["--raw-commit", a.raw_commit]
    limit = (
        plan["search_producer_seconds" if a.stage == "acquire" else "search_checker_seconds"] + 10
    )
    with a.report.open("xb") as stream:
        process = subprocess.Popen(
            command, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True
        )
        try:
            code = process.wait(timeout=limit)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            raise ValueError("supervisor_deadline")
    if code:
        raise SystemExit(code)
