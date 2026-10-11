"""Execute one fixed pair after source, host, resource and previous-raw clearance."""

import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import time
from experiments.iter145_constrained_execution.gpu_batch import check_files, invoke, capacity
from experiments.iter147_full_horizon_execution.coordinator import read, record
from .admission import claim, remaining_budget
from experiments.iter147_full_horizon_execution.protocol import identity
from experiments.iter147_full_horizon_execution.resources import guard
from experiments.iter147_full_horizon_execution.gpu import HUGSIM, cleanup_client


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--control", type=Path, required=True)
    p.add_argument("--manifest-sha256", required=True)
    p.add_argument("--clearance-sha256", required=True)
    p.add_argument("--pair", type=int, required=True)
    a = p.parse_args()
    control = a.control
    manifest = read(control / "execution_manifest.json")
    document = read(control / "plan.json")
    permit_path = control / f"pair_{a.pair:03d}_clearance.json"
    permit = read(permit_path)
    if (
        hashlib.sha256((control / "execution_manifest.json").read_bytes()).hexdigest()
        != a.manifest_sha256
        or hashlib.sha256(permit_path.read_bytes()).hexdigest() != a.clearance_sha256
    ):
        raise ValueError("launch digest")
    if (
        permit["status"] != "supported"
        or permit["pair"] != a.pair
        or permit["plan_sha256"] != identity(document)
        or permit["manifest_sha256"] != a.manifest_sha256
    ):
        raise ValueError("launch binding")
    remaining_budget(permit["remaining_seconds"])
    selected = claim(
        control / "packet",
        control,
        document,
        a.pair,
        permit["history"],
        permit["qualification_sha256"],
        permit["block"],
    )
    report = dict(
        status="running",
        pair=a.pair,
        cases=[],
        plan_sha256=identity(document),
        live_study_admitted=True,
    )
    began = time.monotonic()
    try:
        check_files(manifest)
        for slot in selected:
            for argv in (
                ["docker", "ps", "-q"],
                ["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"],
            ):
                q = subprocess.run(argv, capture_output=True, text=True, timeout=30)
                if q.returncode or q.stdout.strip():
                    raise ValueError("occupied_host")
            q = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if q.returncode:
                raise ValueError("gpu_memory_unobserved")
            mem = dict(
                line.split(":", 1) for line in Path("/proc/meminfo").read_text().splitlines()
            )
            capacity(float(q.stdout.strip()), float(mem["MemAvailable"].split()[0]) / 1024**2)
            output = control / "runs" / slot["id"]
            output.mkdir(parents=True, exist_ok=False)
            env = os.environ.copy()
            env.update(
                PYTHONPATH=str(control / "packet") + ":" + str(HUGSIM),
                OPENBLAS_NUM_THREADS="1",
                OMP_NUM_THREADS="1",
                MKL_NUM_THREADS="1",
            )
            argv = [
                str(HUGSIM / ".pixi/envs/default/bin/python"),
                "-u",
                "-m",
                "experiments.iter147_full_horizon_execution.gpu",
                "--control",
                str(control),
                "--slot",
                str(slot["index"]),
            ]
            result = invoke(
                argv,
                cwd=HUGSIM,
                environment=env,
                log=output / "parent.log",
                timeout=document["child_seconds"],
                guard=lambda: guard(control, output, len(document["slots"])),
            )
            result.update(slot=slot, cleanup=cleanup_client(slot["id"]))
            report["cases"].append(result)
            if result["returncode"] != 0:
                raise RuntimeError("study_case_failed")
        report["status"] = "completed"
    except Exception as exc:
        report.update(status="failed", error=f"{type(exc).__name__}:{exc}")
    finally:
        report["elapsed_seconds"] = time.monotonic() - began
        record(control / f"pair_{a.pair:03d}_result.json", report)
    return 0 if report["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
