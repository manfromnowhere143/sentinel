"""Owned, bounded provider transport. No driving launcher is exposed."""

import argparse
import datetime
import json
from pathlib import Path
import subprocess
import time

PROJECT = "sunlit-unison-487018-b0"
ZONE = "us-west1-a"
VM = "sentinel-gpu"
VM_ID = "3834622546652649531"
BASE = ["--project", PROJECT, "--zone", ZONE]


def write(path, value):
    with Path(path).open("x") as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        import os

        os.fsync(stream.fileno())


def same_start(actual, expected, running=False):
    if (
        str(actual.get("id")) != VM_ID
        or str(actual.get("id")) != str(expected.get("id"))
        or actual.get("lastStartTimestamp") != expected.get("lastStartTimestamp")
        or not actual.get("lastStartTimestamp")
    ):
        raise ValueError("provider_start_mismatch")
    if running and actual.get("status") != "RUNNING":
        raise ValueError("provider_not_running")
    return True


class Cloud:
    def __init__(self, directory, runner=subprocess.run, clock=time.monotonic):
        self.directory = Path(directory)
        self.commands = self.directory / "commands"
        self.commands.mkdir(exist_ok=True)
        self.runner, self.clock = runner, clock
        self.counter = 0

    def run(self, label, argv, timeout=45, stdin=None):
        self.counter += 1
        if not label or Path(label).name != label or "." in label:
            raise ValueError("command_label")
        stem = self.commands / label
        # labels are caller-owned and exclusive; no accidental replacement of failure evidence.
        if any(stem.with_suffix(s).exists() for s in (".stdout", ".stderr", ".json")):
            raise ValueError("duplicate_command_label")
        start = self.clock()
        stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        try:
            result = self.runner(argv, input=stdin, capture_output=True, timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            result = subprocess.CompletedProcess(
                argv, 124, exc.stdout or b"", (exc.stderr or b"") + b"LOCAL_TIMEOUT"
            )
        stem.with_suffix(".stdout").write_bytes(result.stdout)
        stem.with_suffix(".stderr").write_bytes(result.stderr)
        write(
            stem.with_suffix(".json"),
            {
                "argv": argv,
                "start_utc": stamp,
                "elapsed": self.clock() - start,
                "timeout": timeout,
                "returncode": result.returncode,
            },
        )
        return result

    def identity(self, label, timeout=30):
        result = self.run(
            label,
            [
                "gcloud",
                "compute",
                "instances",
                "describe",
                VM,
                *BASE,
                "--format=json(id,status,lastStartTimestamp,lastStopTimestamp,machineType,guestAccelerators)",
            ],
            timeout,
        )
        if result.returncode:
            raise OSError("provider_observation_unavailable")
        return json.loads(result.stdout)

    def ssh(self, label, script, timeout=60, owned=None):
        began = self.clock()
        if owned is not None:
            same_start(self.identity(label + "_before", min(20, timeout)), owned, running=True)
        remaining = timeout - (self.clock() - began)
        if remaining <= 0:
            raise TimeoutError("identity_consumed_deadline")
        (self.commands / (label + ".py.txt")).write_text(script)
        result = self.run(
            label,
            [
                "gcloud",
                "compute",
                "ssh",
                VM,
                *BASE,
                "--tunnel-through-iap",
                "--command",
                "sudo -n python3 -",
            ],
            remaining,
            script.encode(),
        )
        if result.returncode:
            raise OSError("iap_observation_unavailable")
        remaining = timeout - (self.clock() - began)
        if owned is not None:
            if remaining <= 0:
                raise TimeoutError("transport_consumed_deadline")
            same_start(self.identity(label + "_after", min(20, remaining)), owned, running=True)
        return result.stdout

    def stop(self, label, owned):
        current = self.identity(label + "_identity")
        same_start(current, owned)
        if current["status"] != "TERMINATED":
            self.run(
                label + "_stop",
                ["gcloud", "compute", "instances", "stop", VM, *BASE, "--quiet", "--format=json"],
                timeout=120,
            )
        observed = self.identity(label + "_final")
        same_start(observed, owned)
        if observed.get("status") != "TERMINATED":
            raise OSError("termination_unverified")
        return observed


def recover_start(cloud, directory, label):
    """Reconcile a lost start reply under the declared single lifecycle operator assumption."""
    intent = json.loads((Path(directory) / "start_intent.json").read_text())
    prior = intent["before"]
    current = cloud.identity(label)
    if (
        str(current.get("id")) != VM_ID
        or prior.get("status") != "TERMINATED"
        or current.get("lastStartTimestamp") == prior.get("lastStartTimestamp")
        or not current.get("lastStartTimestamp")
    ):
        raise ValueError("unreconciled_start")
    return current


def watch(directory):
    directory = Path(directory)
    budget = json.loads((directory / "budget.json").read_text())
    while time.monotonic() < budget["deadline_monotonic"] - 180:
        if (directory / "closure.json").exists():
            return 0
        time.sleep(1)
    ready = directory / "owned.json"
    if not ready.exists():
        try:
            reconciled = recover_start(Cloud(directory), directory, "watchdog_reconcile_start")
            write(directory / "watchdog_reconciled_start.json", reconciled)
        except Exception as exc:
            write(directory / "watchdog_result.json", {"status": "unknown", "reason": repr(exc)})
            return 1
    else:
        reconciled = json.loads(ready.read_text())
    cloud = Cloud(directory)
    try:
        final = cloud.stop("watchdog", reconciled)
        write(directory / "watchdog_result.json", {"status": "supported", "final": final})
        return 0
    except Exception as exc:
        write(directory / "watchdog_result.json", {"status": "unknown", "reason": repr(exc)})
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    raise SystemExit(watch(args.directory))
