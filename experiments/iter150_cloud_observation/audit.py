"""Reconstruct live qualification from retained outputs, preserving harness failure status."""

from copy import deepcopy
import json
from pathlib import Path

from experiments.iter149_observation_recovery.replay import check
from .check import verify


def load(directory):
    directory = Path(directory)
    names = [
        "owned.json",
        "host_binding.json",
        "budget.json",
        "closure.json",
        "result.json",
        "postflight.json",
        "postflight.stdout",
        "fixtures.json",
        "native_0_trace.json",
        "native_1_trace.json",
        "native_2_trace.json",
        "permanent_disconnect_trace.json",
        "completion_reconnect_trace.json",
    ]
    return {name: json.loads((directory / name).read_bytes()) for name in names}


def audit(records, native_root):
    native_root = Path(native_root).resolve()
    owned = records["owned.json"]
    final = records["closure.json"]["instance"]
    host = records["host_binding.json"]
    budget = records["budget.json"]
    result = records["result.json"]
    if (
        owned["id"] != "3834622546652649531"
        or final["id"] != owned["id"]
        or final["lastStartTimestamp"] != owned["lastStartTimestamp"]
        or final["status"] != "TERMINATED"
        or not final.get("lastStopTimestamp")
    ):
        raise ValueError("owned_termination")
    if (
        budget["deadline_monotonic"] - budget["started_monotonic"] != 900
        or not 0 < result["elapsed_seconds"] <= 900
        or result["watchdog_exit"] != 0
        or result["termination_verified"] is not True
    ):
        raise ValueError("resource_closure")
    post = records["postflight.stdout"]
    if records["postflight.json"]["returncode"] != 0 or post != {
        "status": "supported",
        "native_pair_inventories_unchanged": 2,
        "active_containers": 0,
        "active_gpu_processes": 0,
    }:
        raise ValueError("postflight")
    totals = []
    for pair in (0, 1, 2):
        trace = records[f"native_{pair}_trace.json"]
        check(trace)
        binding = trace["binding"]
        if (
            binding["vm_id"] != owned["id"]
            or binding["vm_start"] != owned["lastStartTimestamp"]
            or binding["host_boot"] != host["boot"]
            or binding["host_deadline_id"] != host["timer_unit"]
        ):
            raise ValueError("native_cloud_binding")
        if pair < 2:
            if not trace["worker_complete"]:
                raise ValueError("native_incomplete")
            blobs = {k: bytes.fromhex(v) for k, v in trace["events"][-1]["blobs_hex"].items()}
            totals.append(verify(native_root / f"pair_{pair:03d}", blobs, binding))
        elif trace["worker_complete"] or trace["events"][-1]["state"] != "partial_evidence":
            raise ValueError("partial_promoted")
    first = records["native_0_trace.json"]["events"]
    if len(first) != 2 or [e["state"] for e in first] != [
        "observation_unavailable",
        "worker_complete",
    ]:
        raise ValueError("recovery_missing")
    permanent = records["permanent_disconnect_trace.json"]
    check(permanent)
    if permanent["reason"] != "unavailable_limit" or len(permanent["events"]) != 4:
        raise ValueError("permanent_loss_bound")
    recovered = records["completion_reconnect_trace.json"]
    check(recovered)
    if not recovered["worker_complete"]:
        raise ValueError("completion_recovery_missing")
    fixtures = records["fixtures.json"]
    for name in ("complete", "disconnected"):
        row = fixtures[name]
        closure = row["closure"]
        if (
            row["duplicate_returncode"] != 1
            or closure["status"] != "terminated"
            or closure["partial_raw_preserved"] is not True
            or not 0 < closure["elapsed"] < 10
        ):
            raise ValueError("fixture_closure")
        launch = json.loads(bytes.fromhex(row["files"]["launch.json"]))
        if launch["initializations"] != 1 or not bytes.fromhex(row["files"]["raw.json"]):
            raise ValueError("fixture_initialization")
    if (
        fixtures["complete"]["closure"]["returncode"] != 0
        or fixtures["disconnected"]["closure"]["returncode"] != -9
        or fixtures["disconnected"]["closure"]["deadline_fired"] is not True
    ):
        raise ValueError("host_deadline")
    return {
        "qualification_status": "supported",
        "execution_status": result["status"],
        "execution_error": result.get("error"),
        "scope": "one VM start; native read adapter and CPU-only synthetic fault qualification",
        "native_pairs_complete": 2,
        "native_pairs_partial": 1,
        "replayed_traces": 5,
        "native_inventory_checks": totals,
        "termination_verified": True,
        "elapsed_seconds": result["elapsed_seconds"],
        "conservative_compute_usd": result["elapsed_seconds"] * 3 / 3600,
        "cloud_rerun_needed_for_report_filename_change": False,
        "corrected_harness_cloud_execution": "unobserved",
        "new_scientific_outcomes": 0,
    }


def known_bads(records, native_root):
    rejected = {}
    for name in (
        "vm_start",
        "termination",
        "budget",
        "postflight",
        "native_binding",
        "partial",
        "deadline",
        "duplicate_initialization",
        "completion",
    ):
        bad = deepcopy(records)
        if name == "vm_start":
            bad["closure.json"]["instance"]["lastStartTimestamp"] = "replacement"
        elif name == "termination":
            bad["closure.json"]["instance"]["status"] = "RUNNING"
        elif name == "budget":
            bad["result.json"]["elapsed_seconds"] = 901
        elif name == "postflight":
            bad["postflight.stdout"]["active_gpu_processes"] = 1
        elif name == "native_binding":
            bad["host_binding.json"]["boot"] = "different-boot"
        elif name == "partial":
            bad["native_2_trace.json"]["worker_complete"] = True
        elif name == "deadline":
            bad["fixtures.json"]["disconnected"]["closure"]["deadline_fired"] = False
        elif name == "duplicate_initialization":
            bad["fixtures.json"]["complete"]["duplicate_returncode"] = 0
        elif name == "completion":
            bad["completion_reconnect_trace.json"]["worker_complete"] = False
        try:
            audit(bad, native_root)
        except ValueError as exc:
            rejected[name] = str(exc)
        else:
            raise ValueError("accepted_bad:" + name)
    return rejected


if __name__ == "__main__":
    import argparse
    import hashlib
    import subprocess

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("native_root", type=Path)
    args = parser.parse_args()
    directory = args.directory.resolve()
    repository = Path(__file__).resolve().parents[2]
    raw_commit = "7528899"
    relative = directory.relative_to(repository).as_posix()
    listing = subprocess.check_output(
        ["git", "ls-tree", "-r", raw_commit, "--", relative], cwd=repository, text=True
    ).splitlines()
    if not listing:
        raise ValueError("raw_commit_empty")
    for line in listing:
        metadata, name = line.split("\t", 1)
        data = (repository / name).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        if actual != metadata.split()[2]:
            raise ValueError("committed_raw_changed:" + name)
    records = load(directory)
    report = audit(records, args.native_root)
    report.update(
        raw_commit=raw_commit,
        committed_raw_files_verified=len(listing),
        known_bads_rejected=known_bads(records, args.native_root),
    )
    print(json.dumps(report, indent=2))
