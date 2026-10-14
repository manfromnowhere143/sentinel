"""One bounded exact/24 continuation from an independently admitted history."""

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
from .common import BASE, encode, inputs, read, require, write
from .continuation import prefix_binding
from .records import initialize, finish, failure
from .search import search


def run(root, output, source, prefix_commit):
    started = time.monotonic()
    # No scientific search initialization until the bound historical prefix is admitted.
    preview = json.loads(read(root, BASE / "PLAN.json"))
    admission, _, admission_sha = prefix_binding(root, prefix_commit, preview, source)
    plan = initialize(root, output, source, "search")
    try:
        geometry, old, arrays = inputs(root, plan)
        population = BackgroundPopulation(arrays["selected_xyz"], plan["population_sha256"])
        ground = arrays["ground_poses"]
        del arrays
        setup_seconds = time.monotonic() - started

        def query(state):
            return population.query(box_for_state(state, ground)[0])

        with (
            (output / "attempts.jsonl").open("xb") as attempts,
            (output / "depths.jsonl").open("xb") as depths,
        ):

            def emit(kind, row):
                (attempts if kind == "attempt" else depths).write(encode(row))
                require(
                    attempts.tell() + depths.tell()
                    < plan["max_output_bytes"] - plan["finalization_reserve_bytes"],
                    "output_budget",
                )
                if kind == "depth":
                    attempts.flush()
                    depths.flush()
                    if row["frame"] % 5 == 0 or row["frame"] == plan["start_frame"] + 1:
                        print(
                            json.dumps(
                                dict(
                                    absolute_frame=row["frame"],
                                    survivors=row["survivors"],
                                    retained=len(row["beam"]),
                                )
                            ),
                            flush=True,
                        )

            result = search(
                geometry,
                old,
                plan,
                lambda state: summary(query(state)),
                emit,
                "exact",
                admission["branch"],
            )
        trace = result.pop("trace")
        materialization_start = time.monotonic()
        retain_trace(output / "selected", trace, query)
        result.update(
            aggregation="exact",
            width=plan["beam_width"],
            materialization_queries=len(trace),
            materialization_seconds=time.monotonic() - materialization_start,
        )
        write(output / "result.json", result)
        finish(
            output,
            source,
            plan,
            "search",
            started,
            result=result,
            prefix_admission_commit=prefix_commit,
            prefix_admission_sha256=admission_sha,
            setup_seconds=setup_seconds,
            selected_points=plan["selected_points"],
            population_sha256=population.sha256,
        )
        print(json.dumps(result), flush=True)
    except Exception as exc:
        failure(output, started, exc)
        raise


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--source", required=True)
    p.add_argument("--prefix-commit", required=True)
    args = p.parse_args()
    run(args.root.resolve(), args.output.resolve(), args.source, args.prefix_commit)
