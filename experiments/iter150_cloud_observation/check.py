"""Independent re-hashing of normalized native evidence; no adapter imports."""

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat


def verify(root, blobs, binding):
    root = Path(root)
    inventory = json.loads(blobs["raw"])
    if inventory.get("schema") != "sentinel.native_pair_inventory.v1":
        raise ValueError("schema")
    plan = json.loads((root / "plan.json").read_bytes())
    pair = binding["pair"]
    selected = plan["slots"][pair * 2 : pair * 2 + 2]
    required = {
        "execution_manifest.json",
        "plan.json",
        f"pair_{pair:03d}_started.json",
        f"pair_{pair:03d}_result.json",
    }
    for slot in selected:
        for suffix in (
            "worker_started.json",
            "worker.json",
            "trace/summary.json",
            "trace/events.jsonl",
            "sentinel_iter48_decisions.jsonl",
            "delivery145.jsonl",
        ):
            required.add(f"runs/{slot['id']}/{suffix}")
    if set(inventory.get("files", {})) != required or len(selected) != 2:
        raise ValueError("inventory_completeness")
    total = 0
    for name, expected in inventory["files"].items():
        parts = PurePosixPath(name).parts
        if not parts or name.startswith("/") or ".." in parts:
            raise ValueError("path")
        path = root
        for part in parts:
            path /= part
            if path.is_symlink():
                raise ValueError("symlink")
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            before = os.fstat(fd)
            if not stat.S_ISREG(before.st_mode) or before.st_size > 256 * 1024**2:
                raise ValueError("file")
            size, sha = 0, hashlib.sha256()
            while True:
                chunk = os.read(fd, 1024**2)
                if not chunk:
                    break
                sha.update(chunk)
                size += len(chunk)
                if size > 256 * 1024**2:
                    raise ValueError("size")
            after = os.fstat(fd)
            if (before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
                after.st_ino,
                after.st_size,
                after.st_mtime_ns,
                after.st_ctime_ns,
            ):
                raise ValueError("changing_file")
        finally:
            os.close(fd)
        if (
            type(expected.get("bytes")) is not int
            or expected["bytes"] != size
            or expected.get("sha256") != sha.hexdigest()
        ):
            raise ValueError("content")
        total += size
    if total > 1024**3:
        raise ValueError("total_size")
    # Independently reconstruct the identities carried by the normalized response.
    plan_digest = hashlib.sha256(
        json.dumps(plan, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()
    marker_name = f"pair_{pair:03d}_started.json"
    marker = json.loads((root / marker_name).read_bytes())
    if (
        binding.get("source_sha256") != inventory["files"]["execution_manifest.json"]["sha256"]
        or binding.get("plan_sha256") != plan_digest
        or binding.get("initialization_sha256") != inventory["files"][marker_name]["sha256"]
        or type(marker.get("pair")) is not int
        or marker["pair"] != pair
        or marker.get("plan_sha256") != plan_digest
    ):
        raise ValueError("native_identity")
    # Existing independently implemented native admission supplies the semantic cross-check.
    from experiments.iter148_recovery_study.admission import completed_pair

    parent = completed_pair(root, plan, pair)
    for slot, case in zip(selected, parent["cases"]):
        directory = root / "runs" / slot["id"]
        worker = json.loads((directory / "worker.json").read_bytes())
        summary = json.loads((directory / "trace/summary.json").read_bytes())
        if worker["summary"] != summary or worker["slot"] != case["slot"]:
            raise ValueError("native_binding")
        event = inventory["files"][f"runs/{slot['id']}/trace/events.jsonl"]
        if event != {"bytes": summary["events_bytes"], "sha256": summary["events_sha256"]}:
            raise ValueError("event_binding")
    return {
        "status": "supported",
        "files": len(required),
        "bytes": total,
        "scientific_admission": False,
    }
