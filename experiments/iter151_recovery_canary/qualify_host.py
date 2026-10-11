"""CPU-only Linux ownership checks; no scientific worker imports or launch path."""

import argparse
from copy import deepcopy
import os
from pathlib import Path
import subprocess
import sys
import time

from .admission import PLAN, identity
from .ownership import capture, alive, check_service
from .records import read, record
from experiments.iter150_cloud_observation.native import bind, observe
from experiments.iter149_observation_recovery.recovery import classify


def child(control, unit):
    config = read(control / "fixture.json")
    record(control / "pair_000_started.json", dict(pair=0, plan_sha256=PLAN))
    capture(control, 0, config["binding"], check_service(unit))
    (control / "partial.txt").write_text("CPU fixture only; no scientific outcome\n")
    time.sleep(60)


def qualify(directory, document, environment, token):
    directory = Path(directory)
    directory.mkdir(exist_ok=False)
    record(directory / "fixture.json", dict(binding=environment))
    record(directory / "plan.json", document)
    record(directory / "execution_manifest.json", {"scope": "CPU fixture only"})
    unit = "sentinel151-ownership-" + token + ".service"
    argv = [sys.executable, "-m", __name__, "--child", "--control", str(directory), "--unit", unit]
    command = [
        "systemd-run",
        "--unit",
        unit,
        "--property=RuntimeMaxSec=2500",
        "--property=KillMode=control-group",
        "--setenv=PYTHONPATH=" + os.environ["PYTHONPATH"],
        *argv,
    ]
    launched = subprocess.run(command, capture_output=True, text=True, timeout=10)
    if launched.returncode:
        raise ValueError("fixture_launch:" + launched.stderr)
    result = dict(status="running", unit=unit, command=command, scientific_outcomes=0)
    try:
        for _ in range(100):
            if (directory / "pair_000_owner.json").exists():
                break
            time.sleep(0.05)
        owner = read(directory / "pair_000_owner.json")
        if (
            owner["service"]["ActiveState"] != "active"
            or int(owner["service"]["MainPID"]) != owner["process"]["pid"]
        ):
            raise ValueError("fixture_service_owner")
        binding, _ = bind(directory, 0, environment)
        if not alive(owner, binding):
            raise ValueError("fixture_not_alive")
        raw, blobs = observe(directory, 0, binding, binding, "host/0", alive=True)
        if classify(raw, blobs, "host/0", binding, -1, None)[0] != "worker_running":
            raise ValueError("running_observation")
        rejected = []
        for key in ("start_ticks", "command", "boot", "executable", "cwd"):
            bad = deepcopy(owner)
            bad["process"][key] = "different"
            try:
                alive(bad, binding)
            except ValueError:
                rejected.append(key)
            else:
                raise ValueError("accepted_bad_owner:" + key)
        before = {p.name: identity(read(p)) for p in directory.glob("*.json")}
        duplicate = subprocess.run(argv, capture_output=True, text=True, timeout=10)
        after = {p.name: identity(read(p)) for p in directory.glob("*.json")}
        if duplicate.returncode == 0 or before != after:
            raise ValueError("duplicate_fixture")
        result.update(
            owner=owner,
            rejected=rejected,
            duplicate_returncode=duplicate.returncode,
            duplicate_stderr=duplicate.stderr,
            records_unchanged=True,
            running_raw_hex=raw.hex(),
        )
    finally:
        stopped = subprocess.run(
            ["systemctl", "stop", unit], capture_output=True, text=True, timeout=10
        )
        result["stop_returncode"] = stopped.returncode
    if alive(owner, binding) or stopped.returncode:
        raise ValueError("fixture_termination")
    raw, blobs = observe(directory, 0, binding, binding, "host/1", alive=False)
    if classify(raw, blobs, "host/1", binding, -1, None)[0] != "partial_evidence":
        raise ValueError("partial_promoted")
    # An independent shorter systemd deadline exercises the same control-group mechanism.
    deadline_unit = "sentinel151-deadline-" + token + ".service"
    deadline_command = [
        "systemd-run",
        "--unit",
        deadline_unit,
        "--property=RuntimeMaxSec=2",
        "--property=KillMode=control-group",
        "/bin/sleep",
        "60",
    ]
    q = subprocess.run(deadline_command, capture_output=True, text=True, timeout=10)
    if q.returncode:
        raise ValueError("deadline_fixture_launch")
    started = time.monotonic()
    for _ in range(100):
        q = subprocess.run(
            [
                "systemctl",
                "show",
                deadline_unit,
                "--property=ActiveState,Result,MainPID,RuntimeMaxUSec,KillMode",
            ],
            capture_output=True,
            text=True,
            timeout=3,
        )
        state = dict(line.split("=", 1) for line in q.stdout.splitlines())
        if q.returncode == 0 and state.get("Result") == "timeout" and state.get("MainPID") == "0":
            break
        time.sleep(0.1)
    else:
        subprocess.run(["systemctl", "stop", deadline_unit], timeout=10, check=False)
        raise ValueError("deadline_fixture_not_closed")
    result.update(
        status="supported",
        partial_raw_hex=raw.hex(),
        deadline=state,
        deadline_elapsed=time.monotonic() - started,
        partial_preserved=(directory / "partial.txt").is_file(),
    )
    record(directory.parent / "host_qualification.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", action="store_true", required=True)
    parser.add_argument("--control", type=Path, required=True)
    parser.add_argument("--unit", required=True)
    args = parser.parse_args()
    child(args.control, args.unit)
