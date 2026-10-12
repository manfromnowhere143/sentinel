"""Scalar selected-path admission; deliberately imports no search/vector query."""

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import time

import numpy as np

from experiments.iter153_action_feasibility.check import gap, motion, near, swept
from experiments.iter155_background_witness.check import selection
from experiments.iter155_background_witness.geometry import count_points, ground_height, vertices
from experiments.iter155_background_witness.storage import read_json
from .common import BASE, git, inputs, raw_check, read, require, rss, sha, source_check, write


def verify_path(trace, geometry, old, points, ground, masks, complete, deadline):
    require(isinstance(trace, list) and 0 < len(trace) <= old["max_actions"] + 1, "trace_length")
    near(trace[0]["state"], geometry["reset"], 0)
    require(
        trace[0]["id"] == 0 and trace[0]["parent"] is None and trace[0]["action"] is None,
        "reset_identity",
    )
    obstacles = [[o[0], -o[1], o[3], o[4], -o[6]] for o in geometry["obstacles"]]
    dims = geometry["ego_dimensions"]
    max_count, progress_checks = 0, 0
    for frame, row in enumerate(trace):
        require(time.monotonic() < deadline, "checker_deadline")
        require(type(row["frame"]) is int and row["frame"] == frame, "frame_sequence")
        state = row["state"]
        require(
            len(state) == 5 and all(type(v) in (int, float) and math.isfinite(v) for v in state),
            "state_domain",
        )
        x, y, heading, speed, steering = state
        if frame:
            previous = trace[frame - 1]
            require(row["parent"] == previous["id"], "parent_chain")
            require(previous["route"]["rc"] < 1, "continued_after_completion")
            action = row["action"]
            require(
                len(action) == 2
                and all(type(v) in (int, float) and math.isfinite(v) for v in action),
                "action_domain",
            )
            near(state, motion(previous["state"], action))
            yaw = speed * math.tan(steering) / 2.7
            require(
                abs(action[0]) <= 2 + 1e-12
                and abs(action[1]) <= math.pi / 12 + 1e-12
                and abs(steering) <= math.pi / 3 + 1e-12
                and -1e-12 <= speed <= 6 + 1e-12
                and abs(yaw) <= 0.95 + 1e-12
                and abs(speed * yaw) <= 4.89 + 1e-12,
                "controls",
            )
            require(swept(previous["state"], state, dims, obstacles, old), "foreground_sweep")
        box2 = [x, y, dims[0], dims[1], heading]
        require(all(gap(box2, obstacle) > 0 for obstacle in obstacles), "foreground")
        distances = [math.hypot(p[0] - y, p[1] - x) for p in geometry["route"]]
        nearest = min(range(len(distances)), key=lambda i: (distances[i], i))
        rc = (nearest + 1) / (0.9 * len(distances))
        require(row["route"]["nearest"] == nearest, "route_index")
        near([row["route"]["distance"], row["route"]["rc"]], [distances[nearest], rc])
        require(distances[nearest] <= 10, "route_distance")
        for comparator in geometry["comparators"].values():
            if frame / 4 == comparator["hazard_time"]:
                progress_checks += 1
                require(rc >= comparator["rc"] - old["progress_slack"], "progress")
        height, _ = ground_height(ground, y, x)
        box = vertices([y, height, x], heading)
        actual = count_points(points, box)
        packed = np.packbits(np.asarray(actual["mask"], dtype=bool), bitorder="little").tobytes()
        require(masks(frame) == packed, "scalar_mask")
        claimed = row["background"]
        require(isinstance(claimed, dict), "missing_background")
        require(
            all(
                type(claimed[k]) is int and claimed[k] == actual[k]
                for k in ("count", "certain_inside", "possible_inside")
            ),
            "scalar_counts",
        )
        require(claimed["mask_sha256"] == sha(packed), "mask_identity")
        require(
            actual["possible_inside"] <= 100 and claimed["decision"] == row["reason"] == "clear",
            "background_clear",
        )
        max_count = max(max_count, actual["count"])
    require(
        type(complete) is bool and (trace[-1]["route"]["rc"] >= 1) is complete, "false_completion"
    )
    return dict(
        verified_states=len(trace),
        selected_actions=len(trace) - 1,
        max_background_count=max_count,
        progress_checks=progress_checks,
    )


def check(root, raw, raw_commit):
    started = time.monotonic()
    plan = read_json(root / BASE / "PLAN.json")
    geometry, old, arrays = inputs(root, plan)
    names = raw_check(root, raw, raw_commit, plan)
    execution = read_json(raw / "execution.json")
    source = execution["source_commit"]
    source_check(root, plan, source)
    git(root, "merge-base", "--is-ancestor", source, raw_commit)
    require(execution["plan_sha256"] == sha(read(root, BASE / "PLAN.json")), "plan_identity")
    require(
        execution["status"] == "completed" and execution["new_driving_episodes"] == 0,
        "execution_status",
    )
    require(0 < execution["elapsed_seconds"] <= plan["producer_seconds"], "producer_time")
    require(
        type(execution["peak_rss_bytes"]) is int
        and 0 < execution["peak_rss_bytes"] <= plan["max_rss_bytes"],
        "producer_memory",
    )
    require(
        type(execution["search_queries"]) is int
        and 0 < execution["search_queries"] <= plan["maximum_search_queries"],
        "query_budget",
    )
    trace = read_json(raw / "trace.json")
    expected = {
        "initialized.json",
        "execution.json",
        "attempts.jsonl",
        "depths.jsonl",
        "trace.json",
    }
    expected |= {f"mask_{i:03d}.bin" for i in range(len(trace))}
    require({Path(n).name for n in names} == expected, "raw_file_set")
    attempts = [json.loads(line) for line in read(raw, "attempts.jsonl").splitlines()]
    depths = [json.loads(line) for line in read(raw, "depths.jsonl").splitlines()]
    require(len(attempts) == execution["attempts"] + 1, "attempt_count")
    for i, row in enumerate(attempts):
        require(type(row["id"]) is int and row["id"] == i, "attempt_order")
        if i:
            require(type(row["parent"]) is int and 0 <= row["parent"] < i, "attempt_parent")
            parent = attempts[row["parent"]]
            require(
                parent["reason"] == "clear" and row["frame"] == parent["frame"] + 1, "attempt_depth"
            )
    require(Counter(r["reason"] for r in attempts[1:]) == execution["counts"], "counts")
    require(
        sum(r["background"] is not None for r in attempts) == execution["search_queries"],
        "query_count",
    )
    require(all(row == attempts[row["id"]] for row in trace), "trace_binding")
    require([d["frame"] for d in depths] == list(range(1, len(depths) + 1)), "depth_sequence")
    require(all(d["complete"] is True for d in depths[:-1]), "partial_depth")
    require(
        sum(d["complete"] is True for d in depths) == execution["completed_depth"],
        "completed_depth",
    )
    require(
        execution["stop"]
        in {"model_complete", "beam_empty", "horizon", "time_budget", "query_budget"},
        "stop",
    )
    complete = execution["stop"] == "model_complete"
    require((execution["selected"] is not None) is complete, "selection_status")
    if complete:
        require(
            execution["selected"] == trace[-1]["id"]
            and trace[-1]["frame"] == execution["completed_depth"],
            "selected_identity",
        )
    points = arrays["selected_xyz"]
    selected = selection(
        arrays["population_xyz"], arrays["population_features"], arrays["population_opacity"]
    )
    require(
        np.array_equal(selected.astype("u1"), arrays["selection"])
        and np.array_equal(points, arrays["population_xyz"][selected]),
        "selected_population",
    )
    require(
        len(points) == plan["selected_points"]
        and sha(points.tobytes()) == execution["population_sha256"],
        "population_identity",
    )
    metrics = verify_path(
        trace,
        geometry,
        old,
        points.tolist(),
        arrays["ground_poses"].tolist(),
        lambda frame: read(raw, f"mask_{frame:03d}.bin", 40000),
        complete,
        started + plan["checker_seconds"],
    )
    require(rss() <= plan["max_rss_bytes"], "checker_memory")
    require(time.monotonic() - started <= plan["checker_seconds"], "checker_deadline")
    return dict(
        status="supported" if complete else "inconclusive",
        iteration=158,
        source_commit=source,
        raw_commit=raw_commit,
        **metrics,
        attempts=execution["attempts"],
        search_queries=execution["search_queries"],
        complete_trajectories=int(complete),
        selected_points=len(points),
        counts=execution["counts"],
        stop=execution["stop"],
        elapsed_seconds=time.monotonic() - started,
        peak_rss_bytes=rss(),
        final_progress=trace[-1]["route"]["rc"],
        final_time=trace[-1]["frame"] / 4,
        all_pruning_independently_replayed=False,
        background_between_samples=None,
        new_driving_episodes=0,
        physical_occupancy=None,
        road_compliance=None,
        useful_recovery=None,
        information_benefit=None,
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
    print(result)
