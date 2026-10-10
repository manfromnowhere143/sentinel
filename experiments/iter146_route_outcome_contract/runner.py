"""Finite route runner over the retained Iter145 controller and environment adapter."""

from contextlib import contextmanager
import hashlib
import json
import math
from pathlib import Path
import time

import numpy as np

from experiments.iter145_constrained_execution.driver import plain, rgb_identity
from experiments.iter145_constrained_execution.simulator import Session

ARMS = ("nominal", "monitor", "brake_t0", "brake_t2_5")
MAX_TRACE = 256 * 1024**2
MAX_EVENT = 4 * 1024**2


class Journal:
    def __init__(self, path, limit=MAX_TRACE):
        self.stream = Path(path).open("xb")
        self.limit, self.size, self.sequence = limit, 0, 0
        self.digest = hashlib.sha256()

    def write(self, event):
        raw = (
            json.dumps(
                dict(seq=self.sequence, **plain(event)),
                sort_keys=True,
                allow_nan=False,
                separators=(",", ":"),
            )
            + "\n"
        ).encode()
        if len(raw) > MAX_EVENT or self.size + len(raw) > self.limit:
            raise ValueError("trace_resource_limit")
        self.stream.write(raw)
        self.stream.flush()
        self.digest.update(raw)
        self.size += len(raw)
        self.sequence += 1


def route_record(env):
    points = np.asarray(env.ground_model[0])[:, [0, 2], 3]
    if points.ndim != 2 or points.shape[1] != 2 or not 2 <= len(points) <= 100000:
        raise ValueError("route_shape")
    if not np.isfinite(points).all():
        raise ValueError("route_nonfinite")
    return points.tolist()


@contextmanager
def observe_collisions(env, records):
    """Call the original functions exactly once and retain each separate result."""
    namespace = env.step.__func__.__globals__
    originals = {name: namespace[name] for name in ("bg_collision_det", "fg_collision_det")}

    def wrap(kind, original):
        def call(*args):
            result = original(*args)
            if not isinstance(result, (bool, np.bool_)):
                raise ValueError("collision_result_type")
            row = dict(kind=kind, time=float(env.timestamp), result=bool(result))
            if kind == "foreground":
                row.update(ego_box=plain(args[0]), objects=plain(args[1]))
            records.append(row)
            return result

        return call

    namespace["bg_collision_det"] = wrap("background", originals["bg_collision_det"])
    namespace["fg_collision_det"] = wrap("foreground", originals["fg_collision_det"])
    try:
        yield
    finally:
        namespace.update(originals)


def run(
    env,
    exchange,
    *,
    output,
    episode,
    arm,
    monitor_reader,
    max_actions=401,
    max_seconds=120,
    device="cpu",
    clock=time.perf_counter_ns,
    guard=lambda: None,
):
    if (
        arm not in ARMS
        or not isinstance(episode, str)
        or not episode
        or type(max_actions) is not int
        or not 1 <= max_actions <= 401
        or type(max_seconds) not in (int, float)
        or not math.isfinite(max_seconds)
        or not 0 < max_seconds <= 3600
    ):
        raise ValueError("run_envelope")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    started = clock()
    log = Journal(output / "events.jsonl")
    summary = dict(
        schema="sentinel.iter146.summary.v2",
        status="running",
        episode=episode,
        arm=arm,
        seed=144,
        max_actions=max_actions,
        max_seconds=max_seconds,
        steps=0,
        stop_reason=None,
        outcome=None,
        live_study_admitted=False,
        timings=[],
        timing_scope=(
            "Elapsed-clock boundaries relative to runner entry. loop_work_ns ends after trace "
            "flush; full_loop_ns also includes the post-step resource guard and stop decision. "
            "Both exclude timing-list append, Python loop dispatch and final summary writing."
        ),
    )
    (output / "started.json").write_text(json.dumps(summary, indent=2) + "\n")
    session = None
    collision_records = []
    terminals = []

    def flush():
        if session is None:
            return
        for event in session.events:
            log.write(event)
        session.events.clear()
        for event in env.planner.events:
            log.write(dict(event="actor", value=event))
        env.planner.events.clear()

    def expired():
        return clock() - started >= max_seconds * 1e9

    try:
        guard()
        route = route_record(env)
        log.write(
            dict(
                event="header",
                schema="sentinel.iter146.trace.v1",
                episode=episode,
                arm=arm,
                seed=144,
                max_actions=max_actions,
                route=route,
            )
        )
        with observe_collisions(env, collision_records):
            session = Session(env, episode, device=device)
            obs, info = session.reset()
            flush()
            for frame in range(max_actions):
                loop_start = clock()
                guard()
                if expired():
                    summary["stop_reason"] = "wall_deadline_before_exchange"
                    break
                log.write(
                    dict(
                        event="observation",
                        frame=frame,
                        time=info["timestamp"],
                        rgb=rgb_identity(obs),
                        info=info,
                    )
                )
                exchange_start = clock()
                delivery = exchange(obs, dict(info, sentinel_episode=episode, sentinel_frame=frame))
                exchange_ns = clock() - exchange_start
                if delivery.get("mode") != arm:
                    raise ValueError("arm_delivery_mismatch")
                log.write(
                    dict(event="delivery", frame=frame, exchange_ns=exchange_ns, value=delivery)
                )
                line = monitor_reader(frame)
                if not isinstance(line, bytes) or not 0 < len(line) <= 1024**2:
                    raise ValueError("monitor_record_boundary")
                log.write(dict(event="monitor", frame=frame, raw=line.decode("utf-8")))
                if expired():
                    summary["stop_reason"] = "wall_deadline_after_exchange"
                    break
                collision_records.clear()
                obs, reward, terminated, truncated, info = session.step(delivery)
                if type(terminated) is not bool or type(truncated) is not bool:
                    raise ValueError("terminal_flag_type")
                rc, distance = env.route_completion
                p = np.asarray(route)
                nearest = int(np.argmin(np.sum((p - env.vab) ** 2, axis=1)))
                terminal = dict(
                    event="outcome_observation",
                    frame=frame + 1,
                    time=env.timestamp,
                    rc=float(rc),
                    nearest_index=nearest,
                    route_samples=len(route),
                    route_distance=float(distance),
                    final_sample_observed=nearest == len(route) - 1,
                    off_route=bool(distance > 10),
                    source_completion=bool(rc >= 1),
                    collision=bool(info["collision"]),
                    collision_records=collision_records.copy(),
                    terminated=terminated,
                    truncated=truncated,
                    reward=float(reward),
                )
                if (
                    not math.isfinite(terminal["rc"])
                    or not math.isfinite(terminal["route_distance"])
                    or [r["kind"] for r in collision_records] != ["background", "foreground"]
                    or any(r["time"] != env.timestamp for r in collision_records)
                    or terminal["collision"] != any(r["result"] for r in collision_records)
                ):
                    raise ValueError("outcome_boundary")
                flush()
                log.write(terminal)
                terminals.append(terminal)
                summary["steps"] = frame + 1
                work_end = clock()
                try:
                    guard()
                    if expired():
                        summary["stop_reason"] = "wall_deadline_after_step"
                    elif terminated or truncated:
                        summary["stop_reason"] = (
                            "source_truncated" if truncated else "source_terminal"
                        )
                finally:
                    loop_end = clock()
                    summary["timings"].append(
                        dict(
                            frame=frame,
                            exchange_ns=exchange_ns,
                            loop_start_ns=loop_start - started,
                            loop_work_end_ns=work_end - started,
                            loop_end_ns=loop_end - started,
                            loop_work_ns=work_end - loop_start,
                            full_loop_ns=loop_end - loop_start,
                        )
                    )
                if summary["stop_reason"] is not None:
                    break
            else:
                summary["stop_reason"] = "action_cap"
            summary["status"] = "completed"
    except Exception as exc:
        summary.update(status="failed", stop_reason=f"{type(exc).__name__}:{exc}")
    finally:
        try:
            flush()
            log.write(
                dict(
                    event="runner_stop",
                    reason=summary["stop_reason"],
                    status=summary["status"],
                    steps=summary["steps"],
                )
            )
        except Exception as exc:
            summary.update(
                status="failed", stop_reason=f"trace_finalize:{type(exc).__name__}:{exc}"
            )
        log.stream.close()
        summary.update(
            elapsed_ns=clock() - started,
            events_sha256=log.digest.hexdigest(),
            events_bytes=log.size,
        )
        summary["outcome"] = classify(terminals, summary["stop_reason"], summary["status"])
        (output / "summary.json").write_text(
            json.dumps(summary, sort_keys=True, indent=2, allow_nan=False) + "\n"
        )
    return summary


def classify(rows, reason, status):
    """Observed failures remain visible under censoring; unknown is never zero."""
    valid = status == "completed"
    censored = reason != "source_terminal"
    collision = any(r["collision"] for r in rows) if rows else None
    off_route = any(r["off_route"] for r in rows) if rows else None
    completion = bool(rows and rows[-1]["source_completion"])
    return dict(
        collision_observed=collision,
        off_route_observed=off_route,
        simulator_completion=completion if rows else None,
        completion_qualified=valid
        and not censored
        and collision is False
        and off_route is False
        and completion,
        censored=censored,
        execution_valid=valid,
        first_failure_time=next(
            (r["time"] for r in rows if r["collision"] or r["off_route"]), None
        ),
        final_sample_observed=rows[-1]["final_sample_observed"] if rows else None,
    )
