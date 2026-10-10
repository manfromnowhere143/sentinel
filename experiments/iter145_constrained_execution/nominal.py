"""Explicit, source-bound nominal plan times; no extrapolated controller horizon."""

import hashlib
import math
import numpy as np
from experiments.iter141_nominal_continuation.client import typed
from experiments.iter144_timed_trajectory.trajectory import (
    ContractError, DT, Trajectory, angle, ego_to_common, scalar,
)

SCHEMA = "sentinel.iter145.delivery.v1"
FRAME = "hugsim.ego_lidar.right_forward"
OFFSETS = (0.5, 1.0, 1.5, 2.0, 2.5, 3.0)


def decode(record):
    if not isinstance(record, dict) or set(record) != {"dtype", "shape", "bytes_hex", "sha256", "values"}:
        raise ContractError("typed_plan_fields")
    if record["dtype"] not in ("<f4", "<f8") or record["shape"] != [6, 2]:
        raise ContractError("typed_plan_shape")
    raw = bytes.fromhex(record["bytes_hex"])
    if len(raw) != 12 * np.dtype(record["dtype"]).itemsize or hashlib.sha256(raw).hexdigest() != record["sha256"]:
        raise ContractError("typed_plan_identity")
    value = np.frombuffer(raw, dtype=record["dtype"]).reshape(6, 2).copy()
    if typed(value) != record:
        raise ContractError("typed_plan_values")
    return value


def packet(nominal, proposed, delivered, *, episode, frame, time, mode, monitor_sha256):
    result = dict(schema=SCHEMA, coordinate_frame=FRAME, episode=episode, frame=frame,
                  observation_time=scalar(time), knot_times=[time + t for t in OFFSETS],
                  mode=mode, nominal=typed(nominal), proposed=typed(proposed),
                  delivered=typed(delivered), monitor_sha256=monitor_sha256)
    validate(result, episode=episode, frame=frame, time=time)
    return result


def validate(value, *, episode, frame, time):
    if (value.get("schema") != SCHEMA or value.get("coordinate_frame") != FRAME
            or not isinstance(episode, str) or not episode or value.get("episode") != episode
            or type(frame) is not int or frame < 0 or type(value.get("frame")) is not int
            or value["frame"] != frame or scalar(time) != frame * DT
            or scalar(value.get("observation_time")) != time
            or value.get("knot_times") != [time + t for t in OFFSETS]
            or value.get("mode") not in ("nominal", "monitor", "brake_t0", "brake_t2_5")
            or not isinstance(value.get("monitor_sha256"), str)
            or len(value["monitor_sha256"]) != 64
            or any(c not in "0123456789abcdef" for c in value["monitor_sha256"])):
        raise ContractError("delivery_identity_time_or_mode")
    arrays = {key: decode(value[key]) for key in ("nominal", "proposed", "delivered")}
    expected = arrays["proposed"] if value["mode"] == "monitor" else arrays["nominal"]
    if typed(arrays["delivered"]) != typed(expected):
        raise ContractError("delivery_policy")
    return arrays["delivered"]


def reference(value, ego, *, episode, frame, time):
    """ego is [a,b,theta,signed_speed]; output uses the common world frame."""
    positions = validate(value, episode=episode, frame=frame, time=time)
    a, b, theta, speed = [scalar(float(x)) for x in ego]
    states = [ego_to_common((a, b, theta, speed))]
    previous = np.zeros(2)
    heading = 0.0
    for position in positions:
        right, forward = map(float, position)
        displacement = position.astype(float) - previous
        distance = float(np.linalg.norm(displacement))
        if distance > 0:
            heading = math.atan2(displacement[0], displacement[1])
        states.append((a + math.cos(theta) * right + math.sin(theta) * forward,
                       b - math.sin(theta) * right + math.cos(theta) * forward,
                       angle(math.pi / 2 - theta - heading), distance / 0.5))
        previous = position.astype(float)
    knots = Trajectory(episode, "ego", time, (time, *value["knot_times"]),
                       tuple(states), "nominal_source_half_second")
    times = tuple(time + i * DT for i in range(13))
    return Trajectory(episode, "ego", time, times, tuple(knots.at(t) for t in times),
                      "nominal_supported_quarter_second")
