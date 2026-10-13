"""Exact immutable action packet and finite native action boundary."""

import hashlib
import math
from pathlib import Path

from experiments.iter150_cloud_observation.native import file, parse
from .admission import BASE, validate_plan
from .records import read


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def vector(value, size):
    require(type(value) is list and len(value) == size, "numeric_shape")
    require(all(type(v) in (int, float) and math.isfinite(v) for v in value), "numeric_value")
    return value


def near(actual, expected, tolerance=1e-9):
    vector(actual, len(expected))
    require(all(abs(a - b) <= tolerance for a, b in zip(actual, expected)), "state_mismatch")


def action_at(packet, frame, state):
    require(type(frame) is int and 0 <= frame < 66, "action_order")
    near(state, packet["expected_model_states"][frame])
    acc, rate = vector(packet["actions"][frame], 2)
    require(abs(acc) <= 2 and abs(rate) <= math.pi / 12, "action_bounds")
    speed, steering = state[3] + acc / 4, state[4] + rate / 4
    require(0 <= speed <= 6 and abs(steering) <= math.pi / 3, "state_bounds")
    yaw = speed * math.tan(steering) / 2.7
    require(abs(yaw) <= 0.95 and abs(speed * yaw) <= 4.89, "comfort_bounds")
    return {"acc": acc, "steer_rate": rate}


def packet(root):
    root = Path(root)
    document = validate_plan(read(root / BASE / "STUDY_PLAN.json"))
    identity, raw = file(root, document["selected_packet_path"], 1024**2, content=True)
    require(identity["sha256"] == document["selected_packet_sha256"], "selected_packet_identity")
    value = parse(raw)
    require(
        value["schema"] == "sentinel.iter163.selected_action.v1" and value["dt"] == 0.25,
        "packet_schema",
    )
    require(
        len(value["actions"]) == 66 and len(value["expected_model_states"]) == 67, "packet_horizon"
    )
    near(value["reset_state"], [0.0, 0.0, 0.0, 1.0, 0.0], 0)
    trace_id, trace_raw = file(root, value["trace_path"], 1024**2, content=True)
    require(trace_id["sha256"] == value["trace_sha256"], "source_trace_identity")
    trace = parse(trace_raw)
    require(
        value["actions"] == [r["action"] for r in trace[1:]]
        and value["expected_model_states"] == [r["state"] for r in trace],
        "source_trace_packet",
    )
    near(value["expected_model_states"][0], value["reset_state"], 0)
    for frame, state in enumerate(value["expected_model_states"][:-1]):
        action_at(value, frame, state)
    _, geometry_raw = file(root, document["geometry_path"], 1024**2, content=True)
    require(
        hashlib.sha256(geometry_raw).hexdigest() == document["geometry_sha256"], "geometry_identity"
    )
    return value, parse(geometry_raw)
