"""Retain actual local watchdog, crash and completion evidence without a cloud connection."""

import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

from .local_host import observe
from .recovery import Limits, closure, digest, encode, reconcile
from .replay import check


def qualify(output):
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    for mode in ("complete", "crash", "disconnected"):
        owned = output / mode
        argv = [
            sys.executable,
            "-m",
            "experiments.iter149_observation_recovery.local_host",
            "host",
            str(owned),
            "10" if mode == "disconnected" else "0.25",
            "--budget",
            "1.5",
        ]
        if mode == "crash":
            argv.append("--crash")
        start = time.monotonic()
        process = subprocess.run(argv, capture_output=True, timeout=8)
        (output / (mode + ".stdout")).write_bytes(process.stdout)
        (output / (mode + ".stderr")).write_bytes(process.stderr)
        if process.returncode:
            raise ValueError("local_host_failure")
        binding = json.loads((owned / "binding.json").read_bytes())
        result = json.loads((owned / "closure.json").read_bytes())
        marker_before = (owned / "initialized.json").read_bytes()
        raw_before = (owned / "raw.json").read_bytes()
        duplicate = subprocess.run(argv, capture_output=True, timeout=5)
        (output / (mode + "_duplicate.stderr")).write_bytes(duplicate.stderr)
        if (
            duplicate.returncode == 0
            or (owned / "initialized.json").read_bytes() != marker_before
            or (owned / "raw.json").read_bytes() != raw_before
        ):
            raise ValueError("duplicate_initialization")
        if closure(binding, result) != "verified" or not raw_before:
            raise ValueError("closure_or_partial_raw")
        if result["elapsed"] >= 5 or time.monotonic() - start >= 10:
            raise ValueError("resource_bound")
        if mode == "disconnected":
            if not result["deadline_fired"] or result["returncode"] != -9:
                raise ValueError("watchdog_not_effective")
            # No observer ran while the worker was active: expiry is host-local.
            replay = None
        else:
            trace = reconcile(
                binding,
                Limits(deadline=time.monotonic() + 2),
                "reattach",
                lambda request, timeout: observe(owned, request, timeout),
                time.monotonic,
                time.sleep,
            )
            (output / (mode + "_trace.json")).write_bytes(encode(trace) + b"\n")
            replay = check(trace)
            expected = "worker_failed" if mode == "crash" else "worker_complete"
            if trace["reason"] != expected:
                raise ValueError("reconciliation")
        rows.append(
            {
                "case": mode,
                "closure": result,
                "replay": replay,
                "initializations": 1,
                "duplicate_returncode": duplicate.returncode,
                "raw_sha256": digest(raw_before),
                "raw_bytes": len(raw_before),
            }
        )
    report = {
        "status": "supported",
        "scope": "actual_local_subprocesses",
        "python": sys.version,
        "rows": rows,
        "cloud_qualified": False,
    }
    (output / "qualification.json").write_bytes(encode(report) + b"\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = qualify(args.output)
    print(json.dumps({"status": result["status"], "cases": len(result["rows"])}))
