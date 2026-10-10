"""Bounded actor dispatch bridge and control application for the new regime."""

import torch
from .trajectory import (
    ContractError,
    DT,
    Executor,
    actor_to_common,
    common_to_actor,
    constant_motion,
    costs,
    ego_to_common,
    from_source,
)
from .control import transition


class ActorWorld:
    """Synchronous pre-step forecasts; explicit ego identity, no index-based exclusion."""

    def __init__(self, episode, actors, samplers):
        if set(actors) != set(samplers) or "ego" in actors:
            raise ContractError("actor_sampler_identity")
        self.episode = episode
        self.executors = {
            name: Executor(episode, name, actor_to_common(state)) for name, state in actors.items()
        }
        self.samplers = samplers
        self.tick = 0
        self.selections = []
        self.stop_reason = None
        self.reset_seen = False

    def plan_traj(self, target_time, ego_native):
        """Compatible timing boundary with HUGSIM step prefix; returns CPU native states.

        This deliberately does not pretend to supply CUDA render transforms.
        Full simulator wiring remains a separate deployment qualification.
        """
        try:
            return self._dispatch(target_time, ego_native)
        except (ValueError, RuntimeError) as exc:
            self.stop_reason = f"{type(exc).__name__}:{exc}"
            raise

    def _dispatch(self, target_time, ego_native):
        if self.stop_reason:
            raise ContractError("world_already_stopped")
        if target_time == 0 and self.tick == 0 and not self.reset_seen:
            self.reset_seen = True
            return {name: common_to_actor(e.state) for name, e in self.executors.items()}
        if not self.reset_seen or target_time != (self.tick + 1) * DT:
            raise ContractError("world_reset_or_tick")
        now = self.tick * DT
        ego = constant_motion(ego_to_common(ego_native), now, self.episode, "ego")
        forecasts = {
            name: constant_motion(e.state, now, self.episode, name)
            for name, e in self.executors.items()
        }
        pending = []
        for name, executor in self.executors.items():
            if not executor.needs_plan:
                continue
            state = executor.state
            if state[3] < 0:
                raise ContractError("reverse_actor_origin_unqualified")
            x0 = torch.tensor([state[0], state[1], state[3], state[2]], dtype=torch.float64)
            rows, _ = self.samplers[name].gen_trajectories(x0, 5.0, lanes=None, dyn_filter=True)
            candidates = [from_source(r, state, now, self.episode, name) for r in rows.tolist()]
            if not candidates:
                candidates = [constant_motion(state, now, self.episode, name, "fallback")]
            # Source intention is at most three nearest neighbors including ego. Remove
            # ego by identity, never by assuming its sorted position.
            ordered = sorted(
                [(ego.owner, ego), *forecasts.items()],
                key=lambda pair: (
                    (pair[1].states[0][0] - state[0]) ** 2 + (pair[1].states[0][1] - state[1]) ** 2,
                    pair[0],
                ),
            )
            nearest = [p for p in ordered if p[0] != name][:3]
            neighbors = [p[1] for p in nearest if p[0] != "ego"]
            values = costs(candidates, ego, neighbors)
            selected = min(range(len(values)), key=lambda i: (values[i], i))
            pending.append((executor, candidates[selected]))
            self.selections.append(
                dict(
                    time=now,
                    actor=name,
                    ego=ego.record(),
                    neighbors=[n.record() for n in neighbors],
                    candidates=[t.record() for t in candidates],
                    costs=values,
                    selected=selected,
                    tie_policy="lowest_index",
                )
            )
        for executor, plan in pending:
            executor.install(plan)
        result = {
            name: common_to_actor(e.advance(target_time)) for name, e in self.executors.items()
        }
        self.tick += 1
        return result


def apply_step(env, requested, source_step):
    """Validate/project action then invoke the actual retained environment step prefix."""
    state = [
        float(env.vab[1]),
        float(env.vab[0]),
        float(env.vr[1]),
        float(env.velo),
        float(env.steer),
    ]
    predicted, applied, _, _ = transition(state, requested)
    record = dict(
        observation_time=float(env.timestamp),
        application_time=float(env.timestamp + DT),
        before=state,
        requested=list(requested),
        applied=applied.tolist(),
        predicted=predicted.tolist(),
    )
    if env.dt != DT:
        raise ContractError("environment_dt")
    source_step(env, dict(acc=float(applied[0]), steer_rate=float(applied[1])))
    record["after"] = [
        float(env.vab[1]),
        float(env.vab[0]),
        float(env.vr[1]),
        float(env.velo),
        float(env.steer),
    ]
    return record
