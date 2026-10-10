"""Bounded single-reset driver shared by CPU qualification and prospective GPU smoke."""

import hashlib
import json
from pathlib import Path
import pickle
import signal
import stat
import time
import numpy as np
from .simulator import Session


def plain(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {k: plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    return value


def rgb_identity(observation):
    return {
        name: dict(
            sha256=hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest(),
            shape=list(array.shape),
            dtype=array.dtype.str,
        )
        for name, array in observation["rgb"].items()
    }


class PipeExchange:
    """Trusted, owned local FIFO pair. Never wait past the explicit exchange deadline."""

    def __init__(self, output, timeout_seconds=60):
        self.output, self.timeout_seconds = Path(output), timeout_seconds
        if not 0 < timeout_seconds <= 60:
            raise ValueError("pipe timeout")
        for name in ("obs_pipe", "plan_pipe"):
            mode = (self.output / name).lstat().st_mode
            if not stat.S_ISFIFO(mode):
                raise ValueError("non_fifo_transport")

    def __call__(self, observation, info):
        def timed_out(signum, frame):
            raise TimeoutError("planner_exchange_deadline")

        old = signal.signal(signal.SIGALRM, timed_out)
        signal.setitimer(signal.ITIMER_REAL, self.timeout_seconds)
        try:
            with (self.output / "obs_pipe").open("wb") as stream:
                pickle.dump((observation, info), stream)
            with (self.output / "plan_pipe").open("rb") as stream:
                raw = stream.read(1024**2 + 1)
            if len(raw) > 1024**2:
                raise ValueError("planner_packet_size")
            return pickle.loads(raw)
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, old)


def run(env, exchange, *, output, episode, max_steps, max_seconds, device="cuda"):
    """No retries. Host admission and owned client lifecycle must precede this call."""
    if type(max_steps) is not int or not 1 <= max_steps <= 12 or not 0 < max_seconds <= 1200:
        raise ValueError("smoke_envelope")
    directory = Path(output)
    directory.mkdir(exist_ok=False)
    session = None
    begun = time.monotonic()
    consumed = actor_consumed = 0
    summary = dict(
        status="running",
        episode=episode,
        max_steps=max_steps,
        max_seconds=max_seconds,
        gpu_observed=False,
        driving_outcome=None,
    )
    with (directory / "started.json").open("x") as stream:
        json.dump(summary, stream, indent=2)
    with (directory / "events.jsonl").open("x") as stream:

        def record(value):
            stream.write(json.dumps(plain(value), sort_keys=True, allow_nan=False) + "\n")
            stream.flush()

        def flush_events():
            nonlocal consumed, actor_consumed
            if session is None:
                return
            for value in session.events[consumed:]:
                record(value)
            consumed = len(session.events)
            for value in env.planner.events[actor_consumed:]:
                record(dict(event="actor", value=value))
            actor_consumed = len(env.planner.events)

        try:
            session = Session(env, episode, device=device)
            obs, info = session.reset()
            initialization_seconds = time.monotonic() - begun
            summary["reset_seconds"] = initialization_seconds
            flush_events()
            for frame in range(max_steps):
                if time.monotonic() - begun >= max_seconds:
                    session.stop("episode_deadline")
                    break
                request_info = dict(info, sentinel_episode=episode, sentinel_frame=frame)
                record(
                    dict(
                        event="observation",
                        frame=frame,
                        time=info["timestamp"],
                        rgb=rgb_identity(obs),
                        info=info,
                    )
                )
                exchange_start = time.monotonic()
                delivery = exchange(obs, request_info)
                record(
                    dict(
                        event="delivery",
                        frame=frame,
                        exchange_seconds=time.monotonic() - exchange_start,
                        value=delivery,
                    )
                )
                if time.monotonic() - begun >= max_seconds:
                    session.stop("episode_deadline_after_delivery")
                    break
                obs, _, terminated, truncated, info = session.step(delivery)
                flush_events()
                if time.monotonic() - begun >= max_seconds:
                    session.stop("episode_deadline_after_step")
                    break
                if terminated or truncated:
                    break
            if not session.stopped:
                session.stop("smoke_step_cap")
            summary.update(status="completed", stop_reason=session.stopped, steps=session.frame)
        except Exception as exc:
            if session is not None and not session.stopped:
                session.stop(f"{type(exc).__name__}:{exc}")
            summary.update(
                status="failed",
                stop_reason=session.stopped
                if session
                else f"initialization:{type(exc).__name__}:{exc}",
                steps=session.frame if session else 0,
            )
        finally:
            flush_events()
            summary["elapsed_seconds"] = time.monotonic() - begun
            summary["events_sha256"] = hashlib.sha256(
                (directory / "events.jsonl").read_bytes()
            ).hexdigest()
            with (directory / "summary.json").open("x") as final:
                json.dump(summary, final, indent=2, allow_nan=False)
                final.write("\n")
    return summary
