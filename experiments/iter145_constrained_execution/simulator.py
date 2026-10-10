"""Full environment boundary; original GPU renderer/collision methods remain called."""

import math
import time
import numpy as np
import torch
from scipy.spatial.transform import Rotation
from experiments.iter144_timed_trajectory.trajectory import (
    ContractError, DT, Executor, actor_to_common, common_to_actor, constant_motion,
    costs, ego_to_common, from_source, scalar, state4,
)
from .optimizer import ConstrainedController, require_action, rollout
from .independent import certificate as replay_certificate
from .nominal import reference


class TimedPlanner:
    """Adapt the actual source-created planner, preserving assets and source actor objects."""

    def __init__(self, original, episode, *, device):
        self.original, self.episode, self.device = original, episode, device
        self.tick, self.reset_seen, self.stop_reason = 0, False, None
        self.events, self.executors = [], {}
        if original.dt != DT or original.PREDICT_STEPS != 20 or original.NUM_NEIGHBORS != 3:
            raise ContractError("planner_constants")
        for name, controller in original.controller.items():
            kind = type(controller).__name__
            if kind not in ("AttackPlanner", "ConstantPlanner", "IDM", "UnicyclePlanner"):
                raise ContractError("unknown_actor_type:" + kind)
            if kind == "AttackPlanner":
                if controller.best_k != 1 or controller.predict_steps != 20:
                    raise ContractError("attack_sampler_configuration")
                if controller.exec_traj is not None or controller.exec_pointer != 1:
                    raise ContractError("actor_not_fresh")
                self.executors[name] = Executor(episode, name, self.common(name))
            if kind == "UnicyclePlanner":
                if controller.t != 0 or not math.isfinite(float(controller.speed)) or controller.speed <= 0:
                    raise ContractError("unicycle_clock")
                self.unicycle_support(controller, 0.0)
            if kind == "IDM" and original.route[name] is None:
                raise ContractError("idm_route_unavailable")

    def __getattr__(self, name):
        return getattr(self.original, name)

    def native(self, name):
        return state4([float(x) for x in self.stats[name][[0, 1, 3, 4]]])

    def common(self, name):
        value = self.native(name)
        return value if type(self.controller[name]).__name__ == "UnicyclePlanner" else actor_to_common(value)

    @staticmethod
    def unicycle_support(controller, t):
        support = controller.uc_model.train_timestamp.detach().cpu().numpy()
        if (support.ndim != 1 or len(support) < 2 or not np.isfinite(support).all()
                or not np.all(np.diff(support) > 0) or not support[0] <= t <= support[-1]):
            raise ContractError("unicycle_unsupported_time")

    def transforms(self):
        transforms = {}
        for name, stat in self.stats.items():
            a, b, yaw, _ = self.native(name)
            unicycle = type(self.controller[name]).__name__ == "UnicyclePlanner"
            rotation = -yaw if unicycle else -yaw - math.pi / 2 - self.rectify_angle
            matrix = np.eye(4)
            matrix[:3, :3] = Rotation.from_euler("y", rotation).as_matrix()
            height = scalar(float(self.ground_height(a, b))) + scalar(float(stat[2]))
            matrix[:3, 3] = [a, height, b]
            transforms[name] = torch.tensor(matrix, dtype=torch.float32, device=self.device)
        return [transforms, {}]

    def plan_traj(self, target_time, ego_stats):
        try:
            return self._step(scalar(float(target_time)), ego_stats)
        except Exception as exc:
            self.stop_reason = f"{type(exc).__name__}:{exc}"
            self.events.append(dict(event="stopped", time=target_time, reason=self.stop_reason))
            raise

    def _step(self, target_time, ego_stats):
        if self.stop_reason:
            raise ContractError("planner_already_stopped")
        if target_time == 0 and not self.reset_seen:
            self.reset_seen = True
            self.events.append(dict(event="reset", time=0.0, advanced=False))
            return self.transforms()
        if not self.reset_seen or target_time != (self.tick + 1) * DT:
            raise ContractError("planner_reset_or_tick")
        now = self.tick * DT
        ego = constant_motion(ego_to_common([float(x) for x in ego_stats]), now, self.episode, "ego")
        forecasts = {name: constant_motion(self.common(name), now, self.episode, name) for name in self.stats}
        pending = {}
        for name, controller in self.controller.items():
            kind = type(controller).__name__
            state = self.common(name)
            ordered = sorted([(ego.owner, ego), *forecasts.items()], key=lambda p: (
                (p[1].states[0][0] - state[0]) ** 2 + (p[1].states[0][1] - state[1]) ** 2, p[0]))
            neighbors = [p for p in ordered if p[0] != name][:3]
            if kind == "AttackPlanner":
                executor = self.executors[name]
                if executor.needs_plan:
                    if state[3] < 0:
                        raise ContractError("reverse_actor_origin_unqualified")
                    x0 = torch.tensor([state[0], state[1], state[3], state[2]], dtype=torch.float32, device=controller.device)
                    rows, _ = controller.planner.gen_trajectories(x0, 5.0, lanes=None, dyn_filter=True)
                    candidates = [from_source(row, state, now, self.episode, name) for row in rows.detach().cpu().tolist()]
                    if not candidates:
                        candidates = [constant_motion(state, now, self.episode, name, "fallback")]
                    values = costs(candidates, ego, [p[1] for p in neighbors if p[0] != "ego"])
                    selected = min(range(len(values)), key=lambda i: (values[i], i))
                    executor.install(candidates[selected])
                    self.events.append(dict(event="select", actor=name, time=now, candidates=[p.record() for p in candidates],
                                            ego=ego.record(), neighbors=[p[1].record() for p in neighbors if p[0] != "ego"],
                                            costs=values, selected=selected, plan_id=candidates[selected].identity))
                value = common_to_actor(executor.advance(target_time))
            elif kind == "ConstantPlanner":
                value = controller.update(torch.tensor(self.native(name), dtype=torch.float64), DT)
            elif kind == "IDM":
                # IDM compares neighbor headings to the route's actor-native headings.
                neighbor_values = torch.tensor([[common_to_actor(s) for s in p[1].states] for p in neighbors], dtype=torch.float64)
                value = controller.update(state=torch.tensor(self.native(name), dtype=torch.float64),
                                          path=self.route[name], dt=DT, neighbors=neighbor_values)
            else:
                self.unicycle_support(controller, target_time * float(controller.speed))
                if not math.isclose(float(controller.t), now * float(controller.speed), abs_tol=1e-10):
                    raise ContractError("unicycle_stale_clock")
                value = controller.update(DT)
            value = state4([float(x) for x in value])
            pending[name] = torch.tensor([value[0], value[1], float(self.stats[name][2]), value[2], value[3]], dtype=torch.float64)
        self.original.stats.update(pending)
        self.tick += 1
        transforms = self.transforms()
        self.events.append(dict(event="consume", time=target_time, states={n: self.native(n) for n in self.stats},
                                transforms={n: m.detach().cpu().tolist() for n, m in transforms[0].items()}))
        return transforms


def ego_state(env):
    return [float(env.vab[1]), float(env.vab[0]), float(env.vr[1]), float(env.velo), float(env.steer)]


def check_runtime(env):
    expected = dict(dt=DT, Lr=1.35, Lf=1.35, min_acc=-2.0, max_acc=2.0,
                    min_steer=-math.pi / 12, max_steer=math.pi / 12)
    if env.dt != DT or any(not math.isclose(scalar(float(env.kinematic[k])), v, abs_tol=1e-12, rel_tol=0) for k, v in expected.items()):
        raise ContractError("runtime_kinematics")
    if abs(scalar(float(env.steer))) > math.pi / 3:
        raise ContractError("runtime_steering_angle")


class Session:
    """One fresh simulator episode; every exception latches a stopping reason."""

    def __init__(self, env, episode, *, device="cuda"):
        self.env, self.episode = env, episode
        self.reset_seen, self.stopped, self.frame = False, None, 0
        self.events = []
        check_runtime(env)
        if env.timestamp != 0 or env.last_accel != 0 or env.last_steer_rate != 0:
            raise ContractError("environment_not_fresh")
        env.planner = TimedPlanner(env.planner, episode, device=device)
        self.controller = ConstrainedController()

    def stop(self, reason):
        self.stopped = reason
        self.events.append(dict(event="stop", frame=self.frame, time=self.env.timestamp, reason=reason))

    def reset(self):
        try:
            if self.reset_seen or self.stopped:
                raise ContractError("duplicate_reset")
            self.reset_seen = True
            self.env.steer = float(self.env.kinematic["start_steer"])
            self.env.last_accel = self.env.last_steer_rate = 0.0
            result = self.env.reset()
            self.events.append(dict(event="reset", time=0.0, state=ego_state(self.env)))
            self.check_observation(result[1], 0.0)
            return result
        except Exception as exc:
            self.stop(f"{type(exc).__name__}:{exc}")
            raise

    def check_observation(self, info, time_value):
        if info["timestamp"] != time_value or self.env.timestamp != time_value or self.env.planner.tick * DT != time_value:
            raise ContractError("observation_clock")
        if not np.allclose(info["obj_boxes"], self.env.objs_list, atol=0, rtol=0):
            raise ContractError("observation_collision_state")

    def step(self, delivery):
        start = time.perf_counter_ns()
        try:
            if not self.reset_seen or self.stopped:
                raise ContractError("session_not_running")
            check_runtime(self.env)
            now = self.frame * DT
            before = ego_state(self.env)
            if self.env.timestamp != now:
                raise ContractError("environment_clock")
            ref = reference(delivery, [before[1], before[0], before[2], before[3]], episode=self.episode, frame=self.frame, time=now)
            result = self.controller.run(ref, before, episode=self.episode, observation_time=now)
            self.events.append(dict(event="control", frame=self.frame, result=result, delivery=delivery, reference=ref.record()))
            replay_certificate(result)
            action = require_action(result)
            # Forced braking is a separate arm, after retaining the same nominal solution.
            if delivery["mode"] == "brake_t0" or (delivery["mode"] == "brake_t2_5" and now >= 2.5):
                action = dict(acc=-2.0, steer_rate=0.0)
            predicted = rollout(before, [[action["acc"], action["steer_rate"]]])[0][1]
            transition_start = time.perf_counter_ns()
            observation = self.env.step(action)
            after = ego_state(self.env)
            if not np.allclose(predicted, after, atol=1e-9, rtol=0):
                raise ContractError("simulator_transition_mismatch")
            self.frame += 1
            self.check_observation(observation[-1], self.frame * DT)
            self.events.append(dict(event="step", frame=self.frame, time=self.frame * DT, before=before,
                                    applied=action, after=after, info={k: observation[-1][k] for k in ("timestamp", "ego_box", "obj_boxes", "collision", "rc")},
                                    simulator_ns=time.perf_counter_ns() - transition_start,
                                    complete_step_ns=time.perf_counter_ns() - start))
            if observation[2] or observation[3]:
                self.stop("simulator_terminated" if observation[2] else "simulator_truncated")
            return observation
        except Exception as exc:
            self.stop(f"{type(exc).__name__}:{exc}")
            raise
