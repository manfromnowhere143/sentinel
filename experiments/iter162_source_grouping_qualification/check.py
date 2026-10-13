"""Independent source-population, scalar-path and mechanical selection admission."""

import argparse
import json
from pathlib import Path
import time

import numpy as np

from experiments.iter155_background_witness.check import selection
from experiments.iter158_constraint_aware_search.check import verify_path
from .audit import audit_run
from .common import BASE, encode, git, inputs, read, require, rss, sha, source_check, write


def verify_population(arrays, plan, execution):
    selected = selection(
        arrays["population_xyz"], arrays["population_features"], arrays["population_opacity"]
    )
    points = arrays["selected_xyz"]
    require(
        np.array_equal(selected.astype("u1"), arrays["selection"])
        and np.array_equal(points, arrays["population_xyz"][selected]),
        "selected_population",
    )
    require(
        len(points) == plan["selected_points"] == execution["selected_points"]
        and sha(points.tobytes()) == plan["population_sha256"] == execution["population_sha256"],
        "population_identity",
    )
    return points


def completion_check(metrics, complete, required):
    if complete:
        require(metrics["progress_checks"] == required, "missing_completion_checkpoint")


def check(root, raw, commit):
    started = time.monotonic()
    plan = json.loads(read(root, BASE / "PLAN.json"))
    names = (
        git(root, "ls-tree", "-r", "--name-only", commit, "--", raw.relative_to(root).as_posix())
        .decode()
        .splitlines()
    )
    require(
        set(names) == {p.relative_to(root).as_posix() for p in raw.rglob("*") if p.is_file()},
        "raw_inventory",
    )
    total = 0
    for name in names:
        data = read(root, name)
        total += len(data)
        require(git(root, "show", commit + ":" + name) == data, "raw_not_committed")
    require(total <= plan["max_output_bytes"], "output_budget")
    execution = json.loads(read(raw, "execution.json"))
    initialized = json.loads(read(raw, "initialized.json"))
    source_check(root, plan, execution["source_commit"])
    git(root, "merge-base", "--is-ancestor", execution["source_commit"], commit)
    require(
        execution["status"] == "completed"
        and execution["new_driving_episodes"] == 0
        and execution["provider_spend"] == 0,
        "execution_scope",
    )
    require(
        execution["plan_sha256"] == initialized["plan_sha256"] == sha(encode(plan))
        and initialized["source_commit"] == execution["source_commit"],
        "initialization_identity",
    )
    require(0 < execution["elapsed_seconds"] <= plan["producer_seconds"], "producer_time")
    require(0 < execution["peak_rss_bytes"] <= plan["max_rss_bytes"], "producer_memory")
    geometry, old, arrays = inputs(root, plan)
    points = verify_population(arrays, plan, execution).tolist()
    ground = arrays["ground_poses"].tolist()
    del arrays
    deadline = started + plan["checker_seconds"]
    expected, records = {"execution.json", "initialized.json"}, []
    for aggregation in plan["arms"]:
        folder = raw / aggregation
        result = json.loads(read(folder, "result.json"))
        require(
            result["aggregation"] == aggregation
            and type(result["width"]) is int
            and result["width"] == plan["beam_width"],
            "arm_identity",
        )
        require(0 < result["elapsed_seconds"] <= plan["per_run_seconds"] + 5, "run_time")
        trace, retention = audit_run(folder, result, plan)
        complete = result["stop"] == "model_complete"
        metrics = verify_path(
            trace,
            geometry,
            old,
            points,
            ground,
            lambda i: read(folder / "selected", f"mask_{i:03d}.bin", 40000),
            complete,
            deadline,
        )
        completion_check(metrics, complete, len(geometry["comparators"]))
        require(result["materialization_queries"] == len(trace), "materialization_count")
        records.append(
            dict(
                **result,
                **metrics,
                complete=complete,
                retention=retention,
                final_progress=trace[-1]["route"]["rc"],
                final_time=trace[-1]["frame"] / 4,
            )
        )
        for name in [
            "attempts.jsonl",
            "depths.jsonl",
            "result.json",
            "selected/trace.json",
            *(f"selected/mask_{i:03d}.bin" for i in range(len(trace))),
        ]:
            expected.add(aggregation + "/" + name)
        require(rss() <= plan["max_rss_bytes"], "checker_memory")
    require(
        len(execution["records"]) == len(records)
        and all(
            all(admitted[k] == v for k, v in recorded.items())
            for recorded, admitted in zip(execution["records"], records)
        ),
        "record_binding",
    )
    require(
        {p.relative_to(raw).as_posix() for p in raw.rglob("*") if p.is_file()} == expected,
        "raw_file_set",
    )
    require(time.monotonic() <= deadline, "checker_deadline")
    candidate = next(r for r in records if r["aggregation"] == "exact")
    states = sum(r["verified_states"] for r in records)
    return dict(
        iteration=162,
        phase="closed",
        status="supported" if candidate["complete"] else "contradicted",
        claim="Exact state grouping at width 24 finds a complete admitted path on the retained source model within the frozen envelope.",
        source_commit=execution["source_commit"],
        raw_commit=commit,
        selected_points=len(points),
        runs=len(records),
        complete_runs=sum(r["complete"] for r in records),
        incomplete_runs=sum(not r["complete"] for r in records),
        candidate_completions=int(candidate["complete"]),
        invalid_runs=0,
        verified_states=states,
        point_state_classifications=states * len(points),
        progress_checks=sum(r["progress_checks"] for r in records),
        attempts=sum(r["attempts"] for r in records),
        search_queries=sum(r["queries"] for r in records),
        records=records,
        elapsed_seconds=time.monotonic() - started,
        peak_rss_bytes=rss(),
        all_pruning_independently_replayed=False,
        beam_selection_from_retained_scores_replayed=True,
        infeasibility=None,
        native_recovery=None,
        background_between_samples=None,
        road_compliance=None,
        information_benefit=None,
        transfer=None,
        new_driving_episodes=0,
        provider_spend=0,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True, type=Path)
    p.add_argument("--raw", required=True, type=Path)
    p.add_argument("--raw-commit", required=True)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    result = check(args.root.resolve(), args.raw.resolve(), args.raw_commit)
    write(args.output, result)
    print(json.dumps({k: v for k, v in result.items() if k != "records"}), flush=True)
