"""One prospective schedule, fixed per-root budgets, full retained raw traces."""

import argparse
import json
from pathlib import Path
import time

from experiments.iter156_background_calibration.background import (
    BackgroundPopulation,
    box_for_state,
)
from experiments.iter158_constraint_aware_search.search import summary
from experiments.iter159_route_search_qualification.run import retain_trace
from experiments.iter164_monitor_time_continuation.continuation import concatenate
from experiments.iter164_monitor_time_continuation.search import search
from .candidates import candidates, prefix_for
from .common import BASE, encode, inputs, read, require, write
from .records import initialize, finish, failure


def run(root, source):
    started = time.monotonic()
    output = root / BASE / "proof/search_raw"
    plan = initialize(root, output, source, "search")
    try:
        geometry, old, arrays = inputs(root, plan)
        population = BackgroundPopulation(arrays["selected_xyz"], plan["population_sha256"])
        ground = arrays["ground_poses"]
        del arrays
        schedule, nodes = candidates(root)
        require(schedule == json.loads(read(root, BASE / "CANDIDATES.json")), "schedule_binding")

        def query(state):
            return population.query(box_for_state(state, ground)[0])

        records, written = [], 0
        for entry in schedule:
            name = f"{entry['cohort']}_{entry['node_id']:04d}"
            if (
                time.monotonic() - started
                > plan["search_producer_seconds"] - plan["per_run_seconds"] - 60
            ):
                records.append(
                    dict(name=name, **entry, status="censored", reason="global_time_reserve")
                )
                continue
            folder = output / name
            folder.mkdir()
            prefix = prefix_for(root, nodes, entry["node_id"])
            branch = dict(frame=27, time=6.75, state=prefix[-1]["state"])
            with (
                (folder / "attempts.jsonl").open("xb") as attempts,
                (folder / "depths.jsonl").open("xb") as depths,
            ):

                def emit(kind, row):
                    nonlocal written
                    data = encode(row)
                    written += len(data)
                    require(
                        written < plan["max_output_bytes"] - plan["finalization_reserve_bytes"],
                        "output_budget",
                    )
                    (attempts if kind == "attempt" else depths).write(data)

                result = search(
                    geometry, old, plan, lambda s: summary(query(s)), emit, "exact", branch
                )
            trace = result.pop("trace")
            retain_trace(folder / "selected", trace, query)
            joined = concatenate(prefix, trace)
            retain_trace(folder / "joined", joined, query)
            result.update(
                name=name,
                **entry,
                status="observed",
                aggregation="exact",
                width=24,
                materialization_queries=len(trace) + len(joined),
            )
            write(folder / "result.json", result)
            records.append(result)
            print(json.dumps(result), flush=True)
        finish(
            output,
            source,
            plan,
            "search",
            started,
            records=records,
            selected_points=plan["selected_points"],
            population_sha256=population.sha256,
        )
    except Exception as exc:
        failure(output, started, exc)
        raise


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--source", required=True)
    args = p.parse_args()
    run(args.root.resolve(), args.source)
