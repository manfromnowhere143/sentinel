"""Read-only inventory for the existing Sentinel host; never starts an episode."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import socket
import subprocess


FILES = {
    "hugsim_driver": ("/opt/sentinel-stack/HUGSIM/closed_loop.py",
                      "42a0c878aa9e365b9e1b1d5e6d902c8fe6e2ee79deac376c23a2bd1ea439c8f5"),
    "scenario": ("/datasets/nuscenes-full/hugsim/extracted/scenarios/nuscenes/scene-0411-hard-00.yaml",
                 "9f38bbdcdc49fe6ac5274a967b9a209417d621f67060357b97deacb887cf67a9"),
    "checkpoint": ("/opt/sentinel-stack/UniAD/ckpts/uniad_base_e2e.pth",
                   "0ad0c2f5dc9788a41c313305779ea49346aeb742d1f6bb5ad25c46f9beffc990"),
    "client": ("/opt/sentinel-stack/UniAD_SIM/tools/closeloop/e2e.py", None),
    "client_launcher": ("/opt/sentinel-stack/UniAD_SIM/tools/e2e.sh", None),
    "shim": ("/opt/sentinel-stack/hugsim-shim/sitecustomize.py",
             "5bf69a1187478c52d49792d5871bd5732c6dd431ecd1f44b5e391f7adb80682c"),
}


def file_record(path, expected):
    p = Path(path)
    if not p.is_file():
        return {"path": path, "status": "missing", "sha256": None}
    digest = hashlib.sha256()
    with p.open("rb") as stream:
        for block in iter(lambda: stream.read(1024*1024), b""):
            digest.update(block)
    observed = digest.hexdigest()
    return {"path": path, "bytes": p.stat().st_size, "sha256": observed,
            "expected_sha256": expected,
            "status": "observed_unbound" if expected is None else
            "matched" if expected == observed else "mismatch"}


def command(argv):
    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=30)
        return {"argv": argv, "returncode": result.returncode,
                "stdout": result.stdout[:65536], "stderr": result.stderr[:65536],
                "truncated": len(result.stdout) > 65536 or len(result.stderr) > 65536}
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"argv": argv, "status": "unavailable", "error": type(error).__name__}


def inventory():
    if socket.gethostname().split(".")[0] != "sentinel-gpu":
        raise ValueError("host identity mismatch")
    mount = Path("/datasets/nuscenes-full")
    return {
        "schema": "sentinel.iter136.host_inventory.v1",
        "at_utc": datetime.now(timezone.utc).isoformat(), "host": socket.gethostname(),
        "files": {key: file_record(*spec) for key, spec in FILES.items()},
        "data_free_gib": shutil.disk_usage(mount).free/2**30 if mount.is_dir() else None,
        "scene_directory_exists": (mount / "hugsim/extracted/scenes/nuscenes/scene-0411").is_dir(),
        "scene_archive_exists": (mount / "hugsim/scenes/nuscenes/scene-0411.zip").is_file(),
        "commands": [command(args) for args in (
            ["git", "-C", "/opt/sentinel-stack/HUGSIM", "rev-parse", "HEAD"],
            ["git", "-C", "/opt/sentinel-stack/UniAD_SIM", "rev-parse", "HEAD"],
            ["docker", "ps", "--format", "{{.ID}} {{.Names}} {{.Image}}"],
            ["docker", "image", "inspect", "uniad:latest", "--format", "{{.Id}}"],
            ["nvidia-smi", "--query-compute-apps=pid,process_name,used_gpu_memory", "--format=csv"],
        )],
        "episode_authorized_by_this_report": False,
    }


if __name__ == "__main__":
    print(json.dumps(inventory(), sort_keys=True, indent=2, allow_nan=False))
