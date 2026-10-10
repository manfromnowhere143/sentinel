"""One finite four-case batch with external process deadlines and ownership checks."""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import shutil
import socket
import subprocess
import time

from .gpu import CASES, HUGSIM, cleanup_client
from .resources import file_identity, actor_identity


def output_guard(control):
    size = sum(p.stat().st_size for p in (control / "runs").rglob("*") if p.is_file())
    if size >= 7 * 1024**3 or shutil.disk_usage(control).free < 25 * 1024**3:
        raise ValueError("output_or_storage_limit")


def invoke(argv, *, cwd, environment, log, timeout, guard=None):
    with Path(log).open("xb") as output:
        process = subprocess.Popen(
            argv,
            cwd=cwd,
            env=environment,
            stdout=output,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        deadline = time.monotonic() + timeout
        while True:
            try:
                if guard is not None:
                    guard()
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise subprocess.TimeoutExpired(argv, timeout)
                return dict(
                    returncode=process.wait(timeout=min(1, remaining)), deadline_exceeded=False
                )
            except subprocess.TimeoutExpired:
                if time.monotonic() < deadline:
                    continue
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                return dict(returncode=124, deadline_exceeded=True)
            except ValueError as exc:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                return dict(returncode=125, deadline_exceeded=False, stop_reason=str(exc))


def capacity(free_mib, available_gib):
    if (
        type(free_mib) not in (int, float)
        or type(available_gib) not in (int, float)
        or not math.isfinite(free_mib)
        or not math.isfinite(available_gib)
        or not (free_mib >= 20000 and available_gib >= 24)
    ):
        raise ValueError("gpu_or_host_memory_capacity")
    return True


def check_files(manifest):
    for name, expected in manifest["files"].items():
        if file_identity(Path(name), allow_empty=expected["bytes"] == 0) != expected:
            raise ValueError("source_or_asset_changed:" + name)
    root = Path("/datasets/nuscenes-full/hugsim/3DRealCar")
    for logical, record in manifest["actor_aliases"].items():
        value = actor_identity(
            root,
            Path(logical).parent.relative_to(root),
            Path(logical).name,
            manifest["actor_files"],
        )
        if value["sha256"] != record["sha256"] or value["physical_path"] != record["physical_path"]:
            raise ValueError("actor_alias_changed:" + logical)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--control", type=Path, required=True)
    p.add_argument("--manifest-sha256", required=True)
    a = p.parse_args()
    control = a.control
    raw = (control / "execution_manifest.json").read_bytes()
    if (
        hashlib.sha256(raw).hexdigest() != a.manifest_sha256
        or socket.gethostname().split(".")[0] != "sentinel-gpu"
    ):
        raise ValueError("execution_manifest_or_host")
    manifest = json.loads(raw)
    if manifest["cases"] != list(CASES):
        raise ValueError("batch_population")
    # The exclusive marker prevents silent reruns after a partial or failed invocation.
    with (control / "batch_started.json").open("x") as f:
        json.dump(dict(status="running", cases=CASES, manifest_sha256=a.manifest_sha256), f)
    receipt = dict(status="running", cases=[], live_study_admitted=False)
    begun = time.monotonic()
    environment = os.environ.copy()
    environment.update(
        PYTHONPATH=str(control / "packet") + ":" + str(HUGSIM),
        OPENBLAS_NUM_THREADS="1",
        OMP_NUM_THREADS="1",
        MKL_NUM_THREADS="1",
    )
    py = str(HUGSIM / ".pixi/envs/default/bin/python")
    try:
        check_files(manifest)
        for case in CASES:
            if time.monotonic() - begun >= 3600:
                raise TimeoutError("batch_remaining_deadline")
            for argv in (
                ["docker", "ps", "-q"],
                ["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"],
            ):
                q = subprocess.run(argv, capture_output=True, text=True, timeout=30)
                if q.returncode or q.stdout.strip():
                    raise ValueError("host_occupied")
            q = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if q.returncode:
                raise ValueError("gpu_capacity_unobserved")
            mem = dict(
                line.split(":", 1) for line in Path("/proc/meminfo").read_text().splitlines()
            )
            capacity(float(q.stdout.strip()), float(mem["MemAvailable"].split()[0]) / 1024**2)
            episode = case.removesuffix(".yaml")
            argv = [
                py,
                "-u",
                "-m",
                "experiments.iter145_constrained_execution.gpu",
                "--control",
                str(control),
                "--case",
                case,
            ]
            start = time.monotonic()
            result = invoke(
                argv,
                cwd=HUGSIM,
                environment=environment,
                log=control / (episode + ".log"),
                timeout=1200,
                guard=lambda: output_guard(control),
            )
            result.update(case=case, elapsed_seconds=time.monotonic() - start)
            result["cleanup"] = cleanup_client(episode)
            receipt["cases"].append(result)
            (control / (episode + "_process.json")).write_text(json.dumps(result, indent=2) + "\n")
            if result["returncode"]:
                raise RuntimeError("qualification_case_failed:" + case)
        receipt["status"] = "completed"
    except Exception as e:
        receipt.update(status="failed", reason=f"{type(e).__name__}:{e}")
    finally:
        receipt["elapsed_seconds"] = time.monotonic() - begun
        (control / "batch.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return 0 if receipt["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
