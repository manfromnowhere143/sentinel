#!/usr/bin/env python3
"""Run the iter28 bounded inventory on sentinel-gpu and copy proof artifacts back."""

from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT = "sunlit-unison-487018-b0"
ZONE = "us-west1-a"
INSTANCE = "sentinel-gpu"
REMOTE_WORKDIR = "/datasets/nuscenes-full/.iter28_tmp/iter28-inventory-work"
REMOTE_RESULT_TGZ = "/datasets/nuscenes-full/.iter28_tmp/iter28-inventory-proof.tgz"
LOCAL_OUT_DIR = Path("experiments/iter28_nuscenes_trainval_staging/proof-inventory")

REQUIRED_FILES = (
    "experiments/iter28_nuscenes_trainval_staging/bounded_inventory.py",
    "experiments/iter25_staged_data_inventory/inventory_roots.py",
    "experiments/iter22_causal_planner_interpretability/official_train_scenes.txt",
    "experiments/iter22_causal_planner_interpretability/split_manifest.json",
    "experiments/iter22_causal_planner_interpretability/proof-extract/sentinel_e22_stage1_gt.jsonl.gz",
    "experiments/iter23_s0_hardened_causal_localization/availability_manifest.json",
    "experiments/iter23_s0_hardened_causal_localization/proof-full-extract/sentinel_e23_stage1_gt.jsonl.gz",
    "experiments/iter24_risk_support_atlas/availability_manifest.json",
    "experiments/iter24_risk_support_atlas/availability_manifest.exclusions.txt",
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run_command(cmd: list[str], *, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=timeout)


def gcloud_base(args: argparse.Namespace) -> list[str]:
    return ["gcloud", "compute"]


def remote_ssh(args: argparse.Namespace, command: str) -> subprocess.CompletedProcess[str]:
    return run_command(
        [
            *gcloud_base(args),
            "ssh",
            args.instance,
            "--zone",
            args.zone,
            "--project",
            args.project,
            "--tunnel-through-iap",
            "--quiet",
            "--command",
            command,
        ],
        timeout=None,
    )


def remote_scp_to(args: argparse.Namespace, local_path: Path, remote_path: str) -> None:
    run_command(
        [
            *gcloud_base(args),
            "scp",
            str(local_path),
            f"{args.instance}:{remote_path}",
            "--zone",
            args.zone,
            "--project",
            args.project,
            "--tunnel-through-iap",
            "--quiet",
        ],
        timeout=None,
    )


def remote_scp_from(args: argparse.Namespace, remote_path: str, local_path: Path) -> None:
    run_command(
        [
            *gcloud_base(args),
            "scp",
            f"{args.instance}:{remote_path}",
            str(local_path),
            "--zone",
            args.zone,
            "--project",
            args.project,
            "--tunnel-through-iap",
            "--quiet",
        ],
        timeout=None,
    )


def required_file_manifest(paths: tuple[str, ...] = REQUIRED_FILES) -> list[dict[str, Any]]:
    manifest = []
    for rel in paths:
        path = Path(rel)
        if not path.is_file():
            raise SystemExit(f"missing required remote-inventory input: {rel}")
        manifest.append(
            {
                "path": rel,
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
        )
    return manifest


def build_bundle(bundle_path: Path, paths: tuple[str, ...] = REQUIRED_FILES) -> None:
    with tarfile.open(bundle_path, "w:gz") as tf:
        for rel in paths:
            tf.add(rel, arcname=rel)


def safe_extract_result(result_tgz: Path, out_dir: Path) -> None:
    tmp_parent = Path(tempfile.mkdtemp(prefix="iter28-inventory-proof-"))
    try:
        with tarfile.open(result_tgz, "r:gz") as tf:
            for member in tf:
                name = Path(member.name)
                if member.name.startswith("/") or ".." in name.parts:
                    raise SystemExit(f"unsafe inventory result member: {member.name}")
            tf.extractall(tmp_parent)
        extracted = tmp_parent / "proof-inventory"
        if not extracted.is_dir():
            extracted = (
                tmp_parent
                / "experiments"
                / "iter28_nuscenes_trainval_staging"
                / "proof-inventory"
            )
        if not extracted.is_dir():
            raise SystemExit("remote inventory result missing proof-inventory directory")
        if out_dir.exists():
            shutil.rmtree(out_dir)
        shutil.move(str(extracted), out_dir)
    finally:
        shutil.rmtree(tmp_parent, ignore_errors=True)


def write_text(path: Path, text: str) -> None:
    path.write_text(text if text.endswith("\n") else text + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=PROJECT)
    parser.add_argument("--zone", default=ZONE)
    parser.add_argument("--instance", default=INSTANCE)
    parser.add_argument("--remote-workdir", default=REMOTE_WORKDIR)
    parser.add_argument("--remote-result-tgz", default=REMOTE_RESULT_TGZ)
    parser.add_argument("--out-dir", type=Path, default=LOCAL_OUT_DIR)
    args = parser.parse_args()

    inputs = required_file_manifest()
    with tempfile.TemporaryDirectory(prefix="iter28-remote-inventory-") as tmp:
        bundle_path = Path(tmp) / "iter28-inventory-inputs.tgz"
        result_path = Path(tmp) / "iter28-inventory-proof.tgz"
        build_bundle(bundle_path)

        q_workdir = shlex.quote(args.remote_workdir)
        q_result = shlex.quote(args.remote_result_tgz)
        remote_ssh(
            args,
            (
                "set -euo pipefail; "
                f"rm -rf {q_workdir} {q_result}; "
                f"mkdir -p {q_workdir}"
            ),
        )
        remote_scp_to(args, bundle_path, f"{args.remote_workdir}/inputs.tgz")
        remote_cmd = (
            "set -euo pipefail; "
            f"cd {q_workdir}; "
            "tar -xzf inputs.tgz; "
            "python3 experiments/iter28_nuscenes_trainval_staging/bounded_inventory.py; "
            "tar -czf proof-inventory.tgz "
            "experiments/iter28_nuscenes_trainval_staging/proof-inventory; "
            f"mv proof-inventory.tgz {q_result}"
        )
        result = remote_ssh(args, remote_cmd)
        remote_scp_from(args, args.remote_result_tgz, result_path)
        safe_extract_result(result_path, args.out_dir)

    controller = {
        "command": shlex.join([sys.executable, *sys.argv]),
        "experiment": "iter28_nuscenes_trainval_staging",
        "inputs": inputs,
        "remote": {
            "instance": args.instance,
            "project": args.project,
            "result_tgz": args.remote_result_tgz,
            "workdir": args.remote_workdir,
            "zone": args.zone,
        },
        "remote_stdout": result.stdout,
        "stage": "iter28_remote_bounded_inventory_controller",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    controller_path = args.out_dir / "remote_inventory_controller.json"
    controller_path.write_text(json.dumps(controller, indent=2, sort_keys=True) + "\n")
    write_text(
        args.out_dir / "remote_inventory_controller.sha256",
        f"{sha256_file(controller_path)}  remote_inventory_controller.json",
    )
    print(result.stdout.strip())
    print(f"iter28 remote inventory proof_dir={args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
