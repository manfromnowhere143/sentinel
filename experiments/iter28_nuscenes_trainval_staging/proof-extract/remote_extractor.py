
import json
import os
import posixpath
import subprocess
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import PurePosixPath

DEST_ROOT = "/datasets/nuscenes-full"
EXPECTED_ARCHIVES = ["v1.0-trainval_meta.tgz", "v1.0-trainval01_blobs.tgz", "v1.0-trainval02_blobs.tgz", "v1.0-trainval03_blobs.tgz", "v1.0-trainval04_blobs.tgz", "v1.0-trainval05_blobs.tgz", "v1.0-trainval06_blobs.tgz", "v1.0-trainval07_blobs.tgz", "v1.0-trainval08_blobs.tgz", "v1.0-trainval09_blobs.tgz", "v1.0-trainval10_blobs.tgz"]
CAMERA_CHANNELS = ["CAM_FRONT", "CAM_FRONT_LEFT", "CAM_FRONT_RIGHT", "CAM_BACK", "CAM_BACK_LEFT", "CAM_BACK_RIGHT"]


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
