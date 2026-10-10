"""Independent scalar execution and outcome replay; no runner/simulator imports."""

import hashlib
import json
import math
from pathlib import Path

from experiments.iter145_constrained_execution.independent import certificate, check, close, motion
from experiments.iter145_constrained_execution.gpu_check import (
    decode,
    nominal_reference,
    overlap,
    check_attack_execution,
)
from experiments.iter145_constrained_execution.resources import file_identity


def strict(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            check(key not in result, "duplicate JSON key")
            result[key] = value
        return result

    def constant(value):
        raise ValueError("nonfinite JSON constant:" + value)

    result = json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)

    def finite(value):
        if isinstance(value, dict):
            for item in value.values():
                finite(item)
        elif isinstance(value, list):
            for item in value:
                finite(item)
        elif isinstance(value, float):
            check(math.isfinite(value), "nonfinite JSON number")

    finite(result)
    return result


def read(directory):
    directory = Path(directory).absolute()
    raw = file_identity(directory / "events.jsonl", max_bytes=256 * 1024**2, include_bytes=True)[
        "data"
    ]
    summary = file_identity(directory / "summary.json", max_bytes=4 * 1024**2, include_bytes=True)[
        "data"
    ]
    check(raw.endswith(b"\n"), "incomplete trace")
    lines = raw.splitlines()
    check(all(len(line) <= 4 * 1024**2 for line in lines), "event size")
    rows = [strict(line) for line in lines]
    s = strict(summary)
    check(
        s["events_sha256"] == hashlib.sha256(raw).hexdigest() and s["events_bytes"] == len(raw),
        "trace identity",
    )
    return rows, s


def verify(rows, summary):
    check(
        summary["schema"] in ("sentinel.iter146.summary.v1", "sentinel.iter146.summary.v2")
        and summary["status"] == "completed",
        "incomplete execution",
    )
    check(
        all(type(r["seq"]) is int for r in rows)
        and [r["seq"] for r in rows] == list(range(len(rows))),
        "event order",
    )
    head = rows[0]
    check(head["event"] == "header" and head["schema"] == "sentinel.iter146.trace.v1", "header")
    check(head["episode"] == summary["episode"] and head["arm"] == summary["arm"], "run identity")
    check(
        head["seed"] == summary["seed"] == 144 and head["max_actions"] == summary["max_actions"],
        "seed or cap",
    )
    check(type(head["max_actions"]) is int and 1 <= head["max_actions"] <= 401, "action envelope")
    check(head["arm"] in ("nominal", "monitor", "brake_t0", "brake_t2_5"), "arm")
    route = head["route"]
    check(2 <= len(route) <= 100000, "route count")
    for point in route:
        check(len(point) == 2, "route point")
        close(point, point, 0)
    grouped = {}
    for row in rows:
        grouped.setdefault(row["event"], []).append(row)
    check(
        set(grouped)
        <= {
            "header",
            "reset",
            "control",
            "step",
            "actor",
            "stop",
            "runner_stop",
            "outcome_observation",
            "observation",
            "delivery",
            "monitor",
        },
        "unknown event",
    )
    check(
        len(grouped["header"]) == len(grouped.get("runner_stop", [])) == 1, "header/stop inventory"
    )
    stop = rows[-1]
    check(
        stop["event"] == "runner_stop"
        and stop["reason"] == summary["stop_reason"]
        and stop["status"] == summary["status"]
        and stop["steps"] == summary["steps"],
        "stop binding",
    )
    resets, controls, steps, outcomes = (
        grouped.get(k, []) for k in ("reset", "control", "step", "outcome_observation")
    )
    deliveries, observations = grouped.get("delivery", []), grouped.get("observation", [])
    monitors = grouped.get("monitor", [])
    n = len(steps)
    check(
        len(resets) == 1 and len(controls) == len(outcomes) == n == summary["steps"],
        "event cardinality",
    )
    reason = summary["stop_reason"]
    check(
        reason
        in (
            "source_terminal",
            "source_truncated",
            "action_cap",
            "wall_deadline_before_exchange",
            "wall_deadline_after_exchange",
            "wall_deadline_after_step",
        ),
        "stop reason",
    )
    extra = int(reason == "wall_deadline_after_exchange")
    check(
        len(deliveries) == len(observations) == len(monitors) == n + extra, "delivery cardinality"
    )
    check(len(summary["timings"]) == n, "timing cardinality")
    actors = [r["value"] for r in grouped.get("actor", []) if r["value"]["event"] == "consume"]
    actor_resets = [r["value"] for r in grouped.get("actor", []) if r["value"]["event"] == "reset"]
    check(
        len(actors) == n and len(actor_resets) == 1 and actor_resets[0]["advanced"] is False,
        "actor resets/steps",
    )
    selections = check_attack_execution(rows, actors)
    previous = resets[0]["state"]
    close(resets[0]["time"], 0, 0)
    maximum = 0.0
    any_collision = any_offroute = False
    first_failure = None
    scientific = []
    for i, (control, step, outcome, delivery, obs, actor, timing) in enumerate(
        zip(controls, steps, outcomes, deliveries, observations, actors, summary["timings"])
    ):
        check(
            control["frame"] == delivery["frame"] == obs["frame"] == timing["frame"] == i,
            "frame sequence",
        )
        check(step["frame"] == outcome["frame"] == i + 1, "step frame")
        close([step["time"], outcome["time"], actor["time"]], [(i + 1) / 4] * 3, 0)
        close(obs["time"], i / 4, 0)
        check(
            obs["seq"] < delivery["seq"] < control["seq"] < step["seq"] < outcome["seq"],
            "causal event order",
        )
        value, r = delivery["value"], control["result"]
        check(value == control["delivery"], "control transport")
        check(
            value["schema"] == "sentinel.iter145.delivery.v1"
            and value["coordinate_frame"] == "hugsim.ego_lidar.right_forward",
            "delivery schema",
        )
        check(
            value["episode"] == r["episode"] == head["episode"]
            and value["frame"] == i
            and value["mode"] == head["arm"],
            "delivery identity",
        )
        close(value["observation_time"], i / 4, 0)
        close(value["knot_times"], [i / 4 + j / 2 for j in range(1, 7)], 0)
        nominal, proposed, delivered = (
            decode(value[k]) for k in ("nominal", "proposed", "delivered")
        )
        monitor = monitors[i]
        check(
            monitor["frame"] == i
            and hashlib.sha256(monitor["raw"].encode()).hexdigest() == value["monitor_sha256"],
            "monitor binding",
        )
        decision = strict(monitor["raw"])
        check(
            decision["frame_index"] == i
            and decision["ts"] == i / 4
            and type(decision["brake"]) is bool
            and "trace_error" not in decision,
            "monitor observation",
        )
        close(decision["traj"], nominal, 0)
        close(proposed, [[0.0, 0.0]] * 6 if decision["brake"] else nominal, 0)
        close(delivered, proposed if head["arm"] == "monitor" else nominal, 0)
        expected_ref = nominal_reference(previous, delivered)
        check(len(r["reference"]) == 13 and len(r["inputs"]) == 12, "control horizon")
        for actual, expected in zip(r["reference"], expected_ref):
            close(actual[:2] + actual[3:], expected[:2] + expected[3:])
            close(
                math.atan2(math.sin(actual[2] - expected[2]), math.cos(actual[2] - expected[2])), 0
            )
        c = certificate(r)
        maximum = max(maximum, c["stationarity"])
        check(r["admitted"] is True, "controller not admitted")
        close(r["initial_state"], previous, 0)
        close([r["observation_time"], r["application_time"]], [i / 4, (i + 1) / 4], 0)
        close(step["before"], previous, 0)
        action = list(r["applied"])
        start = {"brake_t0": 0, "brake_t2_5": 2.5}.get(head["arm"])
        if start is not None and start <= i / 4 < start + 1:
            action[0] = -math.copysign(min(2, abs(previous[3]) * 4), previous[3])
        close([step["applied"]["acc"], step["applied"]["steer_rate"]], action, 0)
        close(step["after"], motion(previous, [action])[1])
        previous = step["after"]
        distances = [math.hypot(p[0] - previous[1], p[1] - previous[0]) for p in route]
        nearest = min(range(len(route)), key=lambda j: (distances[j], j))
        rc, dist = (nearest + 1) / (0.9 * len(route)), distances[nearest]
        close([outcome["rc"], step["info"]["rc"], outcome["route_distance"]], [rc, rc, dist])
        check(
            outcome["nearest_index"] == nearest and outcome["route_samples"] == len(route),
            "route index",
        )
        check(outcome["final_sample_observed"] is (nearest == len(route) - 1), "route end")
        records = outcome["collision_records"]
        check([r["kind"] for r in records] == ["background", "foreground"], "collision sources")
        check(
            all(type(r["result"]) is bool and r["time"] == outcome["time"] for r in records),
            "collision time/type",
        )
        fg = records[1]
        close(fg["ego_box"], step["info"]["ego_box"], 0)
        close(fg["objects"], step["info"]["obj_boxes"], 0)
        check(
            fg["result"] == any(overlap(fg["ego_box"], box) for box in fg["objects"]),
            "foreground replay",
        )
        collided = any(r["result"] for r in records)
        off, complete = dist > 10, rc >= 1
        for key, expected in (
            ("collision", collided),
            ("off_route", off),
            ("source_completion", complete),
        ):
            check(outcome[key] is expected, "outcome boolean:" + key)
        check(step["info"]["collision"] is collided, "collision aggregate")
        check(
            type(outcome["truncated"]) is bool
            and outcome["terminated"] is (collided or off or complete),
            "source termination",
        )
        # The source overwrites reward in this order. Reward does not define success.
        close(
            outcome["reward"], 1000 if complete else (-50 if off else (-100 if collided else 0)), 0
        )
        check(
            i == n - 1 or not outcome["terminated"] and not outcome["truncated"],
            "continued after terminal",
        )
        any_collision |= collided
        any_offroute |= off
        if first_failure is None and (collided or off):
            first_failure = outcome["time"]
        check(
            type(timing["full_loop_ns"]) is int and timing["full_loop_ns"] > 0, "full loop timing"
        )
        check(
            timing["exchange_ns"] == delivery["exchange_ns"]
            and 0 < delivery["exchange_ns"] < timing["full_loop_ns"],
            "exchange timing",
        )
        check(
            r["complete_call_ns"] <= step["complete_step_ns"] <= timing["full_loop_ns"],
            "timing nesting",
        )
        if summary["schema"] == "sentinel.iter146.summary.v2":
            start, work_end, end, work = (
                timing[key]
                for key in ("loop_start_ns", "loop_work_end_ns", "loop_end_ns", "loop_work_ns")
            )
            check(all(type(v) is int for v in (start, work_end, end, work)), "timing boundary type")
            check(0 <= start < work_end <= end <= summary["elapsed_ns"], "timing boundaries")
            check(
                work == work_end - start and timing["full_loop_ns"] == end - start,
                "timing boundary differences",
            )
            check(
                timing["exchange_ns"] < work and step["complete_step_ns"] <= work,
                "work timing nesting",
            )
            if i:
                check(summary["timings"][i - 1]["loop_end_ns"] <= start, "overlapping loops")
        scientific.append(
            dict(
                time=outcome["time"],
                state=step["after"],
                action=action,
                nominal_action=r["applied"],
                rgb=obs["rgb"],
                actors=actor["states"],
                rc=rc,
                nominal=value["nominal"],
                delivered=value["delivered"],
                collision=collided,
                off_route=off,
            )
        )
    if reason == "action_cap":
        check(
            n == head["max_actions"]
            and not outcomes[-1]["terminated"]
            and not outcomes[-1]["truncated"],
            "false cap",
        )
    elif reason in ("source_terminal", "source_truncated"):
        check(
            n > 0 and outcomes[-1]["terminated" if reason == "source_terminal" else "truncated"],
            "false terminal",
        )
    else:
        check(summary["elapsed_ns"] >= summary["max_seconds"] * 1e9, "false deadline")
    source_stops = grouped.get("stop", [])
    terminal = bool(n and (outcomes[-1]["terminated"] or outcomes[-1]["truncated"]))
    check(len(source_stops) == int(terminal), "source stop count")
    if terminal:
        check(
            source_stops[0]["frame"] == n
            and source_stops[0]["time"] == n / 4
            and source_stops[0]["reason"]
            == ("simulator_terminated" if outcomes[-1]["terminated"] else "simulator_truncated"),
            "source stop",
        )
    expected = dict(
        collision_observed=any_collision if n else None,
        off_route_observed=any_offroute if n else None,
        simulator_completion=outcomes[-1]["source_completion"] if n else None,
        completion_qualified=reason == "source_terminal"
        and not any_collision
        and not any_offroute
        and bool(n and outcomes[-1]["source_completion"]),
        censored=reason != "source_terminal",
        execution_valid=True,
        first_failure_time=first_failure,
        final_sample_observed=outcomes[-1]["final_sample_observed"] if n else None,
    )
    check(summary["outcome"] == expected, "outcome classification")
    return dict(
        status="supported",
        episode=head["episode"],
        arm=head["arm"],
        steps=n,
        max_stationarity=maximum if n else None,
        attack_selections=selections,
        outcome=expected,
        scientific=scientific,
        route=route,
        reset_state=resets[0]["state"],
        scope="source execution with declared substitutions; background collision result retained, physical validity unestablished",
    )
