"""Exact admitted adapter with the Iter191 all-query recording wrapper."""

import argparse
import json
from pathlib import Path
import time
from experiments.iter159_route_search_qualification.run import query_for
from experiments.iter190_late_continuation_audit.masks import Queries
from experiments.iter191_stop_wait_release.adapter import search
from experiments.iter191_stop_wait_release.runtime import LIBRARY, verify
from .common import BASE, CASES, OLD, PREVIOUS, encode, read, require, rss, write


def collect(output, case, old, planner, seed, library):
    started = time.monotonic()
    query = Queries(output / "masks", query_for(case))
    with (output / "events.jsonl").open("xb") as stream:

        def emit(kind, row):
            stream.write(encode(dict(kind=kind, **row)))
            require(stream.tell() < 48 * 1024 * 1024, "event_output_budget")

        result = search(library, case["geometry"], old, planner, query, emit, seed)
    trace, sequences = result.pop("trace"), result.pop("sequences")
    query.finish()
    write(output / "trace.json", trace)
    write(output / "sequences.json", sequences)
    require(query.calls == result["queries"], "query_accounting")
    result.update(
        case=case["id"],
        seed=seed,
        recorded_queries=query.calls,
        distinct_queried_states=len(query.rows),
        collection_seconds=time.monotonic() - started,
        collection_peak_rss_bytes=rss(),
    )
    return result


def run(root, output, name, seed):
    started = time.monotonic()
    verify(root)
    plan = json.loads(read(root, BASE / "PLAN.json"))
    require((name, seed) in list(zip(plan["cases"], plan["seeds"])), "case_identity")
    old = json.loads(read(root, OLD))
    planner = json.loads(read(root, PREVIOUS / "PLAN.json"))
    case = next(c for c in json.loads(read(root, CASES)) if c["id"] == name)
    result = collect(output, case, old, planner, seed, LIBRARY)
    verify(root)
    result.update(worker_seconds=time.monotonic() - started, worker_peak_rss_bytes=rss())
    require(
        result["worker_seconds"] <= plan["worker_supervisor_seconds"]
        and result["worker_peak_rss_bytes"] <= plan["max_rss_bytes"],
        "worker_resources",
    )
    write(output / "result.json", result)
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--case", required=True)
    p.add_argument("--seed", type=int, required=True)
    a = p.parse_args()
    run(Path.cwd(), a.output.resolve(), a.case, a.seed)
