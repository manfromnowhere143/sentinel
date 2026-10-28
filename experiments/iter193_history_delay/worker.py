"""One history/delay condition with unchanged native planner implementation."""

import argparse
import json
from pathlib import Path
import time
from experiments.iter159_route_search_qualification.run import query_for, retain_trace
from experiments.iter158_constraint_aware_search.search import summary
from experiments.iter191_stop_wait_release.adapter import search
from experiments.iter191_stop_wait_release.runtime import LIBRARY, verify
from .clock import extend, translate, join
from .common import BASE, PLANNER, encode, read, require, rss, write, load_source


def collect(output, case, old, history, planner, condition, library):
    query = query_for(case)
    prefix = extend(history, condition["origin"], condition["delay"], case, old, query)
    write(output / "prefix.json", prefix)
    setup_queries = condition["delay"]
    if any(r["reason"] != "clear" for r in prefix):
        retain_trace(output / "selected", prefix, query)
        return dict(
            condition=condition,
            complete=False,
            stop="prefix_ineligible",
            attempts=0,
            queries=0,
            setup_queries=setup_queries,
            materialization_queries=len(prefix),
        )
    local, config = translate(case, planner, prefix, old)
    calls = 0

    def counted(state):
        nonlocal calls
        calls += 1
        return summary(query(state))

    with (output / "events.jsonl").open("xb") as events:

        def emit(kind, row):
            events.write(encode(dict(kind=kind, **row)))
            require(events.tell() < 64 * 1024 * 1024, "event_output_budget")

        result = search(library, local["geometry"], old, config, counted, emit, condition["seed"])
    trace, sequences = result.pop("trace"), result.pop("sequences")
    require(calls == result["queries"], "query_accounting")
    write(output / "trace.json", trace)
    write(output / "sequences.json", sequences)
    joined = join(prefix, trace)
    retain_trace(output / "selected", joined, query)
    result.update(
        condition=condition,
        setup_queries=setup_queries,
        materialization_queries=len(joined),
        remaining_actions=config["max_actions"],
        first_new_control_frame=prefix[-1]["frame"] + 1,
    )
    return result


def run(root, output, label):
    started = time.monotonic()
    verify(root)
    plan = json.loads(read(root, BASE / "PLAN.json"))
    condition = next(c for c in plan["conditions"] if c["id"] == label)
    case, old, history = load_source(root)
    planner = json.loads(read(root, PLANNER))
    result = collect(output, case, old, history, planner, condition, LIBRARY)
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
    p.add_argument("--condition", required=True)
    a = p.parse_args()
    run(Path.cwd(), a.output.resolve(), a.condition)
