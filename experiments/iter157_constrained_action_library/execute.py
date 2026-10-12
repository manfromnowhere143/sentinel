"""One bounded producer; source-model evidence, not a native driving episode."""

import argparse
from pathlib import Path
import shutil
import time

import numpy as np

from experiments.iter155_background_witness.storage import get_arrays, read_json, write_json
from experiments.iter156_background_calibration.background import (
    BackgroundPopulation,
    box_for_state,
)
from .support import query_budget
from .support import BASE, OLD, documents, git, inputs, require, rss, sha


def verdict(prior, queries, state_count):
    if prior is not True:
        require(queries == [], "unexpected_background_query")
        return "prior_constraints_failed"
    require(
        queries and [q["frame"] for q in queries] == list(range(len(queries))), "query_sequence"
    )
    require(all(q["decision"] == "clear" for q in queries[:-1]), "continued_after_rejection")
    last = queries[-1]["decision"]
    require(last in {"clear", "collision", "numerically_ambiguous"}, "query_decision")
    if last == "clear":
        require(len(queries) == state_count, "partial_candidate")
        return "qualified"
    return "background_collision" if last == "collision" else "numerically_ambiguous"


def select(rows, alternate=False):
    eligible = [r for r in rows if r["verdict"] == "qualified"]

    def key(row):
        duration, offset = row["completion_time"], abs(row["candidate"]["offset"])
        return (
            (offset, duration, row["candidate"]["id"])
            if alternate
            else (duration, offset, row["candidate"]["id"])
        )

    return min(eligible, key=key)["candidate"]["id"] if eligible else None


def collect(root, output, source):
    require(git(root, "rev-parse", "HEAD").decode().strip() == source, "source_commit")
    require(not git(root, "diff", "HEAD", "--"), "dirty_source")
    plan, _, old = documents(root)
    inputs(root, plan)
    require(shutil.disk_usage(root).free >= plan["minimum_free_bytes"], "storage_budget")
    started = time.monotonic()
    output.mkdir(parents=True, exist_ok=False)
    write_json(
        output / "initialized.json",
        dict(source_commit=source, plan_sha256=sha((root / BASE / "PLAN.json").read_bytes())),
    )
    raw155 = root / "experiments/iter155_background_witness/proof/raw"
    arrays, _ = get_arrays(raw155, read_json(raw155 / "witness.json")["arrays"])
    points = arrays["selected_xyz"]
    population = BackgroundPopulation(points, sha(points.tobytes()))
    require(len(points) == plan["selected_points"], "point_population")
    require(
        len(old["results"]) == 75 and len({r["candidate"]["id"] for r in old["results"]}) == 75,
        "candidate_population",
    )
    rows = []
    for prior in old["results"]:
        spec = prior["candidate"]
        raw = read_json(root / OLD / f"proof/search_000/{spec['id']}_1.json")
        queries = []
        if prior["eligible"]:
            for frame, state in enumerate(raw["states"]):
                if time.monotonic() - started > plan["producer_seconds"]:
                    raise TimeoutError("producer_deadline")
                box, height, nearest = box_for_state(state, arrays["ground_poses"])
                begin = time.perf_counter()
                query = population.query(box)
                elapsed = time.perf_counter() - begin
                mask = np.packbits(query.mask, bitorder="little").tobytes()
                path = f"{spec['id']}_{frame:03d}.bin"
                with (output / path).open("xb") as stream:
                    stream.write(mask)
                queries.append(
                    dict(
                        frame=frame,
                        time=frame / 4,
                        state=state,
                        box=box.tolist(),
                        height=height,
                        ground_nearest_index=nearest,
                        count=query.count,
                        certain_inside=query.certain_inside,
                        possible_inside=query.possible_inside,
                        decision=query.decision,
                        ambiguous_points=query.ambiguous_points,
                        mask=dict(path=path, sha256=sha(mask)),
                        query_seconds=elapsed,
                    )
                )
                require(rss() <= plan["max_rss_bytes"], "memory_budget")
                if query.decision != "clear":
                    break
        row = dict(
            candidate=spec,
            completion_time=prior["completion_time"],
            prior_eligible=prior["eligible"],
            verdict=verdict(prior["eligible"], queries, len(raw["states"])),
            queries=queries,
            background_complete=bool(queries and len(queries) == len(raw["states"])),
            road_compliance=None,
            physical_occupancy=None,
            useful_recovery=None,
            information_benefit=None,
        )
        rows.append(row)
        write_json(output / f"{spec['id']}.json", row)
        print(spec["id"], row["verdict"], len(queries), flush=True)
    record = dict(
        schema="sentinel.iter157.predictions.v1",
        status="completed",
        source_commit=source,
        plan_sha256=sha((root / BASE / "PLAN.json").read_bytes()),
        population_sha256=population.sha256,
        selected=select(rows),
        alternate_selected=select(rows, True),
        candidates=75,
        queried_states=sum(len(r["queries"]) for r in rows),
        elapsed_seconds=time.monotonic() - started,
        peak_rss_bytes=rss(),
        new_driving_episodes=0,
    )
    require(record["elapsed_seconds"] <= plan["producer_seconds"], "producer_deadline")
    query_budget(record["queried_states"], plan["maximum_queries"])
    write_json(output / "predictions.json", record)
    require(
        sum(p.stat().st_size for p in output.iterdir()) <= plan["max_output_bytes"], "output_budget"
    )
    return record


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--source", required=True)
    args = p.parse_args()
    print(collect(args.root.resolve(), args.output.resolve(), args.source))
