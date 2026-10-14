"""Full-horizon shooting in increments around the unchanged physical initialization.

Only optimizer coordinates and their bounds differ from Iter169/170. The frozen
control parameterization, evaluator, dynamics and accounting are imported intact.
"""

import math
import time
import numpy as np
from scipy.optimize import least_squares
from experiments.iter169_full_horizon_control.shooting import Evaluator, StopEvaluation
from .common import rss


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
