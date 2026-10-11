"""Execute one fixed pair after source, host, resource and previous-raw clearance."""

import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import time
from experiments.iter145_constrained_execution.gpu_batch import check_files, invoke, capacity
from .records import read, record
from .admission import claim, remaining, validate_plan
from .ownership import capture, check_service
from experiments.iter150_cloud_observation.remote import context
from experiments.iter147_full_horizon_execution.protocol import identity
from experiments.iter147_full_horizon_execution.resources import guard
from experiments.iter147_full_horizon_execution.gpu import HUGSIM, cleanup_client


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--control", type=Path, required=True)
    p.add_argument("--manifest-sha256", required=True)
    p.add_argument("--clearance-sha256", required=True)
    p.add_argument("--pair", type=int, required=True)
    p.add_argument("--unit", required=True)
    a = p.parse_args()
    control = a.control
    manifest = read(control / "execution_manifest.json")
    document = validate_plan(read(control / "plan.json"))
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
    envelope = read(control / f"block_{permit['block']:03d}_envelope.json")
    if a.unit != envelope["pair_units"][str(a.pair)] or permit["envelope_sha256"] != identity(
        envelope
    ):
        raise ValueError("envelope_binding")
    environment = context(envelope["binding"], envelope["timer_unit"], envelope["timer_readback"])
    if environment != envelope["binding"]:
        raise ValueError("host_binding")
    remaining(envelope["deadline_monotonic"], time.monotonic())
    selected = claim(
        control / "packet",
        control,
        document,
        a.pair,
        permit["history"],
        permit["qualification_sha256"],
        permit["block"],
        a.manifest_sha256,
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
        service = check_service(a.unit)
        if service["ActiveState"] != "active" or int(service["MainPID"]) != os.getpid():
            raise ValueError("pair_service_owner")
        capture(control, a.pair, environment, service)
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
                "experiments.iter154_full_scene_maneuver.worker",
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
