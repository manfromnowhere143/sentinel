"""One connector/request in a fresh process; no RRT or source-scene execution."""

import argparse
import json
from pathlib import Path
import time

from experiments.iter158_constraint_aware_search.search import summary
from experiments.iter159_route_search_qualification.run import query_for, retain_trace
from experiments.iter169_full_horizon_control.shooting import Evaluator as LocalEvaluator
from experiments.iter171_centered_shooting.shooting import search as local_shooting
from experiments.iter172_integrated_rrt.connection import Evaluator, solve as shooting
from .forward import solve as forward
from .common import BASE, OLD, encode, read, require, write
from .runtime import verify


def execute(case, request, arm, old, plan, query, emit):
    if request is not None:
        ev = Evaluator(case["geometry"], request["before"], request["target"],
                       request["task"], old, plan, request["budget"],
                       time.monotonic() + plan["per_run_seconds"], query, emit)
        return shooting(ev) if arm == "shooting" else forward(ev, True, plan["max_proposals"])
    local = dict(plan, attempt_budget=plan["constructive_attempt_budget"])
    if arm == "shooting":
        return local_shooting(case["geometry"], case["task"], old, local, query, emit)
    ev = LocalEvaluator(case["geometry"], case["task"], old, local, query, emit)
    return forward(ev, False, plan["max_proposals"])


def run(root, output, kind, identity, arm):
    verify(root)
    plan = json.loads(read(root, BASE / "PLAN.json"))
    old = json.loads(read(root, OLD))
    request = None
    if kind == "request":
        request = next(r for r in json.loads(read(root, BASE / "REQUESTS.json"))["requests"]
                       if r["id"] == identity)
        cases = json.loads(read(root, "experiments/iter161_grouping_width_ablation/CASES.json"))
        case = next(c for c in cases if c["id"] == request["case"])
    else:
        case = next(c for c in json.loads(read(root, BASE / "CASES.json")) if c["id"] == identity)
    query = query_for(case)
    with (output / "events.jsonl").open("xb") as stream:
        def emit(event, row):
            stream.write(encode(dict(kind=event, **row)))
            require(stream.tell() < 16000000, "worker_output_budget")
        # Only geometry, explicit task and queries enter controller functions.
        result = execute(case, request, arm, old, plan, lambda s: summary(query(s)), emit)
    trace = result.pop("trace")
    retain_trace(output / "selected", trace, query)
    result.update(id=identity, population=kind, arm=arm, materialization_queries=len(trace))
    write(output / "result.json", result)
    verify(root)
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--kind", choices=["request", "constructive"], required=True)
    p.add_argument("--identity", required=True)
    p.add_argument("--arm", choices=["shooting", "forward"], required=True)
    a = p.parse_args()
    run(a.root.resolve(), a.output.resolve(), a.kind, a.identity, a.arm)
