"""Scalar replay of integration evidence; does not import the simulator/controller."""

import argparse
import hashlib
import json
import math
import struct
from pathlib import Path
from .independent import certificate, close, check, cost_gradient


def verify(raw):
    check(
        raw["schema"] == "sentinel.iter145.integration_cpu.v1" and raw["status"] == "completed",
        "raw integration schema",
    )
    check(raw["gpu_observed"] is False and raw["live_study_admitted"] is False, "scope")
    check(len(raw["cases"]) == 8, "fixture inventory")
    expected = [
        (v, c, r)
        for v, c in [(0.0, False), (4.0, False), (0.0, True), (4.0, True)]
        for r in range(2)
    ]
    maximum_stationarity = 0.0
    latencies = []
    all_controls = []
    selections = 0
    for case, identity in zip(raw["cases"], expected):
        check((case["speed"], case["curved"], case["replica"]) == identity, "fixture identity")
        summary = case["summary"]
        check(
            summary["status"] == "completed"
            and summary["steps"] == 12
            and summary["stop_reason"] == "smoke_step_cap",
            "fixture incomplete",
        )
        events = case["events"]
        resets = [e for e in events if e["event"] == "reset"]
        controls = [e for e in events if e["event"] == "control"]
        steps = [e for e in events if e["event"] == "step"]
        actors = [
            e["value"] for e in events if e["event"] == "actor" and e["value"]["event"] == "consume"
        ]
        check(
            len(resets) == 1 and len(controls) == len(steps) == len(actors) == 12,
            "event cardinality",
        )
        check(len(case["boundary"]) == 12, "boundary cardinality")
        close(resets[0]["state"], [0.0, 0.0, 0.0, case["speed"], 0.0], 0)
        previous = resets[0]["state"]
        for i, (control, step, actor, boundary) in enumerate(
            zip(controls, steps, actors, case["boundary"])
        ):
            result = control["result"]
            check(control["frame"] == i and step["frame"] == i + 1, "frame sequence")
            close(result["observation_time"], i * 0.25, 0)
            close(result["application_time"], (i + 1) * 0.25, 0)
            close(step["time"], (i + 1) * 0.25, 0)
            close(actor["time"], step["time"], 0)
            check(
                result["episode"] == case["episode"]
                and control["delivery"]["episode"] == case["episode"],
                "episode sequence",
            )
            delivery = control["delivery"]
            check(
                delivery["schema"] == "sentinel.iter145.delivery.v1"
                and delivery["frame"] == i
                and delivery["coordinate_frame"] == "hugsim.ego_lidar.right_forward"
                and delivery["observation_time"] == i * 0.25
                and delivery["mode"] == "nominal",
                "delivery contract",
            )
            expected_positions = [
                [0.03 * j * j if case["curved"] else 0.0, 2.0 * j] for j in range(1, 7)
            ]
            for key in ("nominal", "proposed", "delivered"):
                array = delivery[key]
                check(array["dtype"] == "<f8" and array["shape"] == [6, 2], "fixture typed plan")
                close(array["values"], expected_positions, 0)
                encoded = struct.pack("<12d", *(x for row in expected_positions for x in row))
                check(
                    array["bytes_hex"] == encoded.hex()
                    and array["sha256"] == hashlib.sha256(encoded).hexdigest(),
                    "typed plan identity",
                )
            check(len(result["inputs"]) == 12 and len(result["reference"]) == 13, "short horizon")
            close(control["reference"]["times"], [i * 0.25 + j * 0.25 for j in range(13)], 0)
            close(control["delivery"]["knot_times"], [i * 0.25 + j * 0.5 for j in range(1, 7)], 0)
            # Independent nominal knot transform and heading construction, including
            # measured t0. Check every half-second knot; quarter knots are interpolated.
            knots = [[previous[0], previous[1], previous[2], previous[3], 0.0]]
            last_right = last_forward = 0.0
            for j in range(1, 7):
                right, forward = (0.03 * j * j if case["curved"] else 0.0), 2.0 * j
                theta = math.atan2(right - last_right, forward - last_forward)
                knots.append(
                    [
                        previous[0]
                        + math.cos(previous[2]) * forward
                        - math.sin(previous[2]) * right,
                        previous[1]
                        + math.sin(previous[2]) * forward
                        + math.cos(previous[2]) * right,
                        previous[2] + theta,
                        math.hypot(right - last_right, forward - last_forward) / 0.5,
                        0.0,
                    ]
                )
                last_right, last_forward = right, forward
            for j in range(13):
                expected_ref = (
                    knots[j // 2]
                    if j % 2 == 0
                    else [(a + b) / 2 for a, b in zip(knots[j // 2], knots[j // 2 + 1])]
                )
                actual = result["reference"][j]
                close(actual[:2] + actual[3:], expected_ref[:2] + expected_ref[3:])
                close(
                    math.atan2(
                        math.sin(actual[2] - expected_ref[2]), math.cos(actual[2] - expected_ref[2])
                    ),
                    0.0,
                )
            metrics = certificate(result)
            maximum_stationarity = max(maximum_stationarity, metrics["stationarity"])
            check(result["admitted"] is True, "uncertified short horizon")
            close(result["initial_state"], previous, 0)
            close(step["before"], previous, 0)
            close([step["applied"]["acc"], step["applied"]["steer_rate"]], result["applied"], 0)
            predicted = cost_gradient(previous, [result["applied"]], [previous, previous])[2][1]
            close(step["after"], predicted)
            previous = step["after"]
            check(
                boundary["time"] == step["time"]
                and boundary["sequence"] == ["collision"] + ["render"] * 6
                and boundary["shared_transform_object"] is True,
                "render collision boundary",
            )
            boxes = boundary["observations"][0]["boxes"]
            close(boxes, step["info"]["obj_boxes"], 0)
            for camera in boundary["observations"][1:]:
                close(list(camera["matrices"].values()), list(actor["transforms"].values()), 0)
            for index, (name, state) in enumerate(actor["states"].items()):
                matrix = actor["transforms"][name]
                yaw = -state[2] if name == "agent_3" else -state[2] - math.pi / 2
                expected_matrix = [
                    [math.cos(yaw), 0.0, math.sin(yaw), state[0]],
                    [0.0, 1.0, 0.0, 0.0],
                    [-math.sin(yaw), 0.0, math.cos(yaw), state[1]],
                    [0.0, 0.0, 0.0, 1.0],
                ]
                close(matrix, expected_matrix, 4e-6)
                close(boxes[index][:3], [matrix[2][3], -matrix[0][3], -matrix[1][3]], 0)
            latencies.append(result["complete_call_ns"] / 1e6)
        for event in events:
            if event["event"] != "actor" or event["value"]["event"] != "select":
                continue
            selection = event["value"]
            selections += 1
            values = []
            for candidate in selection["candidates"]:
                close(candidate["times"], [selection["time"] + j * 0.25 for j in range(20)], 0)
                attack = min(
                    math.hypot(s[0] - e[0], s[1] - e[1])
                    for s, e in zip(candidate["states"], selection["ego"]["states"])
                )
                nearby = sum(
                    min(
                        math.hypot(s[0] - n[0], s[1] - n[1])
                        for s, n in zip(candidate["states"], neighbor["states"])
                    )
                    < 2
                    for neighbor in selection["neighbors"]
                )
                values.append(attack + 0.1 * nearby)
            close(selection["costs"], values)
            check(
                selection["selected"] == min(range(len(values)), key=lambda j: (values[j], j)),
                "actor selection",
            )
        all_controls.append(controls)
    for index in range(0, 8, 2):
        for a, b in zip(all_controls[index], all_controls[index + 1]):
            for key in ("inputs", "states", "objective"):
                close(a["result"][key], b["result"][key], 1e-9)
        first = [
            e["value"]
            for e in raw["cases"][index]["events"]
            if e["event"] == "actor" and e["value"]["event"] == "consume"
        ]
        second = [
            e["value"]
            for e in raw["cases"][index + 1]["events"]
            if e["event"] == "actor" and e["value"]["event"] == "consume"
        ]
        for a, b in zip(first, second):
            close(list(a["states"].values()), list(b["states"].values()), 1e-9)
            close(list(a["transforms"].values()), list(b["transforms"].values()), 0)
    return dict(
        status="supported",
        verdict="SIMULATOR_CPU_WIRING_QUALIFIED",
        independent_validation="passed",
        cases=8,
        replica_pairs=4,
        steps=96,
        actor_advances=384,
        selections=selections,
        max_stationarity=maximum_stationarity,
        complete_call_ms=latencies,
        gpu_observed=False,
        live_study_admitted=False,
        scope="Full retained source method wiring with named CPU substitutions; actual assets, CUDA/GEOS and model transport unqualified.",
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--raw", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    try:
        result = verify(json.loads(a.raw.read_text()))
        code = 0
    except (ValueError, KeyError, TypeError, IndexError) as exc:
        result = dict(status="invalid", error=str(exc))
        code = 2
    with a.output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps(result))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
