"""Versioned, explicit simulation-time trajectories. No simulator globals or I/O."""

from bisect import bisect_left
from dataclasses import dataclass
import hashlib
import json
import math

SCHEMA = "sentinel.timed_trajectory.v1"
FRAME = "hugsim.local_ab.heading_from_positive_a_toward_b"
UNITS = ("s", "m", "m", "rad", "m/s")
DT = 0.25
N = 20


class ContractError(ValueError):
    """Invalid records stop execution; callers retain this reason."""


def scalar(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ContractError("nonfinite_or_missing_scalar")
    return float(value)


def state4(state):
    if len(state) != 4:
        raise ContractError("state_shape")
    return tuple(scalar(x) for x in state)


def angle(value):
    return (value + math.pi) % (2 * math.pi) - math.pi


def actor_to_common(state):
    a, b, yaw, speed = state4(state)
    return (a, b, angle(yaw + math.pi / 2), speed)


def common_to_actor(state):
    a, b, heading, speed = state4(state)
    return (a, b, angle(heading - math.pi / 2), speed)


def ego_to_common(state):
    a, b, theta, speed = state4(state)
    return (a, b, angle(math.pi / 2 - theta), speed)


def same_state(a, b, tolerance=1e-8):
    return (
        max(abs(a[0] - b[0]), abs(a[1] - b[1]), abs(angle(a[2] - b[2])), abs(a[3] - b[3]))
        <= tolerance
    )


@dataclass(frozen=True)
class Trajectory:
    episode: str
    owner: str
    origin: float
    times: tuple
    states: tuple
    branch: str
    source_rows: tuple = ()
    schema: str = SCHEMA
    frame: str = FRAME
    units: tuple = UNITS

    def __post_init__(self):
        if self.schema != SCHEMA or self.frame != FRAME or self.units != UNITS:
            raise ContractError("schema_frame_or_units")
        if not all(isinstance(x, str) and x for x in (self.episode, self.owner, self.branch)):
            raise ContractError("missing_identity")
        object.__setattr__(self, "origin", scalar(self.origin))
        times = tuple(scalar(t) for t in self.times)
        states = tuple(state4(s) for s in self.states)
        if len(times) < 2 or len(times) != len(states):
            raise ContractError("time_state_cardinality")
        if times[0] != self.origin or any(b <= a for a, b in zip(times, times[1:])):
            raise ContractError("time_grid")
        object.__setattr__(self, "times", times)
        object.__setattr__(self, "states", states)
        object.__setattr__(
            self, "source_rows", tuple(tuple(scalar(x) for x in r) for r in self.source_rows)
        )

    def record(self):
        return dict(
            schema=self.schema,
            frame=self.frame,
            units=self.units,
            episode=self.episode,
            owner=self.owner,
            origin=self.origin,
            times=self.times,
            states=self.states,
            branch=self.branch,
            source_rows=self.source_rows,
        )

    @property
    def identity(self):
        return hashlib.sha256(
            json.dumps(
                self.record(), sort_keys=True, separators=(",", ":"), allow_nan=False
            ).encode()
        ).hexdigest()

    def at(self, time):
        time = scalar(time)
        if time < self.times[0] or time > self.times[-1]:
            raise ContractError("unsupported_extrapolation")
        i = bisect_left(self.times, time)
        if self.times[i] == time:
            return self.states[i]
        fraction = (time - self.times[i - 1]) / (self.times[i] - self.times[i - 1])
        lo, hi = self.states[i - 1], self.states[i]
        out = [lo[k] + fraction * (hi[k] - lo[k]) for k in range(4)]
        out[2] = angle(lo[2] + fraction * angle(hi[2] - lo[2]))
        return tuple(out)

    def aligned(self):
        times = tuple(self.origin + i * DT for i in range(N))
        return Trajectory(
            self.episode,
            self.owner,
            self.origin,
            times,
            tuple(self.at(t) for t in times),
            self.branch,
            self.source_rows,
        )


def constant_motion(initial, origin, episode, owner, branch="constant_forecast"):
    a, b, heading, speed = state4(initial)
    times = tuple(scalar(origin) + i * DT for i in range(N))
    states = tuple(
        (
            a + speed * math.cos(heading) * i * DT,
            b + speed * math.sin(heading) * i * DT,
            heading,
            speed,
        )
        for i in range(N)
    )
    return Trajectory(episode, owner, origin, times, states, branch)


def from_source(rows, initial, origin, episode, owner):
    """Pinned Pplan [a,b,v,acc,heading,yaw_rate,relative_seconds], excluding t0."""
    initial = state4(initial)
    rows = tuple(tuple(scalar(x) for x in r) for r in rows)
    if len(rows) != N - 1 or any(len(r) != 7 for r in rows):
        raise ContractError("source_shape_or_dropped_time_channel")
    offsets = tuple(r[6] for r in rows)
    branch = None
    for name, interval in [("spline", 5 / (N - 1)), ("low_speed", 5 / N)]:
        if all(abs(t - i * interval) <= 1e-6 for i, t in enumerate(offsets, 1)):
            branch = name
            break
    if branch is None:
        raise ContractError("shifted_or_unknown_source_time_grid")
    # Source float32 knots can round by <1e-6; preserve them without extrapolating.
    times = (scalar(origin),) + tuple(origin + t for t in offsets)
    states = (initial,) + tuple((r[0], r[1], angle(r[4]), r[2]) for r in rows)
    return Trajectory(episode, owner, origin, times, states, branch, rows).aligned()


def costs(candidates, ego, neighbors):
    if not candidates:
        raise ContractError("empty_candidate_set")
    grid = tuple(ego.origin + i * DT for i in range(N))
    trajectories = [*candidates, ego, *neighbors]
    if any(
        t.episode != ego.episode or t.origin != ego.origin or t.times != grid for t in trajectories
    ):
        raise ContractError("cost_time_or_episode_mismatch")
    result = []
    for candidate in candidates:
        attack = min(
            math.hypot(a[0] - b[0], a[1] - b[1]) for a, b in zip(candidate.states, ego.states)
        )
        near = sum(
            min(math.hypot(a[0] - b[0], a[1] - b[1]) for a, b in zip(candidate.states, n.states))
            < 2
            for n in neighbors
        )
        result.append(attack + 0.1 * near)
    return result


class Executor:
    """Single episode, integer ticks; no pointer inferred from array index alone."""

    def __init__(self, episode, owner, initial):
        if not episode or not owner:
            raise ContractError("missing_identity")
        self.episode, self.owner = episode, owner
        self.state = state4(initial)
        self.tick = 0
        self.plan = None
        self.events = [dict(event="reset", time=0.0, state=self.state, advanced=False)]

    @property
    def time(self):
        return self.tick * DT

    @property
    def needs_plan(self):
        return self.plan is None or self.time - self.plan.origin >= 10 * DT

    def install(self, plan):
        if plan.episode != self.episode or plan.owner != self.owner:
            raise ContractError("plan_identity")
        if plan.origin != self.time or plan.times != tuple(self.time + i * DT for i in range(N)):
            raise ContractError("stale_or_unaligned_plan")
        if not same_state(plan.states[0], self.state):
            raise ContractError("reset_or_replan_state_discontinuity")
        self.plan = plan
        self.events.append(
            dict(event="install", time=self.time, plan_id=plan.identity, branch=plan.branch)
        )

    def advance(self, target_time):
        if scalar(target_time) != (self.tick + 1) * DT:
            raise ContractError("repeated_skipped_or_shifted_tick")
        if self.needs_plan:
            raise ContractError("stale_or_missing_plan")
        value = self.plan.at(target_time)
        self.state = value
        self.tick += 1
        self.events.append(
            dict(
                event="consume",
                time=self.time,
                plan_id=self.plan.identity,
                plan_origin=self.plan.origin,
                state=value,
            )
        )
        return value
