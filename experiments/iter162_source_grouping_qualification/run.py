"""One source-model acquisition, two fixed arms; unchanged Iter161 search."""

import argparse
import json
from pathlib import Path
import platform
import shutil
import sys
import time

import numpy as np

from experiments.iter156_background_calibration.background import (
    BackgroundPopulation,
    box_for_state,
)
from experiments.iter158_constraint_aware_search.search import summary
from experiments.iter159_route_search_qualification.run import retain_trace
from experiments.iter161_grouping_width_ablation.search import search
from .common import BASE, encode, git, inputs, read, require, rss, sha, source_check, write


def run(root, output, source):
    started = time.monotonic()
    plan = json.loads(read(root, BASE / "PLAN.json"))
    source_check(root, plan, source)
    require(git(root, "rev-parse", "HEAD").decode().strip() == source, "source_head")
    require(shutil.disk_usage(root).free >= plan["minimum_free_bytes"], "disk_budget")
    output.mkdir(parents=True, exist_ok=False)
    write(
        output / "initialized.json",
        dict(
            source_commit=source,
            plan_sha256=sha(encode(plan)),
            python=sys.version,
            numpy=np.__version__,
            platform=platform.platform(),
        ),
    )
    records, written = [], 0
    try:
        geometry, old, arrays = inputs(root, plan)
        points, ground = arrays["selected_xyz"], arrays["ground_poses"]
        require(len(points) == plan["selected_points"], "population")
        population = BackgroundPopulation(points, plan["population_sha256"])
        del arrays
        setup_seconds = time.monotonic() - started

        def query(state):
            return population.query(box_for_state(state, ground)[0])

        for aggregation in plan["arms"]:
            require(time.monotonic() - started < plan["producer_seconds"], "producer_deadline")
            folder = output / aggregation
            folder.mkdir()
            with (
                (folder / "attempts.jsonl").open("xb") as attempts,
                (folder / "depths.jsonl").open("xb") as depths,
            ):

                def emit(kind, row):
                    (attempts if kind == "attempt" else depths).write(encode(row))
                    require(
                        written + attempts.tell() + depths.tell()
                        < plan["max_output_bytes"] - plan["finalization_reserve_bytes"],
                        "output_budget",
                    )
                    if kind == "depth":
                        attempts.flush()
                        depths.flush()
                        if row["frame"] == 1 or row["frame"] % 5 == 0:
                            print(
                                json.dumps(
                                    dict(
                                        arm=aggregation,
                                        depth=row["frame"],
                                        survivors=row["survivors"],
                                        retained=len(row["beam"]),
                                    )
                                ),
                                flush=True,
                            )

                result = search(geometry, old, plan, lambda s: summary(query(s)), emit, aggregation)
                written += attempts.tell() + depths.tell()
            rows = result.pop("trace")
            materialization_start = time.monotonic()
            retain_trace(folder / "selected", rows, query)
            record = dict(
                aggregation=aggregation,
                width=plan["beam_width"],
                materialization_queries=len(rows),
                materialization_seconds=time.monotonic() - materialization_start,
                **result,
            )
            records.append(record)
            write(folder / "result.json", record)
            print(json.dumps(record), flush=True)
        total = sum(p.stat().st_size for p in output.rglob("*") if p.is_file())
        require(total < plan["max_output_bytes"] - 100000, "output_budget")
        require(time.monotonic() - started <= plan["producer_seconds"], "producer_deadline")
        require(rss() <= plan["max_rss_bytes"], "memory_budget")
        write(
            output / "execution.json",
            dict(
                status="completed",
                source_commit=source,
                plan_sha256=sha(encode(plan)),
                population_sha256=population.sha256,
                selected_points=len(points),
                records=records,
                setup_seconds=setup_seconds,
                elapsed_seconds=time.monotonic() - started,
                peak_rss_bytes=rss(),
                raw_bytes=total,
                new_driving_episodes=0,
                provider_spend=0,
            ),
        )
    except Exception as exc:
        write(
            output / "failure.json",
            dict(
                status="invalid",
                error=f"{type(exc).__name__}:{exc}",
                completed_records=len(records),
                elapsed_seconds=time.monotonic() - started,
            ),
        )
        raise


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--source", required=True)
    args = p.parse_args()
    run(args.root.resolve(), args.output.resolve(), args.source)
