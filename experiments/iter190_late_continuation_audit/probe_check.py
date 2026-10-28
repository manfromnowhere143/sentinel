"""Separate scalar controls, schedule, prefix and all-query validation."""

import math

from experiments.iter153_action_feasibility.check import near, path_reference, policy
from experiments.iter182_late_frontier_timing.replay import row_check, probe_check as beam_check
from experiments.iter182_late_frontier_timing.retained import state_key
from .common import require


def ancestors(rows, index):
    result = []
    while index is not None:
        result.insert(0, index)
        index = rows[index]["parent"]
    return result


def action(state, frame, mode, speed, geometry, old):
    points, arc = path_reference(geometry["route"], dict(offset=0.0, start=0.0, length=10.0), old)
    routed = policy(state, points, arc, dict(speed=speed), old)
    if frame >= 33:
        return routed
    rate = {
        "hold": 0.0,
        "center": min(math.pi / 12, max(-math.pi / 12, -state[4] / 0.25)),
        "route": routed[1],
    }[mode]
    return [min(2.0, max(-2.0, -state[3] / 0.25)), rate]


def check(value, prefix, case, old, cap, masks):
    rows = value["rows"]
    require(0 < len(rows) <= cap + 1 and value["attempts"] == len(rows) - 1, "arm_attempts")
    require(
        rows[0]["state"] == prefix[-1]["state"]
        and rows[0]["frame"] == prefix[-1]["frame"]
        and rows[0]["action"] is None
        and rows[0]["parent"] is None,
        "arm_root",
    )
    used = set()
    for i, row in enumerate(rows):
        require(type(row["frame"]) is int and 0 <= row["frame"] <= 96, "arm_frame")
        require(type(row["id"]) is int and row["id"] == i, "arm_ids")
        if i:
            require(type(row["parent"]) is int and 0 <= row["parent"] < i, "arm_parent")
            parent = rows[row["parent"]]
            require(
                parent["reason"] == "clear"
                and parent["route"]["rc"] < 1
                and row["frame"] == parent["frame"] + 1,
                "arm_parent_clock",
            )
        else:
            parent = row
        row_check(row, parent, case, old, masks)
        if row["background"] is not None:
            key = state_key(row["state"])
            require(key in masks, "arm_mask_missing")
            used.add(key)
    require(
        value["queries"]
        == sum(r["background"] is not None for r in rows)
        + (1 if value["method"] == "beam_then_route" else 0),
        "arm_queries",
    )
    beam = value["beam"]
    offset = 1
    checkpoint = None
    complete = None
    if value["method"] == "beam_then_route":
        require(isinstance(beam, dict), "beam_missing")
        count = beam["attempts"] + 1
        ids = (
            ancestors(rows, beam["selected"])
            if beam["witness"]
            else [r["id"] for r in beam["trace"]]
        )
        combined = [dict(r) for r in prefix] + [dict(r) for r in beam["trace"][1:]]
        for i, r in enumerate(combined):
            r.update(id=i, parent=i - 1 if i else None)
        record = dict(
            result=beam, selected_attempt_ids=ids, masks=[state_key(r["state"]) for r in combined]
        )
        beam_check(
            record,
            rows[:count],
            combined,
            prefix,
            case,
            old,
            dict(per_root_attempts=cap, target_frame=32, beam_width=16),
            masks,
        )
        offset = count
        if beam["witness"]:
            checkpoint = ancestors(rows, beam["selected"])
            if rows[beam["selected"]]["route"]["rc"] >= 1:
                complete = checkpoint
            schedule = [("route", 2.0)] if complete is None else []
        else:
            schedule = []
    else:
        require(value["method"] == "stop_wait_route" and beam is None, "arm_method")
        schedule = [
            (mode, speed) for mode in ("hold", "center", "route") for speed in (2.0, 4.0, 6.0)
        ]
    programs = value["programs"]
    require(len(programs) <= len(schedule), "program_population")
    stopped = None
    for number, program in enumerate(programs):
        require(stopped is None, "program_after_stop")
        mode, speed = schedule[number]
        require(
            program["number"] == number and program["mode"] == mode and program["speed"] == speed,
            "program_identity",
        )
        ids = program["ids"]
        start = beam["selected"] if beam else 0
        initial = ancestors(rows, start)
        require(ids[: len(initial)] == initial, "program_start")
        previous = start
        for index in ids[len(initial) :]:
            require(index == offset and rows[index]["parent"] == previous, "program_work_order")
            row = rows[index]
            expected = action(
                rows[previous]["state"],
                row["frame"],
                "route" if beam else mode,
                speed,
                case["geometry"],
                old,
            )
            near(row["action"], expected, 1e-10)
            previous = index
            offset += 1
            if row["reason"] == "clear" and row["frame"] == 32 and checkpoint is None:
                checkpoint = ancestors(rows, index)
            terminal = row["reason"] != "clear" or row["route"]["rc"] >= 1 or row["frame"] == 96
            require(not terminal or index == ids[-1], "continued_terminal")
        last = rows[ids[-1]]
        terminal = program["stop"]
        if terminal == "rejected":
            require(last["reason"] != "clear", "false_rejection")
        elif terminal == "horizon":
            require(
                last["reason"] == "clear" and last["frame"] == 96 and last["route"]["rc"] < 1,
                "false_horizon",
            )
        elif terminal == "complete":
            require(
                last["reason"] == "clear" and last["route"]["rc"] >= 1 and last["frame"] >= 32,
                "false_completion",
            )
            complete = ancestors(rows, last["id"])
            stopped = "complete"
        elif terminal == "attempt_budget":
            require(offset - 1 == cap, "early_attempt_stop")
            stopped = terminal
        else:
            require(terminal == "time_budget", "program_stop")
            stopped = terminal
    require(offset == len(rows), "arm_orphan_work")
    if complete is not None:
        require(value["stop"] == "complete", "hidden_complete")
    elif stopped is not None:
        require(value["stop"] == stopped, "arm_stop")
    elif beam and not beam["witness"]:
        require(value["stop"] == beam["stop"] and not programs, "beam_stop")
    else:
        require(
            value["stop"] == "programs_exhausted" and len(programs) == len(schedule),
            "omitted_programs",
        )
    require(
        value["checkpoint_ids"] == checkpoint and value["complete_ids"] == complete,
        "witness_binding",
    )
    return dict(checkpoint=checkpoint is not None, complete=complete is not None, used=used)
