"""Direct fixed actions; native scene observations and terminal conditions remain authoritative."""

import json
from pathlib import Path
import time

import numpy as np

from experiments.iter145_constrained_execution.driver import plain, rgb_identity
from experiments.iter145_constrained_execution.simulator import (
    TimedPlanner,
    check_runtime,
    ego_state,
)
from experiments.iter146_route_outcome_contract.runner import (
    Journal,
    route_record,
    observe_collisions,
)
from .contract import action_at, near, require


def classify(rows, reason, status):
    complete = bool(rows and rows[-1]["source_completion"])
    valid = status == "completed"
    collision = any(r["collision"] for r in rows) if rows else None
    off = any(r["off_route"] for r in rows) if rows else None
    progress = {}
    for name, reference in (
        ("nominal", (7.75, 0.32925097621583244)),
        ("monitor", (9.0, 0.32215122470713525)),
    ):
        row = next((r for r in rows if r["time"] == reference[0]), None)
        progress[name] = None if row is None else row["rc"] + 0.05 >= reference[1]
    return dict(
        execution_valid=valid,
        collision_observed=collision,
        off_route_observed=off,
        background_collision=any(r["collision_records"][0]["result"] for r in rows)
        if rows
        else None,
        foreground_collision=any(r["collision_records"][1]["result"] for r in rows)
        if rows
        else None,
        simulator_completion=complete if rows else None,
        censored=reason != "source_terminal",
        completion_qualified=valid
        and reason == "source_terminal"
        and collision is False
        and off is False
        and complete
        and all(v is True for v in progress.values()),
        progress_checks=progress,
        road_compliance=None,
        information_benefit=None,
        first_failure_time=next(
            (r["time"] for r in rows if r["collision"] or r["off_route"]), None
        ),
        final_sample_observed=rows[-1]["final_sample_observed"] if rows else None,
    )


def run(
    env, *, output, slot, selected, geometry, max_seconds=1100, device="cuda", guard=lambda: None
):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter_ns()
    log = Journal(output / "events.jsonl")
    summary = dict(
        schema="sentinel.iter154.summary.v1",
        status="running",
        episode=slot["id"],
        arm=slot["arm"],
        seed=slot["seed"],
        max_actions=65,
        steps=0,
        stop_reason=None,
        inference_bypassed=True,
        timings=[],
    )
    (output / "started.json").write_text(json.dumps(summary, indent=2) + "\n")
    outcomes, collisions = [], []

    def actors():
        for event in env.planner.events:
            log.write(dict(event="actor", value=event))
        env.planner.events.clear()

    try:
        require(
            slot["arm"] == "selected_maneuver"
            and slot["seed"] == 144
            and slot["max_actions"] == 65
            and slot["reset_count"] == 1,
            "slot_contract",
        )
        guard()
        check_runtime(env)
        require(
            env.timestamp == 0 and env.last_accel == 0 and env.last_steer_rate == 0,
            "environment_not_fresh",
        )
        route = route_record(env)
        require(route == geometry["route"], "source_route_mismatch")
        env.planner = TimedPlanner(env.planner, slot["id"], device=device)
        env.steer = float(env.kinematic["start_steer"])
        env.last_accel = env.last_steer_rate = 0.0
        log.write(
            dict(
                event="header",
                schema="sentinel.iter154.trace.v1",
                slot=slot,
                route=route,
                selected_candidate=selected["candidate"]["id"],
                inference_bypassed=True,
            )
        )
        with observe_collisions(env, collisions):
            obs, info = env.reset()
            near(ego_state(env), selected["reset_state"], 0)
            require(info["timestamp"] == env.timestamp == 0, "reset_clock")
            require(plain(info["obj_boxes"]) == geometry["obstacles"], "reset_actor_geometry")
            near(plain(info["ego_box"])[3:6], geometry["ego_dimensions"], 0)
            log.write(
                dict(
                    event="reset", time=0.0, state=ego_state(env), info=info, rgb=rgb_identity(obs)
                )
            )
            actors()
            for frame in range(65):
                loop = time.perf_counter_ns()
                guard()
                require((loop - started) / 1e9 < max_seconds, "runner_deadline")
                require(
                    env.timestamp == info["timestamp"] == frame / 4 and env.planner.tick == frame,
                    "action_clock",
                )
                check_runtime(env)
                before = ego_state(env)
                action = action_at(selected, frame, before)
                log.write(
                    dict(event="action", frame=frame, time=frame / 4, before=before, applied=action)
                )
                collisions.clear()
                obs, reward, terminated, truncated, info = env.step(action)
                after = ego_state(env)
                near(after, selected["expected_model_states"][frame + 1])
                require(type(terminated) is bool and type(truncated) is bool, "terminal_type")
                require(
                    env.timestamp == info["timestamp"] == (frame + 1) / 4
                    and env.planner.tick == frame + 1,
                    "observation_clock",
                )
                require(plain(info["obj_boxes"]) == plain(env.objs_list), "observation_actor_state")
                require(
                    [r["kind"] for r in collisions] == ["background", "foreground"]
                    and all(r["time"] == env.timestamp for r in collisions),
                    "collision_inventory",
                )
                require(
                    type(info["collision"]) in (bool, np.bool_)
                    and bool(info["collision"]) == any(r["result"] for r in collisions),
                    "collision_aggregate",
                )
                rc, distance = env.route_completion
                nearest = int(np.argmin(np.sum((np.asarray(route) - env.vab) ** 2, axis=1)))
                row = dict(
                    event="step",
                    frame=frame + 1,
                    time=float(env.timestamp),
                    before=before,
                    applied=action,
                    after=after,
                    info=info,
                    rgb=rgb_identity(obs),
                    rc=float(rc),
                    route_distance=float(distance),
                    nearest_index=nearest,
                    route_samples=len(route),
                    final_sample_observed=nearest == len(route) - 1,
                    source_completion=bool(rc >= 1),
                    off_route=bool(distance > 10),
                    collision=bool(info["collision"]),
                    collision_records=collisions.copy(),
                    terminated=terminated,
                    truncated=truncated,
                    reward=float(reward),
                )
                actors()
                log.write(row)
                outcomes.append(row)
                summary["steps"] = frame + 1
                guard()
                summary["timings"].append(
                    dict(frame=frame, full_loop_ns=time.perf_counter_ns() - loop)
                )
                if terminated or truncated:
                    summary["stop_reason"] = "source_truncated" if truncated else "source_terminal"
                    break
            else:
                summary["stop_reason"] = "action_cap"
            summary["status"] = "completed"
    except Exception as exc:
        summary.update(status="failed", stop_reason=f"{type(exc).__name__}:{exc}")
    finally:
        log.write(
            dict(
                event="runner_stop",
                status=summary["status"],
                reason=summary["stop_reason"],
                steps=summary["steps"],
            )
        )
        log.stream.close()
        summary.update(
            events_sha256=log.digest.hexdigest(),
            events_bytes=log.size,
            elapsed_ns=time.perf_counter_ns() - started,
            outcome=classify(outcomes, summary["stop_reason"], summary["status"]),
        )
        (output / "summary.json").write_text(
            json.dumps(plain(summary), indent=2, allow_nan=False) + "\n"
        )
    return summary
