"""Linux process birth identity and host deadline, never a PID-only liveness claim."""

import os
from pathlib import Path
import subprocess
import time

from experiments.iter150_cloud_observation.remote import context
from .native import bind, observe
from .records import read, record


def snapshot(pid, proc=Path("/proc")):
    if type(pid) is not int or pid <= 0:
        raise ValueError("pid")
    proc = Path(proc)
    base = proc / str(pid)

    def stat():
        raw = (base / "stat").read_text()
        prefix, tail = raw.rsplit(") ", 1)
        if int(prefix.split(" (", 1)[0]) != pid:
            raise ValueError("pid_stat")
        fields = tail.split()
        return fields[0], int(fields[1]), int(fields[19])

    state, parent, ticks = stat()
    command = (base / "cmdline").read_bytes().split(b"\0")
    if command[-1:] != [b""]:
        raise ValueError("process_command")
    command = [v.decode() for v in command[:-1]]
    executable = os.readlink(base / "exe")
    cwd = os.readlink(base / "cwd")
    boot = (proc / "sys/kernel/random/boot_id").read_text().strip()
    after = stat()
    if after[2] != ticks or after[1] != parent:
        raise ValueError("process_changed")
    return dict(
        pid=pid,
        parent=parent,
        start_ticks=ticks,
        command=command,
        executable=executable,
        cwd=cwd,
        boot=boot,
        state=after[0],
    )


def capture(control, pair, environment, service, proc=Path("/proc")):
    identity, _ = bind(control, pair, environment)
    owner = dict(binding=identity, process=snapshot(os.getpid(), proc), service=service)
    record(Path(control) / f"pair_{pair:03d}_owner.json", owner)
    return owner


def alive(owner, binding, proc=Path("/proc")):
    if owner.get("binding") != binding:
        raise ValueError("owner_binding")
    expected = owner["process"]
    try:
        actual = snapshot(expected["pid"], proc)
    except FileNotFoundError:
        return False
    if actual["boot"] != binding["host_boot"] or any(
        actual[k] != expected[k] for k in expected if k != "state"
    ):
        raise ValueError("owner_identity")
    return actual["state"] not in ("Z", "X")


def check_service(unit, expected_invocation=None, *, run=subprocess.run):
    q = run(
        [
            "systemctl",
            "show",
            unit,
            "--property=Id,ActiveState,MainPID,InvocationID,RuntimeMaxUSec,KillMode",
        ],
        capture_output=True,
        text=True,
        timeout=3,
    )
    if q.returncode:
        raise OSError("service_unobserved")
    values = dict(line.split("=", 1) for line in q.stdout.splitlines())
    if (
        values.get("Id") != unit
        or values.get("KillMode") != "control-group"
        or values.get("RuntimeMaxUSec") != "41min 40s"
    ):
        raise ValueError("service_deadline")
    if expected_invocation is not None and values.get("InvocationID") != expected_invocation:
        raise ValueError("service_invocation")
    return values


def observation(control, pair, expected, request, envelope):
    current = context(expected, envelope["timer_unit"], envelope["timer_readback"])
    if time.monotonic() >= envelope["deadline_monotonic"]:
        raise OSError("host_deadline_elapsed")
    owner = read(Path(control) / f"pair_{pair:03d}_owner.json")
    active = alive(owner, expected)
    if active:
        service = check_service(envelope["pair_units"][str(pair)], owner["service"]["InvocationID"])
        if int(service["MainPID"]) != owner["process"]["pid"] or service["ActiveState"] != "active":
            raise ValueError("service_owner")
    raw, blobs = observe(control, pair, current, expected, request, alive=active)
    return dict(raw_hex=raw.hex(), blobs_hex={k: v.hex() for k, v in blobs.items()})
