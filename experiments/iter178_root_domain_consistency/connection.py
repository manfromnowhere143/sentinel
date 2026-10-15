"""Accounted centered shooting with absolute scene time and valid-prefix returns."""

import math
import struct
import time

import numpy as np
from scipy.optimize import least_squares

from experiments.iter153_action_feasibility.geometry import obstacles
from experiments.iter153_action_feasibility.planner import transition
from experiments.iter158_constraint_aware_search.search import prior_reason
from experiments.iter167_planner_terminal_contract.adapter import distance, terminal_frame
from experiments.iter169_full_horizon_control.shooting import (
    StopEvaluation,
    actuator_slacks,
    terminal_cost,
)
from experiments.iter168_control_connector.connector import reached
from .common import require, rss
from .controls import Controls


def task_for(before, target, plan):
    require(
        len(before) == len(target) == 6 and all(math.isfinite(x) for x in before + target),
        "connection_domain",
    )
    require(
        float(before[5]).is_integer() and 0 <= before[5] <= plan["max_actions"], "connection_clock"
    )
    remaining = plan["max_actions"] - int(before[5])
    if remaining == 0:
        return None
    horizon = min(plan["connection_horizon"], remaining, max(1, math.ceil(target[5] - before[5])))
    # No prescribed wait/stop phase exists in the four original planner cases.
    # Stopping, waiting and restarting remain free physical controls, never clamped.
    return dict(
        target=target[:5],
        terminal_frame=horizon,
        tolerance=plan["target_tolerance"],
        wait_until=0,
        stop_from=None,
    )


class Evaluator:
    def __init__(self, geometry, before, target, task, old, plan, budget, deadline, query, emit):
        self.geometry, self.before, self.target, self.task = geometry, before, target, task
        self.old, self.plan, self.budget, self.deadline = old, plan, budget, deadline
        self.query, self.emit = query, emit
        self.controls = Controls(before[:5], task)
        self.boxes = obstacles(geometry)
        self.started = time.monotonic()
        self.attempts = self.queries = self.requests = self.cache_hits = self.evaluations = 0
        self.cache = {}
        self.best = None
        self.best_rank = None
        background = query(before[:5])
        self.queries += 1
        reason, outcome = prior_reason(
            before[:5], before[:5], [0.0, 0.0], int(before[5]), geometry, old, self.boxes
        )
        require(
            reason is None and background["decision"] == "clear" and outcome["rc"] < 1,
            "connection_root",
        )
        self.root = dict(
            id=int(before[5]),
            parent=None,
            frame=int(before[5]),
            action=None,
            state=before[:5],
            route=outcome,
            reason="clear",
            background=background,
        )

    def request(self, values, caller, evaluation=None, cached=False, stopped=None):
        self.emit(
            "request",
            dict(
                id=self.requests,
                caller=caller,
                values=values.tolist(),
                evaluation=evaluation,
                cached=cached,
                stopped=stopped,
            ),
        )

    def evaluate(self, values, caller):
        values = np.asarray(values, dtype=float)
        self.controls.table(values)
        self.requests += 1
        if time.monotonic() >= self.deadline:
            self.request(values, caller, stopped="time_budget")
            raise StopEvaluation("time_budget")
        key = struct.pack(">" + "d" * len(values), *values)
        if key in self.cache:
            self.cache_hits += 1
            row = self.cache[key]
            self.request(values, caller, evaluation=row["id"], cached=True)
            return row
        horizon = self.task["terminal_frame"]
        if self.attempts + horizon > self.budget:
            self.request(values, caller, stopped="attempt_budget")
            raise StopEvaluation("attempt_budget")
        self.evaluations += 1
        self.request(values, caller, evaluation=self.evaluations)
        table = self.controls.table(values)
        rows, slacks = [self.root], []
        valid_prefix = 0
        interrupted = None
        world_complete = False
        for local in range(1, horizon + 1):
            if time.monotonic() >= self.deadline:
                interrupted = "time_budget"
                break
            require(rss() <= self.plan["max_rss_bytes"], "memory_budget")
            before = rows[-1]["state"]
            action = self.controls.action(table, local, before)
            self.attempts += 1
            state = transition(before, action, self.old)
            frame = int(self.before[5]) + local
            reason, outcome = prior_reason(
                before, state, action, frame, self.geometry, self.old, self.boxes
            )
            if (
                reason is None
                and outcome["rc"] >= 1
                and frame < terminal_frame(self.geometry, self.old)
            ):
                reason = "premature_completion"
            background = None
            if reason is None:
                background = self.query(state)
                self.queries += 1
                reason = background["decision"]
            rows.append(
                dict(
                    id=frame,
                    parent=frame - 1,
                    frame=frame,
                    action=action,
                    state=state,
                    route=outcome,
                    reason=reason,
                    background=background,
                )
            )
            slacks.extend(actuator_slacks(state, action))
            if valid_prefix == local - 1 and reason == "clear":
                valid_prefix = local
                if outcome["rc"] >= 1:
                    world_complete = True
                    break
        full = len(rows) == horizon + 1
        # Interrupted trajectories are never returned, even if their prefix was valid.
        candidates = range(1, valid_prefix + 1) if interrupted is None else []
        selected_prefix = (
            min(
                candidates,
                key=lambda k: (distance([*rows[k]["state"], rows[k]["frame"]], self.target), k),
            )
            if candidates
            else 0
        )
        if world_complete:
            selected_prefix = valid_prefix
        row = dict(
            id=self.evaluations,
            values=values.tolist(),
            trace=rows,
            constraints=slacks,
            full=full,
            interrupted=interrupted,
            valid_prefix=valid_prefix,
            selected_prefix=selected_prefix,
            world_complete=world_complete,
            target_complete=bool(
                full and valid_prefix == horizon and reached(rows[-1]["state"], horizon, self.task)
            ),
            objective=terminal_cost(rows[-1]["state"], self.task) if full else None,
        )
        self.emit("evaluation", row)
        if selected_prefix:
            endpoint = rows[selected_prefix]
            rank = (
                not world_complete,
                distance([*endpoint["state"], endpoint["frame"]], self.target),
                row["id"],
                selected_prefix,
            )
            if self.best_rank is None or rank < self.best_rank:
                self.best, self.best_rank = row, rank
        if full:
            self.cache[key] = row
        if world_complete:
            raise StopEvaluation("model_complete")
        if row["target_complete"]:
            raise StopEvaluation("qualified_candidate")
        if interrupted:
            raise StopEvaluation(interrupted)
        return row


def solve(evaluator):
    task, plan = evaluator.task, evaluator.plan
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

            def residual(increments):
                row = evaluator.evaluate(initial + increments, "residual")
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
                np.zeros_like(initial),
                bounds=(-1.0 - initial, 1.0 - initial),
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
            evaluator.evaluate(initial + result.x, "returned_point")
            stop = "optimizer_return"
    except StopEvaluation as exc:
        stop = str(exc)
    best = evaluator.best
    trace = best["trace"][: best["selected_prefix"] + 1] if best is not None else [evaluator.root]
    return dict(
        trace=trace,
        target_complete=bool(
            best is not None
            and best["target_complete"]
            and best["selected_prefix"] == task["terminal_frame"]
        ),
        world_complete=bool(best is not None and best["world_complete"]),
        selected_prefix=0 if best is None else best["selected_prefix"],
        selected_evaluation=None if best is None else best["id"],
        attempts=evaluator.attempts,
        queries=evaluator.queries,
        evaluations=evaluator.evaluations,
        requests=evaluator.requests,
        cache_hits=evaluator.cache_hits,
        unused_attempt_budget=evaluator.budget - evaluator.attempts,
        stop=stop,
        optimizer=optimizer,
        elapsed_seconds=time.monotonic() - evaluator.started,
        peak_rss_bytes=rss(),
    )
