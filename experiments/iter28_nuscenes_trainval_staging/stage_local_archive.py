#!/usr/bin/env python3
"""Upload one completed official nuScenes trainval archive to the iter28 staging disk.

This is a staging/provenance script, not an extraction or model script. It accepts one completed
local archive, verifies it belongs to the frozen iter28 package set, copies it to
sentinel-gpu:/datasets/nuscenes-full/archives, verifies remote byte count and SHA256, and writes a
small proof JSON suitable for committing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT = "sunlit-unison-487018-b0"
ZONE = "us-west1-a"
INSTANCE = "sentinel-gpu"
DEST_ROOT = "/datasets/nuscenes-full"
OUT_DIR = Path("experiments/iter28_nuscenes_trainval_staging/proof-staging/uploads")

EXPECTED: dict[str, str] = {
    "metadata": "v1.0-trainval_meta.tgz",
    "1": "v1.0-trainval01_blobs.tgz",
    "2": "v1.0-trainval02_blobs.tgz",
    "3": "v1.0-trainval03_blobs.tgz",
    "4": "v1.0-trainval04_blobs.tgz",
    "5": "v1.0-trainval05_blobs.tgz",
    "6": "v1.0-trainval06_blobs.tgz",
    "7": "v1.0-trainval07_blobs.tgz",
    "8": "v1.0-trainval08_blobs.tgz",
    "9": "v1.0-trainval09_blobs.tgz",
    "10": "v1.0-trainval10_blobs.tgz",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run_command(cmd: list[str], *, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=timeout)


def gcloud_base(args: argparse.Namespace) -> list[str]:
    return ["gcloud", "compute", *args.gcloud_prefix]


def remote_ssh(args: argparse.Namespace, command: str) -> subprocess.CompletedProcess[str]:
    cmd = [
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
    ]
    return run_command(cmd)


def remote_scp(args: argparse.Namespace, local_path: Path, remote_path: str) -> None:
    cmd = [
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
    ]
    run_command(cmd, timeout=None)


def parse_remote_verify(stdout: str) -> tuple[int, str]:
    size: int | None = None
    digest: str | None = None
    for line in stdout.splitlines():
        if line.startswith("ITER28_REMOTE_SIZE "):
            size = int(line.split()[1])
        if line.startswith("ITER28_REMOTE_SHA256 "):
            digest = line.split()[1]
    if size is None or digest is None:
        raise SystemExit("remote verification output missing size or sha256")
    return size, digest


def validate_local_path(path: Path, canonical_name: str, package: str) -> None:
    if not path.is_file():
        raise SystemExit(f"missing local archive: {path}")
    if path.name.endswith(".crdownload"):
        raise SystemExit(f"refusing active partial Chrome download: {path}")
    if package != "metadata" and path.name != canonical_name:
        raise SystemExit(f"expected local basename {canonical_name}, got {path.name}")
    if package == "metadata" and not path.name.startswith("v1.0-trainval_meta"):
        raise SystemExit(f"expected metadata archive basename, got {path.name}")
    if path.stat().st_size <= 0:
        raise SystemExit(f"refusing empty archive: {path}")


def proof_payload(
    *,
    args: argparse.Namespace,
    canonical_name: str,
    local_path: Path,
    local_size: int,
    local_sha256: str,
    remote_size: int,
    remote_sha256: str,
    preflight_stdout: str,
    verify_stdout: str,
) -> dict[str, Any]:
    return {
        "archive": {
            "canonical_name": canonical_name,
            "local_basename": local_path.name,
            "local_path": str(local_path),
            "local_sha256": local_sha256,
            "local_size_bytes": local_size,
            "package": args.package,
            "remote_path": f"{args.dest_root}/archives/{canonical_name}",
            "remote_sha256": remote_sha256,
            "remote_size_bytes": remote_size,
            "sha256_match": local_sha256 == remote_sha256,
            "size_match": local_size == remote_size,
        },
        "command": shlex.join([sys.executable, *sys.argv]),
        "destination": {
            "dest_root": args.dest_root,
            "instance": args.instance,
            "project": args.project,
            "zone": args.zone,
        },
        "experiment": "iter28_nuscenes_trainval_staging",
        "hypothesis": "experiments/iter28_nuscenes_trainval_staging/HYPOTHESIS.md",
        "preflight_stdout": preflight_stdout,
        "source_kind": "local_path",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "verify_stdout": verify_stdout,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True, choices=sorted(EXPECTED))
    parser.add_argument("--local-path", required=True, type=Path)
    parser.add_argument("--project", default=PROJECT)
    parser.add_argument("--zone", default=ZONE)
    parser.add_argument("--instance", default=INSTANCE)
    parser.add_argument("--dest-root", default=DEST_ROOT)
    parser.add_argument("--out-dir", default=str(OUT_DIR), type=Path)
    parser.add_argument(
        "--gcloud-prefix",
        nargs="*",
        default=[],
        help="reserved for tests; do not use in production",
    )
    args = parser.parse_args()

    canonical_name = EXPECTED[args.package]
    local_path = args.local_path.expanduser().resolve()
    validate_local_path(local_path, canonical_name, args.package)

    local_size = local_path.stat().st_size
    local_sha256 = sha256_file(local_path)

    q_dest_root = shlex.quote(args.dest_root)
    q_archives = shlex.quote(f"{args.dest_root}/archives")
    preflight = remote_ssh(
        args,
        (
            "sudo bash -lc "
            + shlex.quote(
                "set -euo pipefail; "
                f"test -d {q_dest_root}; "
                f"mkdir -p {q_archives}; "
                f"df -B1 {q_dest_root}; "
                "docker ps --format '{{.Names}}'"
            )
        ),
    )

    remote_tmp = f"/tmp/iter28-upload-{canonical_name}"
    remote_scp(args, local_path, remote_tmp)

    q_tmp = shlex.quote(remote_tmp)
    q_remote = shlex.quote(f"{args.dest_root}/archives/{canonical_name}")
    verify = remote_ssh(
        args,
        (
            "sudo bash -lc "
            + shlex.quote(
                "set -euo pipefail; "
                f"install -m 0644 {q_tmp} {q_remote}; "
                f"rm -f {q_tmp}; "
                f"echo ITER28_REMOTE_SIZE $(stat -c %s {q_remote}); "
                f"echo ITER28_REMOTE_SHA256 $(sha256sum {q_remote} | awk '{{print $1}}')"
            )
        ),
    )
    remote_size, remote_sha256 = parse_remote_verify(verify.stdout)
    if remote_size != local_size:
        raise SystemExit(f"remote size mismatch: local={local_size} remote={remote_size}")
    if remote_sha256 != local_sha256:
        raise SystemExit(f"remote sha256 mismatch: local={local_sha256} remote={remote_sha256}")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    proof = proof_payload(
        args=args,
        canonical_name=canonical_name,
        local_path=local_path,
        local_size=local_size,
        local_sha256=local_sha256,
        remote_size=remote_size,
        remote_sha256=remote_sha256,
        preflight_stdout=preflight.stdout,
        verify_stdout=verify.stdout,
    )
    proof_path = args.out_dir / f"{canonical_name}.json"
    proof_path.write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n")
    print(f"ITER28_UPLOADED {canonical_name} bytes={local_size} sha256={local_sha256}")
    print(f"ITER28_PROOF {proof_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
