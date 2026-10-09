"""Strict trace capture and comparison for the Iter136 development canary."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re


SCHEMA = "sentinel.iter136.trace.v1"
TOLERANCE = 1e-6
MAX_BYTES = 16 * 1024 * 1024
STATE_KEYS = {"timestamp", "ego_pos", "ego_rot", "ego_velo", "ego_steer", "accelerate",
              "steer_rate", "command", "ego_box", "obj_boxes"}
FRAME_KEYS = {"frame", "time", "observation_sha256", "before", "incoming_plan",
              "executed_plan", "control", "after", "terminated", "truncated",
              "collision", "route_completion"}
IDENTITY_KEYS = {"case", "hugsim_commit", "uniad_commit", "scenario_sha256",
                 "checkpoint_sha256", "client_sha256", "driver_sha256",
                 "simulator_seed", "client_seed"}


def plain(value):
    if hasattr(value, "tolist"):
        value = value.tolist()
    if type(value) is dict:
        if any(type(k) is not str for k in value):
            raise ValueError("non-string key")
        return {k: plain(v) for k, v in value.items()}
    if type(value) in (list, tuple):
        return [plain(v) for v in value]
    if type(value) in (int, float):
        if not math.isfinite(value):
            raise ValueError("nonfinite number")
        return value
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported type {type(value).__name__}")


def canonical(value):
    return json.dumps(plain(value), sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode()


def state(info):
    if not STATE_KEYS <= set(info):
        raise ValueError("missing state fields")
    return plain({key: info[key] for key in sorted(STATE_KEYS)})


def observation_hash(obs):
    """Hash all RGB, semantic and depth arrays, including names, types and shapes."""
    if set(obs) != {"rgb", "semantic", "depth"}:
        raise ValueError("observation modalities")
    digest = hashlib.sha256()
    for modality in sorted(obs):
        if not obs[modality]:
            raise ValueError("empty observation")
        for camera, array in sorted(obs[modality].items()):
            # NumPy is already present in HUGSIM; keep the comparator dependency-free.
            import numpy as np
            if not np.isfinite(array).all():
                raise ValueError("nonfinite observation")
            header = canonical([modality, camera, str(array.dtype), list(array.shape)])
            body = array.tobytes(order="C")
            digest.update(len(header).to_bytes(8, "big") + header)
            digest.update(len(body).to_bytes(8, "big") + body)
    return digest.hexdigest()


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _bad_constant(value):
    raise ValueError(f"nonfinite JSON constant {value}")


def load_trace(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise ValueError("trace file type or size")
    with path.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES or not raw.endswith(b"\n"):
        raise ValueError("trace size or missing final newline")
    rows = [json.loads(line, object_pairs_hook=_pairs, parse_constant=_bad_constant)
            for line in raw.splitlines()]
    validate(rows)
    return rows


def _number(value):
    return type(value) in (int, float) and math.isfinite(value)


def _boolean(value):
    value = plain(value)
    if type(value) is not bool:
        raise ValueError("missing or non-Boolean outcome")
    return value


def validate(rows):
    if type(rows) is not list or not 3 <= len(rows) <= 403:
        raise ValueError("trace record count")
    plain(rows)
    header, footer = rows[0], rows[-1]
    if set(header) != {"schema", "identity", "arm", "stop_at"} or header["schema"] != SCHEMA:
        raise ValueError("header schema")
    identity = header["identity"]
    if type(identity) is not dict or set(identity) != IDENTITY_KEYS:
        raise ValueError("identity fields")
    expected = {"case": "scene-0411-hard-00",
                "hugsim_commit": "62c690d39fd90020e68a196bd8bcc1c4d4191f2e",
                "uniad_commit": "5fb279e39912a5ac7f58e00d56b065cadcd0a749",
                "scenario_sha256": "9f38bbdcdc49fe6ac5274a967b9a209417d621f67060357b97deacb887cf67a9",
                "checkpoint_sha256": "0ad0c2f5dc9788a41c313305779ea49346aeb742d1f6bb5ad25c46f9beffc990",
                "simulator_seed": 136, "client_seed": 0}
    for key, value in expected.items():
        if type(identity[key]) is not type(value) or identity[key] != value:
            raise ValueError(f"identity {key}")
    for key in ("client_sha256", "driver_sha256"):
        if type(identity[key]) is not str or not re.fullmatch("[0-9a-f]{64}", identity[key]):
            raise ValueError("source hash")
    stop_at = header["stop_at"]
    if header["arm"] == "reference":
        if stop_at is not None:
            raise ValueError("reference onset")
    elif header["arm"] == "stop":
        if not _number(stop_at) or stop_at not in (0.0, 2.0, 4.0):
            raise ValueError("unregistered onset")
    else:
        raise ValueError("arm")
    if set(footer) != {"end", "frames", "reason"} or footer["end"] != "completed":
        raise ValueError("incomplete episode")
    frames = rows[1:-1]
    if type(footer["frames"]) is not int or footer["frames"] != len(frames):
        raise ValueError("footer frame count")
    for i, row in enumerate(frames):
        if type(row) is not dict or set(row) != FRAME_KEYS:
            raise ValueError("frame fields")
        if type(row["frame"]) is not int or row["frame"] != i:
            raise ValueError("frame ordering")
        if not _number(row["time"]) or abs(row["time"] - i * 0.25) > TOLERANCE:
            raise ValueError("frame time")
        if type(row["observation_sha256"]) is not str or not re.fullmatch(
            "[0-9a-f]{64}", row["observation_sha256"]
        ):
            raise ValueError("observation hash")
        for key in ("before", "after"):
            if type(row[key]) is not dict or set(row[key]) != STATE_KEYS:
                raise ValueError("state fields")
            for field in ("timestamp", "ego_velo", "ego_steer", "accelerate", "steer_rate"):
                if not _number(row[key][field]):
                    raise ValueError("state scalar")
            for field, size in (("ego_pos", 3), ("ego_rot", 3), ("ego_box", 7)):
                vector = row[key][field]
                if type(vector) is not list or len(vector) != size or not all(
                    _number(v) for v in vector
                ):
                    raise ValueError("state vector")
            objects = row[key]["obj_boxes"]
            if type(objects) is not list or any(
                type(box) is not list or len(box) != 7 or not all(_number(v) for v in box)
                for box in objects
            ):
                raise ValueError("actor state")
            if type(row[key]["command"]) is not int:
                raise ValueError("command type")
        if abs(row["before"]["timestamp"] - row["time"]) > TOLERANCE or abs(
            row["after"]["timestamp"] - row["time"] - 0.25
        ) > TOLERANCE:
            raise ValueError("state timing")
        for key in ("incoming_plan", "executed_plan"):
            plan = row[key]
            if type(plan) is not list or len(plan) != 6 or any(
                type(p) is not list or len(p) != 2 or not all(_number(v) for v in p)
                for p in plan
            ):
                raise ValueError("trajectory shape")
        if type(row["control"]) is not list or len(row["control"]) != 2 or not all(
            _number(v) for v in row["control"]
        ):
            raise ValueError("control shape")
        for key in ("terminated", "truncated", "collision"):
            if type(row[key]) is not bool:
                raise ValueError("terminal flag type")
        if not _number(row["route_completion"]) or not 0 <= row["route_completion"] <= 1:
            raise ValueError("route completion")
        if i < len(frames) - 1 and (row["terminated"] or row["truncated"]):
            raise ValueError("frames after termination")
        active = stop_at is not None and row["time"] >= stop_at
        expected_plan = [[0.0, 0.0] for _ in range(6)] if active else row["incoming_plan"]
        if row["executed_plan"] != expected_plan:
            raise ValueError("intervention contract")
        if i and difference(frames[i-1]["after"], row["before"]):
            raise ValueError("discontinuous state")
    last = frames[-1]
    reason = ("collision" if last["collision"] else "route_complete"
              if last["terminated"] and last["route_completion"] >= 1 else "other_termination"
              if last["terminated"] else "truncated")
    if not (last["terminated"] or last["truncated"]) or footer["reason"] != reason:
        raise ValueError("terminal reason")


def difference(left, right, path="root"):
    if _number(left) and _number(right):
        return None if abs(left-right) <= TOLERANCE else path
    if type(left) is not type(right):
        return path
    if type(left) is dict:
        if set(left) != set(right):
            return path
        for key in sorted(left):
            result = difference(left[key], right[key], f"{path}.{key}")
            if result:
                return result
        return None
    if type(left) is list:
        if len(left) != len(right):
            return path
        for i, (a, b) in enumerate(zip(left, right)):
            result = difference(a, b, f"{path}[{i}]")
            if result:
                return result
        return None
    return None if left == right else path


def compare(reference, candidate):
    validate(reference)
    validate(candidate)
    if reference[0]["arm"] != "reference":
        raise ValueError("reference arm required")
    if reference[0]["identity"] != candidate[0]["identity"]:
        return {"status": "invalid", "first_difference": "identity"}
    onset = candidate[0]["stop_at"]
    if onset is None:
        location = difference(reference[1:], candidate[1:])
        return {"status": "REPLAY_DIVERGED" if location else "REPLAY_MATCHED",
                "first_difference": location, "frames": len(reference)-2}
    left, right = reference[1:-1], candidate[1:-1]
    onset_index = int(onset / 0.25)
    if len(left) <= onset_index or len(right) <= onset_index:
        return {"status": "unobserved", "reason": "onset_not_reached"}
    location = difference(left[:onset_index], right[:onset_index])
    for key in ("time", "observation_sha256", "before", "incoming_plan"):
        location = location or difference(left[onset_index][key], right[onset_index][key], key)
    if location:
        return {"status": "invalid", "first_difference": location}
    reference_collision = next((r["after"]["timestamp"] for r in left if r["collision"]), None)
    if reference_collision is None:
        return {"status": "NO_RECOVERABILITY_TARGET"}
    final = right[-1]
    reason = candidate[-1]["reason"]
    observed_horizon = final["after"]["timestamp"] >= reference_collision or reason == "route_complete"
    avoided = not any(r["collision"] for r in right) and observed_horizon and reason == "route_complete"
    progress_ok = final["route_completion"] >= left[-1]["route_completion"] - 0.05
    # Any early non-route terminal or truncation cannot count as prevention.
    return {"status": "supported" if avoided and progress_ok else "not_demonstrated",
            "collision_avoided": avoided, "progress_bar_met": progress_ok,
            "collision_observed": any(r["collision"] for r in right),
            "collision_type": None, "collision_type_status": "not_in_trace",
            "termination_time": final["after"]["timestamp"],
            "terminal_reason": reason, "route_completion": final["route_completion"],
            "observed_reference_collision_horizon": observed_horizon,
            "stop_frames": sum(r["time"] >= onset for r in right),
            "severity": None, "severity_status": "not_measured"}


class Recorder:
    """Called only by the source-bound instrumented driver; writes a new trace exclusively."""

    def __init__(self, output, driver):
        identity = json.loads(Path(os.environ["SENTINEL_I136_IDENTITY"]).read_text(),
                              object_pairs_hook=_pairs, parse_constant=_bad_constant)
        if hashlib.sha256(Path(driver).read_bytes()).hexdigest() != identity["driver_sha256"]:
            raise ValueError("executing driver identity")
        onset = os.environ.get("SENTINEL_I136_STOP_AT", "reference")
        if onset not in ("reference", "0", "2", "4"):
            raise ValueError("unregistered onset")
        self.stop_at = None if onset == "reference" else float(onset)
        self.rows = [{"schema": SCHEMA, "identity": identity,
                      "arm": "reference" if self.stop_at is None else "stop",
                      "stop_at": self.stop_at}]
        self.path = Path(output) / "iter136_trace.jsonl"
        self.stream = self.path.open("xb")
        self._write(self.rows[0])
        self.pending = None

    def _write(self, row):
        self.stream.write(canonical(row) + b"\n")
        self.stream.flush()
        if self.stream.tell() > MAX_BYTES:
            raise ValueError("trace budget exceeded")

    def begin(self, obs, info, index):
        if self.pending is not None:
            raise ValueError("unfinished frame")
        self.pending = {"frame": index, "time": plain(info["timestamp"]),
                        "observation_sha256": observation_hash(obs), "before": state(info)}

    def choose(self, incoming):
        import numpy as np
        if incoming is None:
            raise ValueError("planner returned no trajectory")
        self.pending["incoming_plan"] = plain(incoming)
        active = self.stop_at is not None and self.pending["time"] >= self.stop_at
        selected = np.zeros_like(incoming) if active else incoming
        self.pending["executed_plan"] = plain(selected)
        return selected

    def end_step(self, action, info, terminated, truncated):
        row = self.pending
        row.update(control=plain([action["acc"], action["steer_rate"]]), after=state(info),
                   terminated=_boolean(terminated), truncated=_boolean(truncated),
                   collision=_boolean(info["collision"]), route_completion=plain(info["rc"]))
        self.rows.append(row)
        self._write(row)
        self.pending = None

    def finish(self):
        last = self.rows[-1]
        reason = ("collision" if last["collision"] else "route_complete"
                  if last["terminated"] and last["route_completion"] >= 1 else "other_termination"
                  if last["terminated"] else "truncated")
        footer = {"end": "completed", "frames": len(self.rows)-1, "reason": reason}
        validate(self.rows + [footer])
        self._write(footer)
        self.stream.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    print(json.dumps(compare(load_trace(args.reference), load_trace(args.candidate)),
                     sort_keys=True, indent=2))
