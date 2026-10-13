"""Separate scalar native-outcome replay; never imports the action runner or GPU worker."""

import math
import re
from pathlib import Path

from experiments.iter145_constrained_execution.independent import check, close, motion
from experiments.iter145_constrained_execution.gpu_check import overlap
from experiments.iter146_route_outcome_contract.check import read, strict

CAMERAS = {
    "CAM_FRONT",
    "CAM_FRONT_LEFT",
    "CAM_FRONT_RIGHT",
    "CAM_BACK",
    "CAM_BACK_LEFT",
    "CAM_BACK_RIGHT",
}


def verify(rows, summary, selected, geometry, slot):
    check(
        summary["schema"] == "sentinel.iter163.summary.v1" and summary["status"] == "completed",
        "incomplete_execution",
    )
    check(
        all(type(r["seq"]) is int for r in rows)
        and [r["seq"] for r in rows] == list(range(len(rows))),
        "event_order",
    )
    head = rows[0]
    check(
        head["event"] == "header"
        and head["schema"] == "sentinel.iter163.trace.v1"
        and head["slot"] == slot
        and head["selected_candidate"] == "iter162_exact_width24"
        and head["inference_bypassed"] is True,
        "header_binding",
    )
    check(
        summary["episode"] == slot["id"]
        and summary["arm"] == slot["arm"] == "selected_maneuver"
        and summary["seed"] == 144
        and summary["max_actions"] == 66
        and summary["inference_bypassed"] is True,
        "summary_binding",
    )
    route = head["route"]
    check(route == geometry["route"], "route_identity")
    grouped = {}
    for row in rows:
        check(
            row["event"] in {"header", "reset", "actor", "action", "step", "runner_stop"},
            "unknown_event",
        )
        grouped.setdefault(row["event"], []).append(row)
    check(
        len(grouped["header"]) == len(grouped["reset"]) == len(grouped["runner_stop"]) == 1,
        "unique_boundaries",
    )
    reset = grouped["reset"][0]
    close(reset["state"], geometry["reset"], 0)
    close(reset["state"], selected["reset_state"], 0)
    check(reset["time"] == reset["info"]["timestamp"] == 0, "reset_clock")
    close(reset["info"]["obj_boxes"], geometry["obstacles"], 0)
    actions, steps = grouped.get("action", []), grouped.get("step", [])
    n = len(steps)
    check(
        type(summary["steps"]) is int
        and n == summary["steps"] == len(actions)
        and 1 <= n <= 66
        and len(summary["timings"]) == n,
        "step_inventory",
    )
    actors = [r["value"] for r in grouped["actor"] if r["value"]["event"] == "consume"]
    actor_reset = [r["value"] for r in grouped["actor"] if r["value"]["event"] == "reset"]
    check(
        len(actors) == n
        and len(actor_reset) == 1
        and actor_reset[0]["advanced"] is False
        and len(grouped["actor"]) == n + 1,
        "actor_inventory",
    )
    # This scene has one ConstantPlanner. Other actor families require a new qualified protocol.
    previous = reset["state"]
    scientific = []
    for i, (action, step, actor, timing) in enumerate(
        zip(actions, steps, actors, summary["timings"])
    ):
        check(
            reset["seq"] < action["seq"] < step["seq"]
            and (i == 0 or steps[i - 1]["seq"] < action["seq"]),
            "action_event_order",
        )
        check(
            type(action["frame"]) is int
            and action["frame"] == i
            and type(step["frame"]) is int
            and step["frame"] == i + 1,
            "action_index",
        )
        close(
            [action["time"], step["time"], actor["time"], step["info"]["timestamp"]],
            [i / 4, (i + 1) / 4, (i + 1) / 4, (i + 1) / 4],
            0,
        )
        check(set(action["applied"]) == {"acc", "steer_rate"}, "action_fields")
        applied = [action["applied"]["acc"], action["applied"]["steer_rate"]]
        close(applied, selected["actions"][i], 0)
        check(step["applied"] == action["applied"], "applied_action")
        close(action["before"], previous, 0)
        close(step["before"], previous, 0)
        close(step["after"], motion(previous, [applied])[1], 1e-9)
        close(step["after"], selected["expected_model_states"][i + 1], 1e-9)
        previous = step["after"]
        v, steer = previous[3:]
        yaw = v * math.tan(steer) / 2.7
        check(
            abs(applied[0]) <= 2
            and abs(applied[1]) <= math.pi / 12
            and 0 <= v <= 6
            and abs(steer) <= math.pi / 3
            and abs(yaw) <= 0.95
            and abs(v * yaw) <= 4.89,
            "control_screen",
        )
        info = step["info"]
        close(
            [info["ego_box"][0], info["ego_box"][1], info["ego_box"][6]],
            [previous[0], -previous[1], -previous[2]],
            1e-9,
        )
        close(info["ego_box"][3:6], geometry["ego_dimensions"], 0)
        distances = [math.hypot(p[0] - previous[1], p[1] - previous[0]) for p in route]
        nearest = min(range(len(route)), key=lambda j: (distances[j], j))
        rc, dist = (nearest + 1) / (0.9 * len(route)), distances[nearest]
        close([step["rc"], info["rc"], step["route_distance"]], [rc, rc, dist], 1e-9)
        check(
            step["nearest_index"] == nearest
            and step["route_samples"] == len(route)
            and step["final_sample_observed"] is (nearest == len(route) - 1),
            "route_index",
        )
        collision = step["collision_records"]
        check(
            [r["kind"] for r in collision] == ["background", "foreground"]
            and all(type(r["result"]) is bool and r["time"] == step["time"] for r in collision),
            "collision_inventory",
        )
        fg = collision[1]
        close(fg["ego_box"], info["ego_box"], 0)
        close(fg["objects"], info["obj_boxes"], 0)
        check(
            fg["result"] == any(overlap(fg["ego_box"], o) for o in fg["objects"]),
            "foreground_replay",
        )
        collided = any(r["result"] for r in collision)
        for k, expected in (
            ("collision", collided),
            ("off_route", dist > 10),
            ("source_completion", rc >= 1),
            ("terminated", collided or dist > 10 or rc >= 1),
            ("truncated", False),
        ):
            check(step[k] is expected, "source_outcome:" + k)
        check(info["collision"] is collided, "aggregate_collision")
        close(step["reward"], 1000 if rc >= 1 else -50 if dist > 10 else -100 if collided else 0, 0)
        check(i == n - 1 or not step["terminated"], "continued_after_terminal")
        check(set(actor["states"]) == set(actor["transforms"]) == {"agent_0"}, "actor_ids")
        close(
            actor["states"]["agent_0"], [-1.0499999523162842, 30.0, 0.2800000011920929, 0.0], 1e-9
        )
        matrix = actor["transforms"]["agent_0"]
        obj = info["obj_boxes"][0]
        check(len(info["obj_boxes"]) == 1, "actor_box_count")
        close(obj[:3], [matrix[2][3], -matrix[0][3], -matrix[1][3]], 0)
        angle = -math.atan2(matrix[0][2], matrix[2][2]) - math.pi / 2
        close([math.sin(obj[6]), math.cos(obj[6])], [math.sin(angle), math.cos(angle)], 1e-6)
        close(obj[3:6], geometry["obstacles"][0][3:6], 0)
        check(
            timing["frame"] == i
            and type(timing["full_loop_ns"]) is int
            and timing["full_loop_ns"] > 0,
            "loop_timing",
        )
        scientific.append(
            dict(
                time=step["time"],
                state=previous,
                action=applied,
                rc=rc,
                distance=dist,
                collision=collided,
                background=collision[0]["result"],
                foreground=fg["result"],
                actors=actor["states"],
                objects=info["obj_boxes"],
                terminated=step["terminated"],
            )
        )
    for row in [reset, *steps]:
        check(set(row["rgb"]) == CAMERAS, "camera_observation_count")
        for camera in row["rgb"].values():
            check(
                re.fullmatch("[0-9a-f]{64}", camera["sha256"]) is not None
                and len(camera["shape"]) == 3
                and camera["shape"][2] == 3
                and min(camera["shape"]) > 0
                and camera["dtype"] == "|u1",
                "rgb_identity",
            )
    reason = "source_terminal" if steps[-1]["terminated"] else "action_cap"
    check(reason == "source_terminal" or n == 66, "premature_stop")
    check(
        summary["stop_reason"] == reason
        and rows[-1]
        == dict(seq=len(rows) - 1, event="runner_stop", status="completed", reason=reason, steps=n),
        "stop_binding",
    )
    progress = {}
    for arm, ref in geometry["comparators"].items():
        row = next((r for r in scientific if r["time"] == ref["hazard_time"]), None)
        progress[arm] = None if row is None else row["rc"] + 0.05 >= ref["rc"]
    collided = any(r["collision"] for r in scientific)
    off = any(r["distance"] > 10 for r in scientific)
    outcome = dict(
        execution_valid=True,
        collision_observed=collided,
        off_route_observed=off,
        background_collision=any(r["background"] for r in scientific),
        foreground_collision=any(r["foreground"] for r in scientific),
        simulator_completion=steps[-1]["source_completion"],
        censored=reason != "source_terminal",
        completion_qualified=reason == "source_terminal"
        and not collided
        and not off
        and steps[-1]["source_completion"]
        and all(v is True for v in progress.values()),
        progress_checks=progress,
        road_compliance=None,
        information_benefit=None,
        first_failure_time=next(
            (r["time"] for r in scientific if r["collision"] or r["distance"] > 10), None
        ),
        final_sample_observed=steps[-1]["final_sample_observed"],
    )
    check(summary["outcome"] == outcome, "false_outcome_claim")
    return dict(
        status="supported",
        episode=slot["id"],
        steps=n,
        outcome=outcome,
        scientific=scientific,
        route=route,
        reset_state=reset["state"],
        model_stationarity_agreement=all(r["objects"] == geometry["obstacles"] for r in scientific),
    )


def verify_device(rows, summary, worker, slot):
    check(
        worker["status"] == "completed"
        and worker["gpu_observed"] is True
        and worker["inference_bypassed"] is True
        and worker["summary"] == summary
        and worker["slot"] == slot
        and worker["episode"] == slot["id"]
        and worker["purpose"] == "study"
        and worker["seed"] == 144,
        "gpu_identity",
    )
    check(
        worker["actor_types"] == {"agent_0": "ConstantPlanner"}
        and worker["geos"]
        and worker["torch"]
        and worker["cuda_device"],
        "runtime_identity",
    )
    check(worker["cleanup"]["status"] == "absent", "cleanup")
    actors = [
        r["value"] for r in rows if r["event"] == "actor" and r["value"]["event"] == "consume"
    ]
    steps = [r for r in rows if r["event"] == "step"]
    renders, collisions = worker["render_events"], worker["collision_events"]
    check(
        len(renders) == 6 * (len(steps) + 1) and len(collisions) == 2 * len(steps),
        "device_inventory",
    )
    check([r["index"] for r in renders] == list(range(len(renders))), "render_order")
    for tick in range(len(steps) + 1):
        cameras = [r for r in renders if r["time"] == tick / 4]
        check(len(cameras) == 6, "camera_tick_count")
        for camera in cameras:
            check(
                camera["device"].startswith("cuda")
                and camera["shape"] == [3, 450, 800]
                and type(camera["elapsed_ns"]) is int
                and camera["elapsed_ns"] > 0,
                "cuda_render",
            )
            if tick:
                close(camera["transforms"]["agent_0"], actors[tick - 1]["transforms"]["agent_0"], 0)
        if tick:
            observed = [r for r in collisions if r["time"] == tick / 4]
            check(len(observed) == 2, "collision_tick_count")
            for a, b in zip(observed, steps[tick - 1]["collision_records"]):
                check(
                    a["kind"] == b["kind"]
                    and type(a["result"]) is bool
                    and a["result"] == b["result"],
                    "collision_receipt",
                )
                if a["kind"] == "background":
                    check(
                        a["device"].startswith("cuda")
                        and type(a["points"]) is int
                        and a["points"] > 0,
                        "background_device",
                    )
                else:
                    close(a["ego_box"], b["ego_box"], 0)
                    close(a["objects"], b["objects"], 0)


def verify_case(directory, slot, selected, geometry, repository):
    directory = Path(directory)
    rows, summary = read(directory / "trace")
    result = verify(rows, summary, selected, geometry, slot)
    worker = strict((directory / "worker.json").read_bytes())
    verify_device(rows, summary, worker, slot)
    from .background_check import verify as verify_background

    background = verify_background(repository, rows, worker)
    result.update(
        gpu_observed=True,
        camera_calls=len(worker["render_events"]),
        actor_types=worker["actor_types"],
        inference_bypassed=True,
        background=background,
        background_replay_scope="Full retained population, actual source masks and scalar replay at every executed step",
    )
    return result
