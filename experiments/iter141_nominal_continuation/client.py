"""Client-side typed capture and shadow delivery; no monitor algorithm change."""

import hashlib
import json
import os
from pathlib import Path

import numpy as np


def typed(value):
    if (
        not isinstance(value, np.ndarray)
        or value.dtype.str not in ("<f4", "<f8")
        or value.shape != (6, 2)
        or not np.isfinite(value).all()
    ):
        raise ValueError("actual planner dtype/shape/finite")
    a = np.ascontiguousarray(value)
    raw = a.tobytes()
    return dict(
        dtype=a.dtype.str,
        shape=list(a.shape),
        bytes_hex=raw.hex(),
        sha256=hashlib.sha256(raw).hexdigest(),
        values=a.tolist(),
    )


def deliver(nominal, result, data, output, monitor, enabled):
    mode = os.environ["SENTINEL_I141_MODE"]
    if mode not in ("reference", "nominal") or enabled is not True:
        raise ValueError("mode or enabled monitor")
    original = typed(nominal)
    proposed = monitor(nominal, result, data, output)
    if typed(nominal) != original:
        raise ValueError("monitor mutated nominal input")
    decisions = Path(output) / "sentinel_iter48_decisions.jsonl"
    raw = decisions.read_bytes()
    if len(raw) > 16 * 1024**2 or not raw.endswith(b"\n"):
        raise ValueError("monitor capture size/truncation")
    lines = raw.splitlines()
    row = json.loads(lines[-1])
    index = len(lines) - 1
    if (
        "trace_error" in row
        or row.get("frame_index") != index
        or row.get("ts") != float(data["timestamp"])
        or type(row.get("brake")) is not bool
        or row.get("traj") != original["values"]
    ):
        raise ValueError("monitor capture alignment/error")
    expected = np.zeros_like(nominal) if row["brake"] else nominal
    if typed(proposed) != typed(expected):
        raise ValueError("monitor proposal mismatch")
    delivered = nominal if mode == "nominal" else proposed
    capture = dict(
        schema="sentinel.iter141.delivery.v1",
        frame=index,
        time=float(data["timestamp"]),
        mode=mode,
        nominal=original,
        proposed=typed(proposed),
        delivered=typed(delivered),
        monitor_sha256=hashlib.sha256(lines[-1]).hexdigest(),
    )
    target = Path(output) / "delivery141.jsonl"
    if index == 0:
        stream = target.open("x")
    else:
        previous = target.read_bytes()
        if not previous.endswith(b"\n") or len(previous.splitlines()) != index:
            raise ValueError("delivery capture ordering")
        stream = target.open("a")
    with stream:
        stream.write(json.dumps(capture, sort_keys=True, allow_nan=False) + "\n")
    return delivered
