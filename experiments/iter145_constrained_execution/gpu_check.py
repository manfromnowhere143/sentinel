"""Independent scalar checks for real-render smoke records; no simulator imports."""

import hashlib
import json
import math
import struct
from pathlib import Path
from .independent import check, close, certificate, motion


def decode(record):
    check(record["shape"] == [6, 2] and record["dtype"] in ("<f4", "<f8"), "plan encoding")
    raw = bytes.fromhex(record["bytes_hex"])
    values = struct.unpack("<12" + ("f" if record["dtype"] == "<f4" else "d"), raw)
    check(hashlib.sha256(raw).hexdigest() == record["sha256"], "plan digest")
    rows = [list(values[i : i + 2]) for i in range(0, 12, 2)]
    close(record["values"], rows, 0)
    return rows


def nominal_reference(initial, positions):
    x, y, theta, v, _ = initial
    knots = [[x, y, theta, v, 0.0]]
    pr = pf = 0.0
    heading = 0.0
    for right, forward in positions:
        d = math.hypot(right - pr, forward - pf)
        if d > 0:
            heading = math.atan2(right - pr, forward - pf)
        knots.append(
            [
                x + math.cos(theta) * forward - math.sin(theta) * right,
                y + math.sin(theta) * forward + math.cos(theta) * right,
                theta + heading,
                d / 0.5,
                0.0,
            ]
        )
        pr, pf = right, forward
    result = []
    for j in range(13):
        if j % 2 == 0:
            result.append(knots[j // 2])
        else:
            a, b = knots[j // 2 : j // 2 + 2]
            row = [(u + w) / 2 for u, w in zip(a, b)]
            row[2] = a[2] + math.atan2(math.sin(b[2] - a[2]), math.cos(b[2] - a[2])) / 2
            result.append(row)
    return result


def polygon(box):
    x, y, _, width, length, _, yaw = box
    return [
        (x + u * math.cos(yaw) - v * math.sin(yaw), y + u * math.sin(yaw) + v * math.cos(yaw))
        for u, v in [
            (length / 2, width / 2),
            (length / 2, -width / 2),
            (-length / 2, -width / 2),
            (-length / 2, width / 2),
        ]
    ]


def overlap(a, b):
    a, b = polygon(a), polygon(b)
    for poly in (a, b):
        for p, q in zip(poly, poly[1:] + poly[:1]):
            axis = (p[1] - q[1], q[0] - p[0])
            aa = [x * axis[0] + y * axis[1] for x, y in a]
            bb = [x * axis[0] + y * axis[1] for x, y in b]
            if max(aa) < min(bb) or max(bb) < min(aa):
                return False
    return True


def check_attack_execution(events, actors):
    selections = [
        e["value"] for e in events if e["event"] == "actor" and e["value"]["event"] == "select"
    ]
    for row in selections:
        values = []
        for candidate in row["candidates"]:
            close(candidate["times"], [row["time"] + j * 0.25 for j in range(20)], 0)
            distance = min(
                math.hypot(a[0] - b[0], a[1] - b[1])
                for a, b in zip(candidate["states"], row["ego"]["states"])
            )
            penalty = sum(
                min(
                    math.hypot(a[0] - b[0], a[1] - b[1])
                    for a, b in zip(candidate["states"], n["states"])
                )
                < 2
                for n in row["neighbors"]
            )
            values.append(distance + 0.1 * penalty)
        close(row["costs"], values)
        check(
            row["selected"] == min(range(len(values)), key=lambda j: (values[j], j)),
            "attack selection",
        )
        chosen = row["candidates"][row["selected"]]
        for consume in actors:
            delta = consume["time"] - row["time"]
            if 0 < delta <= 2.5:
                expected = chosen["states"][round(delta / 0.25)]
                actual = consume["states"][row["actor"]]
                close(actual[:2] + actual[3:], expected[:2] + expected[3:])
                close(
                    math.atan2(
                        math.sin(actual[2] + math.pi / 2 - expected[2]),
                        math.cos(actual[2] + math.pi / 2 - expected[2]),
                    ),
                    0.0,
                )
    return len(selections)


def verify(directory):
    directory = Path(directory)
    worker = json.loads((directory / "worker.json").read_text())
    summary = json.loads((directory / "trace/summary.json").read_text())
    raw = (directory / "trace/events.jsonl").read_bytes()
    check(worker["status"] == "completed" and worker["gpu_observed"] is True, "gpu worker failed")
    check(
        worker["cleanup"]["status"] in ("removed", "absent") and worker["geos"],
        "cleanup or geometry unavailable",
    )
    check(
        summary["status"] == "completed"
        and summary["steps"] == 12
        and summary["stop_reason"] == "smoke_step_cap",
        "incomplete smoke",
    )
    check(hashlib.sha256(raw).hexdigest() == summary["events_sha256"], "event digest")
    events = [json.loads(line) for line in raw.splitlines()]
    by = {
        k: [e for e in events if e["event"] == k]
        for k in ("reset", "control", "step", "observation", "delivery", "stop")
    }
    check(
        len(by["reset"]) == 1
        and len(by["stop"]) == 1
        and by["stop"][0]["reason"] == "smoke_step_cap",
        "reset/stop count",
    )
    check(
        all(len(by[k]) == 12 for k in ("control", "step", "observation", "delivery")), "step counts"
    )
    decisions = [
        json.loads(line)
        for line in (directory / "sentinel_iter48_decisions.jsonl").read_text().splitlines()
    ]
    client = [
        json.loads(line) for line in (directory / "delivery145.jsonl").read_text().splitlines()
    ]
    decision_lines = (directory / "sentinel_iter48_decisions.jsonl").read_bytes().splitlines()
    check(len(decisions) == len(client) == 12, "monitor/client counts")
    actors = [
        e["value"] for e in events if e["event"] == "actor" and e["value"]["event"] == "consume"
    ]
    check(len(actors) == 12, "actor clocks")
    selections = check_attack_execution(events, actors)
    previous = by["reset"][0]["state"]
    latencies = []
    exchanges = []
    steps = []
    for i, (control, step, obs, delivery, actor) in enumerate(
        zip(by["control"], by["step"], by["observation"], by["delivery"], actors)
    ):
        check(
            control["frame"] == obs["frame"] == delivery["frame"] == i and step["frame"] == i + 1,
            "frame",
        )
        check(obs["time"] == i * 0.25 and step["time"] == actor["time"] == (i + 1) * 0.25, "time")
        value = delivery["value"]
        check(value == client[i] == control["delivery"], "transport bytes")
        check(
            value["episode"] == worker["episode"]
            and value["frame"] == i
            and value["mode"] == "nominal"
            and value["observation_time"] == i * 0.25,
            "delivery identity",
        )
        check(
            value["monitor_sha256"] == hashlib.sha256(decision_lines[i]).hexdigest(),
            "monitor binding",
        )
        positions = decode(value["nominal"])
        proposed = decode(value["proposed"])
        close(decode(value["delivered"]), positions, 0)
        decision = decisions[i]
        check(
            decision.get("frame_index") == i
            and decision.get("ts") == i * 0.25
            and type(decision.get("brake")) is bool
            and "trace_error" not in decision,
            "monitor observation",
        )
        close(decision["traj"], positions, 0)
        close(proposed, [[0.0, 0.0]] * 6 if decision["brake"] else positions, 0)
        close(value["knot_times"], [i * 0.25 + j * 0.5 for j in range(1, 7)], 0)
        result = control["result"]
        certificate(result)
        check(
            result["admitted"] is True and result["episode"] == worker["episode"],
            "controller admission",
        )
        close(result["initial_state"], previous, 0)
        close(step["before"], previous, 0)
        expected = nominal_reference(previous, positions)
        for a, b in zip(result["reference"], expected):
            close(a[:2] + a[3:], b[:2] + b[3:])
            close(math.atan2(math.sin(a[2] - b[2]), math.cos(a[2] - b[2])), 0.0)
        check(len(result["reference"]) == 13 and len(result["inputs"]) == 12, "horizon")
        close([step["applied"]["acc"], step["applied"]["steer_rate"]], result["applied"], 0)
        close(step["after"], motion(previous, [result["applied"]])[1])
        previous = step["after"]
        cameras = [r for r in worker["render_events"] if r["time"] == step["time"]]
        check(len(cameras) == 6 and len(obs["rgb"]) == 6, "camera count")
        for camera in cameras:
            check(
                camera["device"].startswith("cuda")
                and camera["shape"][0] == 3
                and min(camera["shape"][1:]) > 2
                and camera["elapsed_ns"] > 0,
                "cuda render",
            )
            check(set(camera["transforms"]) == set(actor["transforms"]), "render actor identities")
            for name in camera["transforms"]:
                close(camera["transforms"][name], actor["transforms"][name], 0)
        fg = [
            r
            for r in worker["collision_events"]
            if r["time"] == step["time"] and r["kind"] == "foreground"
        ]
        check(len(fg) == 1, "foreground count")
        close(fg[0]["objects"], step["info"]["obj_boxes"], 0)
        check(
            fg[0]["result"] == any(overlap(fg[0]["ego_box"], box) for box in fg[0]["objects"]),
            "GEOS replay",
        )
        latencies.append(result["complete_call_ns"] / 1e6)
        exchanges.append(delivery["exchange_seconds"])
        steps.append(step["complete_step_ns"] / 1e9)
    check(len(worker["render_events"]) == 78, "total camera count")
    return dict(
        status="supported",
        verdict="GPU_SMOKE_CONTRACT_SUPPORTED",
        episode=worker["episode"],
        steps=12,
        attack_selections=selections,
        gpu_observed=True,
        controller_ms=latencies,
        controller_over_50ms=sum(v > 50 for v in latencies),
        exchange_seconds=exchanges,
        step_seconds=steps,
        physical_validity="unestablished",
        live_study_admitted=False,
    )
