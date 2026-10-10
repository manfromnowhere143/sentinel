"""Released monitor boundary with typed timestamped delivery to the simulator."""

import hashlib
import json
import os
from pathlib import Path
import numpy as np
from experiments.iter141_nominal_continuation.client import typed
from .nominal import packet


def deliver(nominal, result, data, output, monitor, enabled, info):
    episode, mode = os.environ["SENTINEL_I145_EPISODE"], os.environ["SENTINEL_I145_MODE"]
    if enabled is not True or info.get("sentinel_episode") != episode or info["timestamp"] != float(data["timestamp"]):
        raise ValueError("client observation identity")
    frame = info["sentinel_frame"]
    original = typed(nominal)
    proposed = monitor(nominal, result, data, output)
    if typed(nominal) != original:
        raise ValueError("monitor mutated nominal")
    path = Path(output) / "sentinel_iter48_decisions.jsonl"
    if path.is_symlink() or path.stat().st_size > 16*1024**2:
        raise ValueError("monitor log boundary")
    raw = path.read_bytes()
    if not raw.endswith(b"\n") or len(raw.splitlines()) != frame + 1:
        raise ValueError("monitor log ordering")
    line = raw.splitlines()[-1]; row = json.loads(line)
    if ("trace_error" in row or row.get("frame_index") != frame or row.get("ts") != info["timestamp"]
            or type(row.get("brake")) is not bool or row.get("traj") != original["values"]):
        raise ValueError("monitor observation alignment")
    if typed(proposed) != typed(np.zeros_like(nominal) if row["brake"] else nominal):
        raise ValueError("monitor proposal mismatch")
    delivered = proposed if mode == "monitor" else nominal
    value = packet(nominal, proposed, delivered, episode=episode, frame=frame, time=info["timestamp"],
                   mode=mode, monitor_sha256=hashlib.sha256(line).hexdigest())
    target = Path(output) / "delivery145.jsonl"
    if frame and (target.is_symlink() or not target.read_bytes().endswith(b"\n") or len(target.read_bytes().splitlines()) != frame):
        raise ValueError("delivery ordering")
    with target.open("x" if frame == 0 else "a") as stream:
        stream.write(json.dumps(value, sort_keys=True, allow_nan=False) + "\n")
    return value


def instrument(raw):
    from experiments.iter141_nominal_continuation.instrument import CLIENT_SHA
    if hashlib.sha256(raw).hexdigest() != CLIENT_SHA:
        raise ValueError("client source identity")
    anchor = "            plan_traj = _sentinel_i48_intervene(plan_traj, results[0], data, args.output)"
    source = raw.decode()
    if source.count(anchor) != 1:
        raise ValueError("client source anchor")
    source = source.replace(anchor,
        "            from experiments.iter145_constrained_execution.client import deliver\n"
        "            plan_traj = deliver(plan_traj, results[0], data, args.output,\n"
        "                                _sentinel_i48_intervene, _S48_ENABLED, raw_data[1])")
    compile(source, "iter145_client.py", "exec")
    return source.encode()
