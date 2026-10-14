"""One seeded OMPL process per case; no shared planner/RNG lifetime."""

import argparse
import json
from pathlib import Path

from experiments.iter158_constraint_aware_search.search import summary
from experiments.iter159_route_search_qualification.run import query_for, retain_trace
from .adapter import search
from .common import BASE, encode, read, require, write
from .runtime import verify


def run(root, output, case_id, seed, library):
    verify(root, library)
    plan = json.loads(read(root, BASE / "PLAN.json"))
    old = json.loads(read(root, "experiments/iter153_action_feasibility/PLAN.json"))
    cases = json.loads(read(root, "experiments/iter161_grouping_width_ablation/CASES.json"))
    case = next(c for c in cases if c["id"] == case_id)
    query = query_for(case)
    with (output / "events.jsonl").open("xb") as events:

        def emit(kind, row):
            events.write(encode(dict(kind=kind, **row)))
            require(events.tell() < plan["max_output_bytes"] // 4 - 1000000, "output_budget")

        result = search(
            library, case["geometry"], old, plan, lambda s: summary(query(s)), emit, seed
        )
    trace = result.pop("trace")
    retain_trace(output / "selected", trace, query)
    result.update(case=case_id, seed=seed, materialization_queries=len(trace))
    write(output / "result.json", result)
    verify(root, library)
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--case", required=True)
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--library", type=Path, required=True)
    a = p.parse_args()
    run(a.root.resolve(), a.output.resolve(), a.case, a.seed, a.library.resolve())
