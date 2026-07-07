#!/usr/bin/env python3
"""Extract the staged iter28 nuScenes trainval archives with a path-safety gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import posixpath
import shlex
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import PurePosixPath


PROJECT = "sunlit-unison-487018-b0"
ZONE = "us-west1-a"
INSTANCE = "sentinel-gpu"
DEST_ROOT = "/datasets/nuscenes-full"
OUT_DIR = "experiments/iter28_nuscenes_trainval_staging/proof-extract"
EXPECTED_ARCHIVES = (
    "v1.0-trainval_meta.tgz",
    "v1.0-trainval01_blobs.tgz",
    "v1.0-trainval02_blobs.tgz",
    "v1.0-trainval03_blobs.tgz",
    "v1.0-trainval04_blobs.tgz",
    "v1.0-trainval05_blobs.tgz",
    "v1.0-trainval06_blobs.tgz",
    "v1.0-trainval07_blobs.tgz",
    "v1.0-trainval08_blobs.tgz",
    "v1.0-trainval09_blobs.tgz",
    "v1.0-trainval10_blobs.tgz",
)
CAMERA_CHANNELS = (
    "CAM_FRONT",
    "CAM_FRONT_LEFT",
    "CAM_FRONT_RIGHT",
    "CAM_BACK",
    "CAM_BACK_LEFT",
    "CAM_BACK_RIGHT",
)


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safety_reason(name: str, *, linkname: str = "", root: str = DEST_ROOT) -> str | None:
    """Return why a tar member is unsafe, or None when it stays inside root."""
    if not name:
        return "empty member name"
    if "\x00" in name:
        return "NUL byte in member name"
    if name.startswith("/"):
        return "absolute member path"

    normalized = posixpath.normpath(name)
    if normalized in ("", "."):
        return "empty normalized member path"
    if normalized == ".." or normalized.startswith("../"):
        return "parent traversal in member path"

    parts = PurePosixPath(normalized).parts
    if any(part == ".." for part in parts):
        return "parent traversal in member path"

    root_abs = os.path.abspath(root)
    target_abs = os.path.abspath(os.path.join(root_abs, *parts))
    if target_abs != root_abs and not target_abs.startswith(root_abs + os.sep):
        return "member path escapes destination root"

    if linkname:
        if "\x00" in linkname:
            return "NUL byte in link target"
        if linkname.startswith("/"):
            return "absolute link target"
        if any(part == ".." for part in PurePosixPath(linkname).parts):
            return "parent traversal in link target"
        link_norm = posixpath.normpath(posixpath.join(posixpath.dirname(normalized), linkname))
        if link_norm == ".." or link_norm.startswith("../"):
            return "parent traversal in link target"
        if any(part == ".." for part in PurePosixPath(link_norm).parts):
            return "parent traversal in link target"

    return None


REMOTE_EXTRACTOR = r'''
import json
import os
import posixpath
import subprocess
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import PurePosixPath

DEST_ROOT = "__DEST_ROOT__"
EXPECTED_ARCHIVES = __EXPECTED_ARCHIVES__
CAMERA_CHANNELS = __CAMERA_CHANNELS__


def safety_reason(name, linkname="", root=DEST_ROOT):
    if not name:
        return "empty member name"
    if "\x00" in name:
        return "NUL byte in member name"
    if name.startswith("/"):
        return "absolute member path"

    normalized = posixpath.normpath(name)
    if normalized in ("", "."):
        return "empty normalized member path"
    if normalized == ".." or normalized.startswith("../"):
        return "parent traversal in member path"

    parts = PurePosixPath(normalized).parts
    if any(part == ".." for part in parts):
        return "parent traversal in member path"

    root_abs = os.path.abspath(root)
    target_abs = os.path.abspath(os.path.join(root_abs, *parts))
    if target_abs != root_abs and not target_abs.startswith(root_abs + os.sep):
        return "member path escapes destination root"

    if linkname:
        if "\x00" in linkname:
            return "NUL byte in link target"
        if linkname.startswith("/"):
            return "absolute link target"
        if any(part == ".." for part in PurePosixPath(linkname).parts):
            return "parent traversal in link target"
        link_norm = posixpath.normpath(posixpath.join(posixpath.dirname(normalized), linkname))
        if link_norm == ".." or link_norm.startswith("../"):
            return "parent traversal in link target"
        if any(part == ".." for part in PurePosixPath(link_norm).parts):
            return "parent traversal in link target"

    return None


def archive_members_report(archive_path):
    result = {
        "archive": os.path.basename(archive_path),
        "first_members": [],
        "member_count": 0,
        "unsafe_members": [],
    }
    with tarfile.open(archive_path, "r:gz") as tf:
        for member in tf:
            result["member_count"] += 1
            if len(result["first_members"]) < 5:
                result["first_members"].append(member.name)
            linkname = member.linkname if member.issym() or member.islnk() else ""
            reason = safety_reason(member.name, linkname=linkname)
            if reason is not None:
                result["unsafe_members"].append(
                    {
                        "name": member.name,
                        "reason": reason,
                        "type": member.type.decode(errors="replace")
                        if isinstance(member.type, bytes)
                        else str(member.type),
                    }
                )
    return result


def camera_summary(root):
    summary = {}
    for channel in CAMERA_CHANNELS:
        path = os.path.join(root, "samples", channel)
        if os.path.isdir(path):
            try:
                count = sum(1 for entry in os.scandir(path) if entry.is_file())
            except OSError as exc:
                summary[channel] = {"present": True, "file_count_error": str(exc)}
            else:
                summary[channel] = {"present": True, "file_count": count}
        else:
            summary[channel] = {"present": False, "file_count": 0}
    return summary


def run(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def main():
    root = sys.argv[1]
    if root != DEST_ROOT:
        raise SystemExit(f"iter28 extraction may target only {DEST_ROOT}, got {root}")
    archive_dir = os.path.join(root, "archives")
    actual = sorted(name for name in os.listdir(archive_dir) if name.endswith(".tgz"))
    expected = sorted(EXPECTED_ARCHIVES)
    report = {
        "archive_dir": archive_dir,
        "archives": [],
        "camera_channels": {},
        "command": " ".join(sys.argv),
        "destination_root": root,
        "extraction": {"attempted": False, "completed": False},
        "expected_archives": expected,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "metadata_dir_present": False,
        "missing_archives": sorted(set(expected) - set(actual)),
        "path_traversal_attempts_accepted": 0,
        "stage": "iter28_extract_archives",
        "unexpected_archives": sorted(set(actual) - set(expected)),
    }
    if report["missing_archives"] or report["unexpected_archives"]:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 2

    unsafe_count = 0
    for name in expected:
        archive_path = os.path.join(archive_dir, name)
        archive_report = archive_members_report(archive_path)
        unsafe_count += len(archive_report["unsafe_members"])
        report["archives"].append(archive_report)

    report["unsafe_member_count"] = unsafe_count
    if unsafe_count:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 3

    report["extraction"]["attempted"] = True
    for name in expected:
        archive_path = os.path.join(archive_dir, name)
        run(
            [
                "tar",
                "--extract",
                "--gzip",
                "--file",
                archive_path,
                "--directory",
                root,
                "--no-same-owner",
                "--delay-directory-restore",
            ]
        )
    report["extraction"]["completed"] = True
    report["camera_channels"] = camera_summary(root)
    report["metadata_dir_present"] = os.path.isdir(os.path.join(root, "v1.0-trainval"))
    report["df_stdout"] = run(["df", "-B1", root]).stdout
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def render_remote_extractor(dest_root: str) -> str:
    return (
        REMOTE_EXTRACTOR.replace("__DEST_ROOT__", dest_root)
        .replace("__EXPECTED_ARCHIVES__", json.dumps(list(EXPECTED_ARCHIVES)))
        .replace("__CAMERA_CHANNELS__", json.dumps(list(CAMERA_CHANNELS)))
    )


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


def remote_scp(args: argparse.Namespace, local_path: str, remote_path: str) -> None:
    run_command(
        [
            *gcloud_base(args),
            "scp",
            local_path,
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


def write_text(path: str, text: str) -> None:
    with open(path, "w") as f:
        f.write(text if text.endswith("\n") else text + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=PROJECT)
    parser.add_argument("--zone", default=ZONE)
    parser.add_argument("--instance", default=INSTANCE)
    parser.add_argument("--dest-root", default=DEST_ROOT)
    parser.add_argument("--out-dir", default=OUT_DIR)
    args = parser.parse_args()

    if args.dest_root != DEST_ROOT:
        raise SystemExit(f"iter28 extraction may target only {DEST_ROOT}, got {args.dest_root}")

    remote_script = f"{args.dest_root}/.iter28_tmp/iter28-extract-archives.py"
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(render_remote_extractor(args.dest_root))
        local_script = f.name
    try:
        remote_scp(args, local_script, remote_script)
    finally:
        os.unlink(local_script)

    command = (
        "sudo bash -lc "
        + shlex.quote(
            "set -euo pipefail; "
            f"chmod 0700 {shlex.quote(remote_script)}; "
            f"python3 {shlex.quote(remote_script)} {shlex.quote(args.dest_root)}; "
            f"rm -f {shlex.quote(remote_script)}"
        )
    )
    result = remote_ssh(args, command)
    report = json.loads(result.stdout)
    report["controller"] = {
        "command": shlex.join([sys.executable, *sys.argv]),
        "instance": args.instance,
        "project": args.project,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "zone": args.zone,
    }

    os.makedirs(args.out_dir, exist_ok=True)
    report_path = os.path.join(args.out_dir, "extraction_safety_report.json")
    write_text(report_path, json.dumps(report, indent=2, sort_keys=True))
    write_text(
        os.path.join(args.out_dir, "extraction_safety_report.sha256"),
        f"{sha256_file(report_path)}  extraction_safety_report.json",
    )
    write_text(
        os.path.join(args.out_dir, "extraction_safety_report.command.txt"),
        shlex.join([sys.executable, *sys.argv]),
    )
    print(
        "iter28 extraction "
        f"archives={len(report['archives'])} "
        f"unsafe_members={report.get('unsafe_member_count')} "
        f"completed={report['extraction']['completed']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
