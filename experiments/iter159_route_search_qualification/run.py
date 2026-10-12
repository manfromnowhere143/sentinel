"""One frozen synthetic factorial acquisition. Raw precedes scalar admission."""

import argparse
import json
from pathlib import Path
import platform
import shutil
import sys
import time

import numpy as np

from experiments.iter153_action_feasibility.geometry import route_outcome
from experiments.iter153_action_feasibility.planner import transition
from experiments.iter156_background_calibration.background import (
    BackgroundPopulation,
    box_for_state,
)
from experiments.iter158_constraint_aware_search.search import summary
from .common import BASE, OLD, encode, git, read, require, rss, sha, source_check, write
from .search import search


def query_for(case):
    points = np.asarray(case["points"], dtype="<f4")
    population = BackgroundPopulation(points, sha(points.tobytes()))
    ground = np.asarray(case["ground"])

    def query(state):
        box, _, _ = box_for_state(state, ground)
        return population.query(box)

    return query


def witness(case, old, query):
    state, rows = case["geometry"]["reset"], []
    for frame, action in enumerate([None, *case["witness_actions"]]):
        if action is not None:
            state = transition(state, action, old)
        rows.append(
            dict(
                id=frame,
                parent=frame - 1 if frame else None,
                frame=frame,
                action=action,
                state=state,
                route=route_outcome(state, case["geometry"]["route"]),
                background=summary(query(state)),
                reason="clear",
            )
        )
        if rows[-1]["route"]["rc"] >= 1:
            break
    return rows


def retain_trace(folder, rows, query):
    folder.mkdir()
    write(folder / "trace.json", rows)
    for row in rows:
        result = query(row["state"])
        require(summary(result) == row["background"], "materialization_changed")
        with (folder / f"mask_{row['frame']:03d}.bin").open("xb") as stream:
            stream.write(np.packbits(result.mask, bitorder="little").tobytes())


def run(root, output, source):
    started = time.monotonic()
    plan = json.loads(read(root, BASE / "PLAN.json"))
    source_check(root, plan, source)
    require(git(root, "rev-parse", "HEAD").decode().strip() == source, "source_head")
    require(shutil.disk_usage(root).free >= plan["minimum_free_bytes"], "disk_budget")
    old = json.loads(read(root, OLD))
    cases = json.loads(read(root, BASE / "CASES.json"))
    output.mkdir(exist_ok=False)
    write(
        output / "initialized.json",
        dict(
            source_commit=source,
            python=sys.version,
            numpy=np.__version__,
            platform=platform.platform(),
            plan_sha256=sha(encode(plan)),
            cases_sha256=sha(read(root, BASE / "CASES.json")),
        ),
    )
    records = []
    try:
        for case in cases:
            query = query_for(case)
            retain_trace(output / (case["id"] + "_witness"), witness(case, old, query), query)
            for ranking, pruning in plan["arms"]:
                require(time.monotonic() - started < plan["producer_seconds"], "producer_deadline")
                name = f"{case['id']}_{ranking}_{pruning}"
                folder = output / name
                folder.mkdir()
                with (
                    (folder / "attempts.jsonl").open("xb") as attempts,
                    (folder / "depths.jsonl").open("xb") as depths,
                ):

                    def emit(kind, row):
                        (attempts if kind == "attempt" else depths).write(encode(row))

                    result = search(
                        case["geometry"],
                        old,
                        plan,
                        lambda s: summary(query(s)),
                        emit,
                        ranking,
                        pruning,
                    )
                rows = result.pop("trace")
                retain_trace(folder / "selected", rows, query)
                record = dict(
                    name=name, case=case["id"], ranking=ranking, pruning=pruning, **result
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
                records=records,
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
                error=str(exc),
                completed_records=len(records),
                elapsed_seconds=time.monotonic() - started,
            ),
        )
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--source", required=True)
    args = parser.parse_args()
    run(args.root.resolve(), args.output.resolve(), args.source)
