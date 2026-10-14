"""Bounded full-horizon shooting; exact task phases and hard candidate admission.

Bounded trust-region least squares guides terminal/actuator optimization. Scene and temporal predicates remain
hard eligibility checks. Optimizer convergence and task completion are separate.
Every computed transition is charged, including derivative and line-search probes.
"""

import math
import struct
import time

import numpy as np
from scipy.optimize import least_squares

from experiments.iter153_action_feasibility.geometry import obstacles
from experiments.iter153_action_feasibility.planner import transition
from experiments.iter158_constraint_aware_search.search import prior_reason
from experiments.iter168_control_connector.connector import reached, task_reason
from .common import require, rss


class StopEvaluation(Exception):
    """Declared stopping, never interpreted as optimizer convergence."""


class Controls:
    def __init__(self, reset, task):
        self.reset, self.task = reset, task
        horizon, wait, stop = task["terminal_frame"], task["wait_until"], task["stop_from"]
        require(type(horizon) is int and 1 <= horizon <= 16, "task_horizon")
        require(type(wait) is int and 0 <= wait <= horizon, "wait_domain")
        require(stop is None or type(stop) is int and wait < stop <= horizon, "stop_domain")
        require(
            len(reset) == 5
            and len(task["target"]) == 5
            and all(
                type(v) in (int, float) and math.isfinite(v) for v in [*reset, *task["target"]]
            ),
            "state_domain",
        )
        require(0 <= reset[3] <= 6 and abs(reset[4]) <= math.pi / 3, "reset_bounds")
        require(
            len(task["tolerance"]) == 5
            and all(
                type(v) in (int, float) and math.isfinite(v) and v > 0 for v in task["tolerance"]
            ),
            "tolerance_domain",
        )
        self.variables = []
        for frame in range(wait + 1, horizon + 1):
            if stop is None or frame < stop:
                self.variables.append((frame, 0))
            self.variables.append((frame, 1))

    def initial(self):
        task, reset = self.task, self.reset
        duration = (task["stop_from"] or task["terminal_frame"]) - task["wait_until"]
        acceleration = ((0 if task["stop_from"] else task["target"][3]) - reset[3]) / (
            0.25 * max(1, duration)
        )
        rate = (task["target"][4] - reset[4]) / (
            0.25 * max(1, task["terminal_frame"] - task["wait_until"])
        )
        return np.asarray(
            [
                np.clip(acceleration / 2 if k == 0 else rate / (math.pi / 12), -1.0, 1.0)
                for _, k in self.variables
            ],
            dtype=float,
        )

    def table(self, values):
        require(
            len(values) == len(self.variables) and np.isfinite(values).all(), "parameter_domain"
        )
        return {pair: float(value) for pair, value in zip(self.variables, values)}

    def action(self, table, frame, state):
        a = 2 * table.get((frame, 0), 0.0)
        if frame == self.task["stop_from"]:
            a = -state[3] / 0.25
        return [a, math.pi / 12 * table.get((frame, 1), 0.0)]


def terminal_cost(state, task):
    errors = [a - b for a, b in zip(state, task["target"])]
    errors[2] = math.remainder(errors[2], 2 * math.pi)
    return sum((x / tolerance) ** 2 for x, tolerance in zip(errors, task["tolerance"]))


def actuator_slacks(state, action):
    speed, steering = state[3:]
    yaw = speed * math.tan(steering) / 2.7
    return [
        2 - action[0],
        2 + action[0],
        math.pi / 12 - action[1],
        math.pi / 12 + action[1],
        speed,
        6 - speed,
        math.pi / 3 - steering,
        math.pi / 3 + steering,
        0.95 - yaw,
        0.95 + yaw,
        4.89 - speed * yaw,
        4.89 + speed * yaw,
    ]


class Evaluator:
    def __init__(self, geometry, task, old, plan, query, emit):
        require(old["dt"] == 0.25 and old["wheelbase"] == 2.7, "motion_contract")
        self.geometry, self.task, self.old, self.plan = geometry, task, old, plan
        self.query, self.emit = query, emit
        self.controls = Controls(geometry["reset"], task)
        self.boxes = obstacles(geometry)
        self.started = time.monotonic()
        self.attempts = self.queries = self.requests = self.cache_hits = self.evaluations = 0
        self.cache = {}
        self.best = None
        state = geometry["reset"]
        background = query(state)
        self.queries += 1
        reason, outcome = prior_reason(state, state, [0.0, 0.0], 0, geometry, old, self.boxes)
        require(reason is None and background["decision"] == "clear", "initial_rejected")
        self.root = dict(
            id=0,
            parent=None,
            frame=0,
            action=None,
            state=state,
            route=outcome,
            reason="clear",
            background=background,
        )

    def evaluate(self, values, caller):
        values = np.asarray(values, dtype=float)
        self.controls.table(values)  # Validate before encoding/cache lookup.
        self.requests += 1
        if time.monotonic() - self.started >= self.plan["per_run_seconds"]:
            self.emit(
                "request",
                dict(
                    id=self.requests,
                    caller=caller,
                    values=values.tolist(),
                    evaluation=None,
                    cached=False,
                    stopped="time_budget",
                ),
            )
            raise StopEvaluation("time_budget")
        key = struct.pack(">" + "d" * len(values), *values)
        if key in self.cache:
            self.cache_hits += 1
            result = self.cache[key]
            self.emit(
                "request",
                dict(
                    id=self.requests,
                    caller=caller,
                    values=values.tolist(),
                    evaluation=result["id"],
                    cached=True,
                    stopped=None,
                ),
            )
            return result
        horizon = self.task["terminal_frame"]
        if self.attempts + horizon > self.plan["attempt_budget"]:
            self.emit(
                "request",
                dict(
                    id=self.requests,
                    caller=caller,
                    values=values.tolist(),
                    evaluation=None,
                    cached=False,
                    stopped="attempt_budget",
                ),
            )
            raise StopEvaluation("attempt_budget")
        self.evaluations += 1
        self.emit(
            "request",
            dict(
                id=self.requests,
                caller=caller,
                values=values.tolist(),
                evaluation=self.evaluations,
                cached=False,
                stopped=None,
            ),
        )
        table = self.controls.table(values)
        rows, constraints = [self.root], []
        eligible, interrupted = True, None
        for frame in range(1, horizon + 1):
            if time.monotonic() - self.started >= self.plan["per_run_seconds"]:
                interrupted = "time_budget"
                break
            require(rss() <= self.plan["max_rss_bytes"], "memory_budget")
            before = rows[-1]["state"]
            action = self.controls.action(table, frame, before)
            self.attempts += 1
            state = transition(before, action, self.old)
            reason, outcome = prior_reason(
                before, state, action, frame, self.geometry, self.old, self.boxes
            )
            if reason is None:
                reason = task_reason(state, frame, self.task, self.geometry["reset"])
            background = None
            if reason is None:
                background = self.query(state)
                self.queries += 1
                reason = background["decision"]
            eligible &= reason == "clear"
            rows.append(
                dict(
                    id=frame,
                    parent=frame - 1,
                    frame=frame,
                    action=action,
                    state=state,
                    route=outcome,
                    background=background,
                    reason=reason,
                )
            )
            constraints.extend(actuator_slacks(state, action))
        full = len(rows) == horizon + 1
        eligible = bool(full and eligible)
        complete = bool(eligible and reached(rows[-1]["state"], horizon, self.task))
        result = dict(
            id=self.evaluations,
            values=values.tolist(),
            trace=rows,
            full=full,
            eligible=eligible,
            complete=complete,
            interrupted=interrupted,
            objective=terminal_cost(rows[-1]["state"], self.task) if full else None,
            constraints=constraints,
        )
        self.emit("evaluation", result)
        if eligible and (
            self.best is None
            or (result["objective"], result["id"]) < (self.best["objective"], self.best["id"])
        ):
            self.best = result
        if full:
            self.cache[key] = result
        if complete:
            self.best = result
            raise StopEvaluation("qualified_candidate")
        if interrupted:
            raise StopEvaluation(interrupted)
        return result


def search(geometry, task, old, plan, query, emit):
    evaluator = Evaluator(geometry, task, old, plan, query, emit)
    initial = evaluator.controls.initial()
    optimizer = dict(
        started=False,
        returned=False,
        success=None,
        status=None,
        message=None,
        iterations=None,
        function_evaluations=None,
        gradient_evaluations=None,
    )
    stop = "no_free_controls"
    try:
        evaluator.evaluate(initial, "initial")
        if len(initial):
            optimizer["started"] = True

            def residual(values):
                row = evaluator.evaluate(values, "residual")
                state = row["trace"][-1]["state"]
                errors = [state[i] - task["target"][i] for i in range(5)]
                errors[2] = math.remainder(errors[2], 2 * math.pi)
                terminal = [errors[i] / task["tolerance"][i] for i in range(5)]
                # Guide actuator feasibility; exact hard checks still decide eligibility.
                violations = [
                    min(0.0, slack) / plan["actuator_guidance_scale"]
                    for slack in row["constraints"]
                ]
                return np.asarray(terminal + violations)

            result = least_squares(
                residual,
                initial,
                bounds=(-1.0, 1.0),
                method="trf",
                tr_solver="exact",
                jac="2-point",
                x_scale="jac",
                loss="linear",
                max_nfev=plan["optimizer_max_nfev"],
                ftol=plan["optimizer_tolerance"],
                xtol=plan["optimizer_tolerance"],
                gtol=plan["optimizer_tolerance"],
                diff_step=plan["optimizer_diff_step"],
            )
            optimizer.update(
                returned=True,
                success=bool(result.success),
                status=int(result.status),
                message=str(result.message),
                iterations=None,
                function_evaluations=int(result.nfev),
                gradient_evaluations=int(result.njev),
            )
            # Charge or explicitly cache the optimizer-returned point as well.
            evaluator.evaluate(result.x, "returned_point")
            stop = "optimizer_return"
    except StopEvaluation as exc:
        stop = str(exc)
    best = evaluator.best
    trace = best["trace"] if best is not None else [evaluator.root]
    return dict(
        trace=trace,
        complete=bool(best is not None and best["complete"]),
        selected_evaluation=None if best is None else best["id"],
        attempts=evaluator.attempts,
        queries=evaluator.queries,
        evaluations=evaluator.evaluations,
        requests=evaluator.requests,
        cache_hits=evaluator.cache_hits,
        unused_attempt_budget=plan["attempt_budget"] - evaluator.attempts,
        stop=stop,
        optimizer=optimizer,
        elapsed_seconds=time.monotonic() - evaluator.started,
        peak_rss_bytes=rss(),
    )
