"""One feedback request followed by unchanged legacy proposals within one budget."""

import math
import time
from experiments.iter169_full_horizon_control.shooting import StopEvaluation
from experiments.iter177_pose_aware_seed.forward import proposals
from .common import require, rss
from .policy import active


def solve(evaluator, integrated, limit):
    stop = "no_free_controls"
    inserted = int(active(evaluator.geometry, evaluator.before, evaluator.old, evaluator.plan))
    try:
        if inserted:
            require(limit > 0, "proposal_generation_limit")
            evaluator.evaluate_feedback()
        for index, values in enumerate(proposals(evaluator.controls)):
            require(index + inserted < limit, "proposal_generation_limit")
            evaluator.evaluate(values, "initial" if index == 0 else "forward_proposal")
            if not len(values):
                break
    except StopEvaluation as exc:
        stop = str(exc)
    best = evaluator.best
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
    result = dict(
        selected_evaluation=None if best is None else best["id"],
        attempts=evaluator.attempts,
        queries=evaluator.queries,
        evaluations=evaluator.evaluations,
        requests=evaluator.requests,
        cache_hits=evaluator.cache_hits,
        stop=stop,
        optimizer=optimizer,
        elapsed_seconds=time.monotonic() - evaluator.started,
        peak_rss_bytes=rss(),
    )
    if integrated:
        result.update(
            trace=best["trace"][: best["selected_prefix"] + 1] if best else [evaluator.root],
            selected_prefix=best["selected_prefix"] if best else 0,
            target_complete=bool(
                best
                and best["target_complete"]
                and best["selected_prefix"] == evaluator.task["terminal_frame"]
            ),
            world_complete=bool(best and best["world_complete"]),
            unused_attempt_budget=evaluator.budget - evaluator.attempts,
        )
    else:
        result.update(
            trace=best["trace"] if best else [evaluator.root],
            complete=bool(best and best["complete"]),
            unused_attempt_budget=evaluator.plan["attempt_budget"] - evaluator.attempts,
        )
    require(math.isfinite(result["elapsed_seconds"]), "elapsed_time")
    return result
