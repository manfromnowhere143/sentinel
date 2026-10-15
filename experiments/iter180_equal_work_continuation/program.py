"""Actual retained generator/evaluator with first-checkpoint-witness stopping."""

from collections import Counter
import time
from experiments.iter177_pose_aware_seed.forward import proposals
from experiments.iter178_root_domain_consistency.connection import Evaluator
from experiments.iter169_full_horizon_control.shooting import StopEvaluation
from .common import require
from .target import task_for


def run_program(state, frame, geometry, old, plan, query, target, deadline):
    events = []
    task = task_for(target, frame)
    evaluator = Evaluator(
        geometry,
        [*state, frame],
        [*target["state"], target["frame"]],
        task,
        old,
        plan,
        plan["per_root_attempts"],
        deadline,
        query,
        lambda kind, row: events.append(dict(kind=kind, **row)),
    )
    witness = None
    stop = generator_stop = None
    for index, values in enumerate(proposals(evaluator.controls)):
        require(index < plan["max_proposals"], "proposal_generation_limit")
        try:
            evaluator.evaluate(values, "initial" if index == 0 else "forward_proposal")
        except StopEvaluation as exc:
            generator_stop = str(exc)
        evaluations = [e for e in events if e["kind"] == "evaluation"]
        last = evaluations[-1] if evaluations else None
        if (
            last
            and last["full"]
            and last["valid_prefix"] == task["terminal_frame"]
            and last["interrupted"] is None
        ):
            witness, stop = last, "checkpoint_witness"
            break
        if generator_stop is not None:
            require(generator_stop in ("attempt_budget", "time_budget"), "noncheckpoint_stop")
            stop = generator_stop
            break
    require(stop is not None, "missing_stop")
    chosen = witness or evaluator.best
    prefix = task["terminal_frame"] if witness else (chosen["selected_prefix"] if chosen else 0)
    trace = chosen["trace"][: prefix + 1] if chosen else [evaluator.root]
    result = dict(
        start_frame=frame,
        target_frame=target["frame"],
        witness=witness is not None,
        stop=stop,
        generator_stop=generator_stop,
        attempts=evaluator.attempts,
        queries=evaluator.queries,
        evaluations=evaluator.evaluations,
        requests=evaluator.requests,
        cache_hits=evaluator.cache_hits,
        selected_evaluation=None if chosen is None else chosen["id"],
        selected_prefix=prefix,
        counts=dict(
            Counter(
                r["reason"] for e in events if e["kind"] == "evaluation" for r in e["trace"][1:]
            )
        ),
        evaluator_elapsed_seconds=time.monotonic() - evaluator.started,
    )
    return dict(result=result, trace=trace, events=events)
