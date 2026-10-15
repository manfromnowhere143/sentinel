"""Bounded forward proposals with one algebraic pose-aware initial program."""

import itertools
import math
import time

import numpy as np

from experiments.iter169_full_horizon_control.shooting import StopEvaluation
from .common import require, rss
from .seed import initial


def radical(index, base):
    value, scale = 0.0, 1.0
    while index:
        index, digit = divmod(index, base)
        scale /= base
        value += digit * scale
    return value


def proposals(controls):
    yield initial(controls)
    phases = ((1, 1, 1, 1), (1, 1, -1, -1), (1, -1, -1, 1))
    horizon = controls.task["terminal_frame"] - controls.task["wait_until"]
    for pa, pr, a, r in itertools.product(phases, phases, (0, -1, 1), (0, -1, 1)):
        yield np.asarray([
            (a * pa[min(3, 4 * (frame - controls.task["wait_until"] - 1) // horizon)]
             if kind == 0 else r * pr[min(3, 4 * (frame - controls.task["wait_until"] - 1) // horizon)])
            for frame, kind in controls.variables
        ], dtype=float)
    index = 1
    while True:
        values = [2 * radical(index, b) - 1 for b in (2, 3, 5, 7, 11, 13, 17, 19)]
        yield np.asarray([
            values[2 * min(3, 4 * (frame - controls.task["wait_until"] - 1) // horizon) + kind]
            for frame, kind in controls.variables
        ])
        index += 1


def solve(evaluator, integrated, limit):
    stop = "no_free_controls"
    try:
        for index, values in enumerate(proposals(evaluator.controls)):
            require(index < limit, "proposal_generation_limit")
            evaluator.evaluate(values, "initial" if index == 0 else "forward_proposal")
            if not len(values):
                break
    except StopEvaluation as exc:
        stop = str(exc)
    best = evaluator.best
    optimizer = dict(started=False, returned=False, success=None, status=None,
                     message=None, iterations=None, function_evaluations=None,
                     gradient_evaluations=None)
    result = dict(
        selected_evaluation=None if best is None else best["id"],
        attempts=evaluator.attempts, queries=evaluator.queries,
        evaluations=evaluator.evaluations, requests=evaluator.requests,
        cache_hits=evaluator.cache_hits, stop=stop, optimizer=optimizer,
        elapsed_seconds=time.monotonic() - evaluator.started, peak_rss_bytes=rss(),
    )
    if integrated:
        result.update(
            trace=best["trace"][:best["selected_prefix"] + 1] if best else [evaluator.root],
            selected_prefix=best["selected_prefix"] if best else 0,
            target_complete=bool(best and best["target_complete"]
                                 and best["selected_prefix"] == evaluator.task["terminal_frame"]),
            world_complete=bool(best and best["world_complete"]),
            unused_attempt_budget=evaluator.budget-evaluator.attempts,
        )
    else:
        result.update(trace=best["trace"] if best else [evaluator.root],
                      complete=bool(best and best["complete"]),
                      unused_attempt_budget=evaluator.plan["attempt_budget"]-evaluator.attempts)
    require(math.isfinite(result["elapsed_seconds"]), "elapsed_time")
    return result
