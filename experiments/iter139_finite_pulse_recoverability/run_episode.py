"""Execute one registered fresh finite-pulse episode on the inspected host; never retry an episode."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import time


CONTROL = Path("/datasets/nuscenes-full/hugsim/iter139_control_20261009")
OUTPUT = Path("/datasets/nuscenes-full/hugsim/outputs/iter139-20261009")
HUGSIM = Path("/opt/sentinel-stack/HUGSIM")
ARMS = (
    "reference_a",
    "reference_b",
    "pulse_0_1",
    "pulse_0_2",
    "pulse_2_1",
    "pulse_2_2",
    "pulse_4_1",
    "pulse_4_2",
)
CONTAINER = "sentinel-i139-client"


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def check_files(files):
    for name, expected in files.items():
        path = Path(name)
        if not path.is_file() or path.is_symlink() or digest(path) != expected:
            raise ValueError(f"runtime file mismatch: {name}")


def check_budget(free_gib, remaining_seconds, output_exists):
    if free_gib < 100 or free_gib - 8 < 25:
        raise ValueError("storage budget")
    if remaining_seconds < 1230:
        raise ValueError("insufficient session runtime for bounded episode and cleanup")
    if output_exists:
        raise ValueError("episode already attempted; no overwrite or retry")


def command(argv):
    result = subprocess.run(argv, capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise RuntimeError(f"{argv[0]} failed: {result.stderr[:2000]}")
    return result.stdout.strip()


def check_runtime_identity(actual_image, expected_image, containers, gpu_processes):
    if actual_image != expected_image:
        raise ValueError("client image identity")
    if containers:
        raise ValueError("another container is running")
    if gpu_processes:
        raise ValueError("GPU process already running")


def check_predecessor(report, arm, directory):
    if report.get("status") != "validated":
        raise ValueError("predecessor not validated")
    if arm == "reference_b" and report.get("verdict") != "REPLAY_MATCHED":
        raise ValueError("reference pair gate")
    if arm.startswith("pulse_") and report.get("prefix") != "matched":
        raise ValueError("predecessor prefix")
    summary = report["reference"] if arm == "reference_a" else report["candidate"]
    expected = {"iter139_trace.jsonl", "controller139.jsonl", "sentinel_iter48_decisions.jsonl"}
    if set(summary["files"]) != expected:
        raise ValueError("predecessor file inventory")
    for name, expected in summary["files"].items():
        p = directory / "scene-0411_hard_00" / name
        if not p.is_file() or p.is_symlink() or digest(p) != expected:
            raise ValueError("predecessor evidence changed")


def predecessors(arm, root):
    for prior in ARMS[: ARMS.index(arm)]:
        previous = root / prior
        receipt = previous / "episode.json"
        if not receipt.is_file() or json.loads(receipt.read_text()).get("returncode") != 0:
            raise ValueError("previous episode incomplete or failed")
        report_path = CONTROL / "validations" / (prior + ".json")
        if report_path.is_symlink() or not report_path.is_file():
            raise ValueError("missing predecessor validation")
        check_predecessor(json.loads(report_path.read_text()), prior, previous)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("arm", choices=ARMS)
    parser.add_argument("--manifest-sha256", required=True)
    args = parser.parse_args()
    if socket.gethostname().split(".")[0] != "sentinel-gpu":
        raise ValueError("host mismatch")
    manifest_path = CONTROL / "runtime_manifest.json"
    if digest(manifest_path) != args.manifest_sha256:
        raise ValueError("manifest identity")
    manifest = json.loads(manifest_path.read_text())
    with (CONTROL / "episode.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        check_files(manifest["files"])
        check_runtime_identity(
            command(["docker", "image", "inspect", manifest["image_id"], "--format", "{{.Id}}"]),
            manifest["image_id"],
            command(["docker", "ps", "-q"]),
            command(["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"]),
        )
        run = OUTPUT / args.arm
        check_budget(
            shutil.disk_usage(OUTPUT.parent).free / 2**30,
            manifest["deadline_epoch"] - time.time(),
            run.exists(),
        )
        predecessors(args.arm, OUTPUT)
        run.mkdir(parents=True, exist_ok=False)
        environment = os.environ.copy()
        environment.update(
            PYTHONPATH=f"{CONTROL}:{CONTROL}/packet:{HUGSIM}",
            OPENBLAS_NUM_THREADS="1",
            OMP_NUM_THREADS="1",
            MKL_NUM_THREADS="1",
            SENTINEL_ENABLED="1",
            SENTINEL_I139_ARM=args.arm,
            SENTINEL_I139_IDENTITY=str(CONTROL / "identity.json"),
        )
        # Gym loads this module lazily. Importing closed_loop alone misses this boundary.
        probe = subprocess.run(
            [
                str(HUGSIM / ".pixi/envs/default/bin/python"),
                "-c",
                "from hugsim_env.envs.hug_sim import HUGSimEnv; import closed_loop",
            ],
            cwd=HUGSIM,
            env=environment,
            capture_output=True,
            text=True,
            timeout=90,
        )
        (run / "environment_import.json").write_text(
            json.dumps(
                dict(returncode=probe.returncode, stdout=probe.stdout, stderr=probe.stderr),
                indent=2,
            )
            + "\n"
        )
        if probe.returncode:
            raise RuntimeError("environment class import failed before episode launch")
        check_budget(
            shutil.disk_usage(OUTPUT.parent).free / 2**30,
            manifest["deadline_epoch"] - time.time(),
            False,
        )
        argv = [
            str(HUGSIM / ".pixi/envs/default/bin/python"),
            "-u",
            str(CONTROL / "iter139_closed_loop.py"),
            "--scenario_path",
            manifest["scenario"],
            "--base_path",
            str(CONTROL / "nuscenes_base.yaml"),
            "--camera_path",
            "configs/sim/nuscenes_camera.yaml",
            "--kinematic_path",
            "configs/sim/kinematic.yaml",
            "--ad",
            "uniad",
            "--ad_cuda",
            "0",
            "--i139-output-base",
            str(run),
        ]
        receipt = dict(
            arm=args.arm,
            manifest_sha256=args.manifest_sha256,
            argv=argv,
            started_at_utc=datetime.now(timezone.utc).isoformat(),
            status="running",
            timeout_seconds=1200,
        )
        (run / "started.json").write_text(json.dumps(receipt, indent=2) + "\n")
        began = time.monotonic()
        with (run / "driver.log").open("xb") as log:
            process = subprocess.Popen(
                argv,
                cwd=HUGSIM,
                env=environment,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            receipt["driver_pid"] = process.pid
            try:
                receipt["returncode"] = process.wait(timeout=1200)
                receipt["status"] = "process_completed"
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                receipt.update(returncode=124, status="timeout")
            finally:
                # Never remove a historical or unrelated container.
                inspect = subprocess.run(
                    [
                        "docker",
                        "inspect",
                        CONTAINER,
                        "--format",
                        '{{index .Config.Labels "sentinel.iter139.arm"}}',
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if inspect.returncode == 0:
                    if inspect.stdout.strip() != args.arm:
                        receipt["cleanup"] = "ownership_mismatch_no_removal"
                    else:
                        result = subprocess.run(
                            ["docker", "rm", "-f", CONTAINER],
                            capture_output=True,
                            text=True,
                            timeout=30,
                        )
                        receipt["cleanup"] = dict(
                            returncode=result.returncode, stdout=result.stdout, stderr=result.stderr
                        )
                else:
                    receipt["cleanup"] = "container_absent"
        receipt["elapsed_seconds"] = time.monotonic() - began
        receipt["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        receipt["artifacts"] = {
            str(p.relative_to(run)): {"sha256": digest(p), "bytes": p.stat().st_size}
            for p in sorted(run.rglob("*"))
            if p.is_file() and not p.is_symlink()
        }
        (run / "episode.json").write_text(json.dumps(receipt, indent=2) + "\n")
        print(json.dumps(receipt, indent=2))
        return receipt["returncode"]


if __name__ == "__main__":
    raise SystemExit(main())
