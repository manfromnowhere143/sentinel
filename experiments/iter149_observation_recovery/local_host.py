"""Real local subprocess fixture, independent of the observer. Not a cloud adapter."""

import argparse
import hashlib
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import time
import uuid

from .recovery import decode, digest, encode


def read(root, name, limit=65536):
    """Read one regular file without following its final symlink, bounded in size.

    root is an owned, trusted directory, never an externally supplied path traversal.
    """
    if Path(name).name != name:
        raise ValueError("filename")
    directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
                raise ValueError("file_bounds")
            with os.fdopen(fd, "rb", closefd=False) as stream:
                raw = stream.read(limit + 1)
            if len(raw) > limit:
                raise ValueError("file_bounds")
            return raw
        finally:
            os.close(fd)
    finally:
        os.close(directory)


def write(root, name, value, exclusive=False):
    raw = encode(value)
    path = root / name
    if exclusive:
        with path.open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    else:
        temporary = root / (name + "." + uuid.uuid4().hex + ".tmp")
        with temporary.open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def observe(root, request, timeout):
    # Local reads only. A cloud transport must independently enforce timeout.
    try:
        snapshot = decode(read(root, "snapshot.json"))
    except (ValueError, UnicodeError) as exc:
        raise OSError("snapshot_unavailable") from exc
    snapshot["request"] = request
    blobs = {}
    for name in snapshot["artifacts"]:
        try:
            blobs[name] = read(root, name + ".json")
        except (OSError, ValueError):
            pass
    return encode(snapshot), blobs


def worker(root, seconds, crash):
    end = time.monotonic() + seconds
    with (root / "raw.json").open("xb") as stream:
        while time.monotonic() < end:
            stream.write(b'{"event":"synthetic_progress"}\n')
            stream.flush()
            os.fsync(stream.fileno())
            time.sleep(0.02)
    return 7 if crash else 0


def host(root, budget, seconds, crash=False):
    if not (0 < budget <= 60 and 0 < seconds <= 60):
        raise ValueError("local_fixture_budget")
    root.mkdir(exist_ok=False)
    # Exclusive directory plus marker: rerunning this command cannot initialize twice.
    token = uuid.uuid4().hex
    marker = {"session": token, "initialized": time.time_ns(), "count": 1}
    write(root, "initialized.json", marker, exclusive=True)
    binding = {
        "vm_id": "local-fixture",
        "vm_start": token,
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "plan_sha256": digest(encode({"budget": budget, "seconds": seconds, "crash": crash})),
        "pair": 0,
        "initialization_sha256": digest(read(root, "initialized.json")),
        "host_boot": token,
        "host_deadline_id": token + "-deadline",
    }
    write(root, "binding.json", binding, exclusive=True)
    started = time.monotonic()
    argv = [
        sys.executable,
        "-m",
        "experiments.iter149_observation_recovery.local_host",
        "worker",
        str(root),
        str(seconds),
    ]
    if crash:
        argv.append("--crash")
    child = subprocess.Popen(
        argv, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    snapshot = {
        "binding": binding,
        "request": "",
        "revision": 0,
        "state": "running",
        "artifacts": {},
    }
    expired = False
    try:
        write(
            root,
            "launch.json",
            {"pid": child.pid, "initializations": 1, "deadline": started + budget},
            exclusive=True,
        )
        write(root, "snapshot.json", snapshot)
        code = child.wait(timeout=max(0.0, started + budget - time.monotonic()))
    except subprocess.TimeoutExpired:
        expired = True
        os.killpg(child.pid, signal.SIGKILL)
        code = child.wait(timeout=5)
    finally:
        # A fixture write failure must not leave an unbounded child behind.
        if child.poll() is None:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait(timeout=5)
    bound = digest(encode(binding))
    write(
        root,
        "worker.json",
        {
            "binding_sha256": bound,
            "status": "completed" if code == 0 else "failed",
            "returncode": code,
        },
        exclusive=True,
    )
    if code == 0:
        write(
            root,
            "summary.json",
            {"binding_sha256": bound, "status": "complete", "scope": "synthetic_local_worker"},
            exclusive=True,
        )
        files = {
            name: {
                "bytes": len(read(root, name + ".json")),
                "sha256": digest(read(root, name + ".json")),
            }
            for name in ("raw", "worker", "summary")
        }
        write(
            root,
            "inventory.json",
            {"binding_sha256": bound, "status": "sealed", "files": files},
            exclusive=True,
        )
        hashes = {
            name: digest(read(root, name + ".json"))
            for name in ("raw", "worker", "summary", "inventory")
        }
        snapshot.update(state="complete", artifacts=hashes)
    else:
        snapshot.update(state="partial" if expired else "failed")
    snapshot["revision"] = 1
    write(root, "snapshot.json", snapshot)
    # wait() observed termination of our unreaped owned child; no process-name/PID lookup.
    write(
        root,
        "closure.json",
        {
            "binding": binding,
            "status": "terminated",
            "returncode": code,
            "deadline_fired": expired,
            "elapsed": time.monotonic() - started,
            "partial_raw_preserved": (root / "raw.json").exists(),
        },
        exclusive=True,
    )
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("host", "worker"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("seconds", type=float)
    parser.add_argument("--budget", type=float, default=2)
    parser.add_argument("--crash", action="store_true")
    args = parser.parse_args()
    if args.mode == "worker":
        return worker(args.directory, args.seconds, args.crash)
    return host(args.directory, args.budget, args.seconds, args.crash)


if __name__ == "__main__":
    raise SystemExit(main())
