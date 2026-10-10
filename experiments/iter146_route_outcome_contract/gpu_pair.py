"""One fixed qualification arm pair; later arms require retained prior replay clearance."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

from experiments.iter145_constrained_execution.gpu_batch import check_files, invoke, capacity
from .gpu import HUGSIM, CASES, cleanup_client
from .resources import output_guard
from .runner import ARMS


def validate_clearance(raw, clearance, arm, manifest_sha, clearance_sha):
    if (
        arm not in ARMS
        or hashlib.sha256(raw).hexdigest() != manifest_sha
        or hashlib.sha256(clearance).hexdigest() != clearance_sha
    ):
        raise ValueError("manifest_or_clearance_identity")
    permit = json.loads(clearance)
    if (
        permit["arm"] != arm
        or permit["manifest_sha256"] != manifest_sha
        or permit["status"] != "supported"
    ):
        raise ValueError("clearance_binding")
    index = ARMS.index(arm)
    if index:

        def digest(value, size):
            return (
                isinstance(value, str)
                and len(value) == size
                and all(c in "0123456789abcdef" for c in value)
            )

        if (
            permit.get("prior_arm") != ARMS[index - 1]
            or not digest(permit.get("raw_commit"), 40)
            or not digest(permit.get("replay_sha256"), 64)
        ):
            raise ValueError("prior_arm_clearance")
    return permit


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--control", type=Path, required=True)
    p.add_argument("--manifest-sha256", required=True)
    p.add_argument("--arm", choices=ARMS, required=True)
    p.add_argument("--clearance-sha256", required=True)
    a = p.parse_args()
    control = a.control
    raw = (control / "execution_manifest.json").read_bytes()
    clearance = (control / (a.arm + "_clearance.json")).read_bytes()
    validate_clearance(raw, clearance, a.arm, a.manifest_sha256, a.clearance_sha256)
    with (control / (a.arm + "_started.json")).open("x") as f:
        json.dump(
            dict(arm=a.arm, manifest_sha256=a.manifest_sha256, clearance_sha256=a.clearance_sha256),
            f,
        )
    report = dict(status="running", arm=a.arm, cases=[], live_study_admitted=False)
    began = time.monotonic()
    try:
        check_files(json.loads(raw))
        for replica in (1, 2):
            episode = CASES[0].removesuffix(".yaml") + "__" + a.arm + "__" + str(replica)
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
            env = os.environ.copy()
            env.update(
                PYTHONPATH=str(control / "packet") + ":" + str(HUGSIM),
                OPENBLAS_NUM_THREADS="1",
                OMP_NUM_THREADS="1",
                MKL_NUM_THREADS="1",
            )
            output = control / "runs" / episode

            def guard():
                if output.exists():
                    output_guard(output)

            argv = [
                str(HUGSIM / ".pixi/envs/default/bin/python"),
                "-u",
                "-m",
                "experiments.iter146_route_outcome_contract.gpu",
                "--control",
                str(control),
                "--case",
                CASES[0],
                "--arm",
                a.arm,
                "--replica",
                str(replica),
            ]
            result = invoke(
                argv,
                cwd=HUGSIM,
                environment=env,
                log=control / (episode + ".log"),
                timeout=600,
                guard=guard,
            )
            result.update(episode=episode, cleanup=cleanup_client(episode))
            report["cases"].append(result)
            if result["returncode"] != 0:
                raise RuntimeError("qualification_case_failed")
        report["status"] = "completed"
    except Exception as exc:
        report.update(status="failed", error=f"{type(exc).__name__}:{exc}")
    finally:
        report["elapsed_seconds"] = time.monotonic() - began
        (control / (a.arm + "_pair.json")).write_text(json.dumps(report, indent=2) + "\n")
    return 0 if report["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
