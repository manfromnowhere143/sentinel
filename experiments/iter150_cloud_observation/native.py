"""Read-only native pair reconciliation, with streamed traces and small normalized replies."""

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat

from experiments.iter149_observation_recovery.recovery import digest, encode, validate_binding

META_LIMIT = 4 * 1024**2
TRACE_LIMIT = 256 * 1024**2


class EvidenceError(ValueError):
    """A native record is incomplete or does not establish terminal execution."""


def parse(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise EvidenceError("duplicate_key")
            result[key] = value
        return result

    def nonfinite(value):
        raise EvidenceError("nonfinite")

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)


def file(root, name, limit, content=False):
    """No-follow traversal under a trusted owned root; bounded streaming and mutation check."""
    parts = PurePosixPath(name).parts
    if not parts or PurePosixPath(name).is_absolute() or any(p in ("..", ".") for p in parts):
        raise EvidenceError("relative_path")
    directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for component in parts[:-1]:
            child = os.open(
                component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory
            )
            os.close(directory)
            directory = child
        fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        try:
            before = os.fstat(fd)
            if not stat.S_ISREG(before.st_mode) or not 0 <= before.st_size <= limit:
                raise EvidenceError("file_bound")
            sha, size, blocks = hashlib.sha256(), 0, []
            while True:
                block = os.read(fd, min(1024**2, limit + 1 - size))
                if not block:
                    break
                size += len(block)
                if size > limit:
                    raise EvidenceError("file_growth")
                sha.update(block)
                if content:
                    blocks.append(block)
            after = os.fstat(fd)
            current = os.stat(parts[-1], dir_fd=directory, follow_symlinks=False)
            fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
            if (
                any(
                    getattr(before, k) != getattr(after, k)
                    or getattr(after, k) != getattr(current, k)
                    for k in fields
                )
                or size != after.st_size
            ):
                raise EvidenceError("file_changed")
            result = {"bytes": size, "sha256": sha.hexdigest()}
            return (result, b"".join(blocks)) if content else result
        finally:
            os.close(fd)
    finally:
        os.close(directory)


def document(root, name):
    identity, raw = file(root, name, META_LIMIT, content=True)
    return identity, parse(raw)


def bind(root, pair, environment):
    actual = dict(environment)
    manifest_id, _ = document(root, "execution_manifest.json")
    _, plan = document(root, "plan.json")
    marker_id, marker = document(root, f"pair_{pair:03d}_started.json")
    actual.update(
        source_sha256=manifest_id["sha256"],
        plan_sha256=digest(encode(plan)),
        pair=pair,
        initialization_sha256=marker_id["sha256"],
    )
    validate_binding(actual)
    if type(marker.get("pair")) is not int or marker["pair"] != pair:
        raise EvidenceError("marker_pair")
    if marker.get("plan_sha256") != actual["plan_sha256"]:
        raise EvidenceError("marker_plan")
    return actual, plan


def terminal(root, pair, binding, plan):
    """Operational completeness only. Scientific replay remains mandatory elsewhere."""
    records = {}

    def get(name):
        identity, value = document(root, name)
        records[name] = identity
        return value

    get("execution_manifest.json")
    get("plan.json")
    get(f"pair_{pair:03d}_started.json")
    parent = get(f"pair_{pair:03d}_result.json")
    if (
        type(parent.get("pair")) is not int
        or parent["pair"] != pair
        or parent.get("plan_sha256") != binding["plan_sha256"]
    ):
        raise EvidenceError("parent_identity")
    if parent.get("status") == "failed":
        return "failed", {}
    selected = plan.get("slots", [])[pair * 2 : pair * 2 + 2]
    if (
        parent.get("status") != "completed"
        or len(selected) != 2
        or len(parent.get("cases", [])) != 2
    ):
        raise EvidenceError("parent_incomplete")
    for case, slot in zip(parent["cases"], selected):
        name = slot.get("id")
        if not isinstance(name, str) or not name or Path(name).name != name:
            raise EvidenceError("slot_path")
        if (
            encode(case.get("slot")) != encode(slot)
            or type(case.get("returncode")) is not int
            or case["returncode"] != 0
            or case.get("deadline_exceeded") is not False
            or case.get("cleanup") != {"status": "absent"}
        ):
            raise EvidenceError("parent_worker")
        prefix = f"runs/{name}/"
        started = get(prefix + "worker_started.json")
        worker = get(prefix + "worker.json")
        summary = get(prefix + "trace/summary.json")
        for row in (started, worker):
            if (
                encode(row.get("slot")) != encode(slot)
                or row.get("episode") != name
                or row.get("purpose") != plan.get("purpose")
            ):
                raise EvidenceError("worker_identity")
        if (
            worker.get("status") != "completed"
            or summary.get("status") != "completed"
            or summary.get("schema") != "sentinel.iter146.summary.v2"
            or summary.get("episode") != name
            or summary.get("arm") != slot["arm"]
            or summary.get("seed") != slot["seed"]
            or summary.get("max_actions") != slot["max_actions"]
            or summary.get("outcome", {}).get("execution_valid") is not True
            or encode(worker.get("summary")) != encode(summary)
        ):
            raise EvidenceError("worker_summary")
        trace_name = prefix + "trace/events.jsonl"
        records[trace_name] = file(root, trace_name, TRACE_LIMIT)
        if type(summary.get("events_bytes")) is not int or records[trace_name] != {
            "bytes": summary["events_bytes"],
            "sha256": summary.get("events_sha256"),
        }:
            raise EvidenceError("event_content")
        for suffix in ("sentinel_iter48_decisions.jsonl", "delivery145.jsonl"):
            records[prefix + suffix] = file(root, prefix + suffix, TRACE_LIMIT)
    # Re-read the exact inventory after construction. No success from a mutable mixed snapshot.
    for name, expected in records.items():
        if file(root, name, TRACE_LIMIT) != expected:
            raise EvidenceError("inventory_changed")
    raw = encode(
        {
            "schema": "sentinel.native_pair_inventory.v1",
            "files": records,
            "scope": "native_operational_records_not_scientific_admission",
        }
    )
    if len(raw) > 65536 or sum(x["bytes"] for x in records.values()) > 1024**3:
        raise EvidenceError("inventory_bound")
    bound = digest(encode(binding))
    blobs = {
        "raw": raw,
        "worker": encode(
            {
                "binding_sha256": bound,
                "status": "completed",
                "returncode": 0,
                "normalization": "native_pair_inventory",
            }
        ),
        "summary": encode(
            {
                "binding_sha256": bound,
                "status": "complete",
                "native_pair": pair,
                "scientific_admission": False,
            }
        ),
    }
    blobs["inventory"] = encode(
        {
            "binding_sha256": bound,
            "status": "sealed",
            "files": {
                key: {"bytes": len(value), "sha256": digest(value)} for key, value in blobs.items()
            },
        }
    )
    return "complete", blobs


def observe(root, pair, environment, expected, request, alive=False):
    """alive must come from a host ownership check, never from a mere PID/name lookup."""
    actual, plan = bind(root, pair, environment)
    blobs = {}
    if actual != expected:
        state, revision = "partial", 1
    else:
        try:
            state, blobs = terminal(root, pair, actual, plan)
            revision = 2
        except FileNotFoundError:
            state, revision = ("running", 0) if alive else ("partial", 1)
        except (EvidenceError, ValueError, OSError, KeyError, TypeError):
            state, revision = "partial", 1
    row = {
        "binding": actual,
        "request": request,
        "revision": revision,
        "state": state,
        "artifacts": {key: digest(value) for key, value in blobs.items()},
    }
    return encode(row), blobs
