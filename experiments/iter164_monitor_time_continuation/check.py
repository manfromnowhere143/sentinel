"""Independent full-path admission and absolute-clock selection audit."""

import argparse
import json
from pathlib import Path
import time

from experiments.iter162_source_grouping_qualification.check import (
    verify_population,
    completion_check,
)
from .audit import audit_run
from .common import BASE, inputs, read, require, rss, write
from .continuation import prefix_binding, concatenate
from .path_check import verify_path
from .records import committed


def check(root, raw, commit):
    started = time.monotonic()
    plan = json.loads(read(root, BASE / "PLAN.json"))
    execution = committed(root, raw, commit, plan)
    require(execution["stage"] == "search", "stage")
    prefix, prefix_trace, identity = prefix_binding(
        root, execution["prefix_admission_commit"], plan, execution["source_commit"]
    )
    require(identity == execution["prefix_admission_sha256"], "prefix_admission_identity")
    result = json.loads(read(raw, "result.json"))
    require(result == execution["result"], "result_binding")
    require(
        result["aggregation"] == "exact"
        and type(result["width"]) is int
        and result["width"] == plan["beam_width"],
        "arm_identity",
    )
    require(0 < result["elapsed_seconds"] <= plan["per_run_seconds"] + 5, "run_time")
    suffix, retention = audit_run(raw, result, plan, prefix["branch"])
    trace = concatenate(prefix_trace, suffix)
    geometry, old, arrays = inputs(root, plan)
    points = verify_population(arrays, plan, execution).tolist()
    ground = arrays["ground_poses"].tolist()
    del arrays
    deadline = started + plan["search_checker_seconds"]
    start = plan["start_frame"]
    prefix_folder = root / BASE / "proof/prefix_raw/replica_0"
    require(
        read(prefix_folder, f"mask_{start:03d}.bin", 40000)
        == read(raw / "selected", f"mask_{start:03d}.bin", 40000),
        "branch_mask",
    )

    def mask(frame):
        return read(
            prefix_folder if frame <= start else raw / "selected", f"mask_{frame:03d}.bin", 40000
        )

    complete = result["stop"] == "model_complete"
    metrics = verify_path(trace, geometry, old, points, ground, mask, complete, deadline)
    completion_check(metrics, complete, len(geometry["comparators"]))
    require(result["materialization_queries"] == len(suffix), "materialization_count")
    expected = {
        "initialized.json",
        "execution.json",
        "result.json",
        "attempts.jsonl",
        "depths.jsonl",
        "selected/trace.json",
        *(f"selected/mask_{r['frame']:03d}.bin" for r in suffix),
    }
    require(
        {p.relative_to(raw).as_posix() for p in raw.rglob("*") if p.is_file()} == expected,
        "raw_file_set",
    )
    require(rss() <= plan["max_rss_bytes"] and time.monotonic() <= deadline, "checker_resources")
    return dict(
        iteration=164,
        phase="closed",
        status="supported" if complete else "contradicted",
        claim="Exact/24 finds a complete source-model continuation from the retained first-fire history within the frozen budget.",
        source_commit=execution["source_commit"],
        raw_commit=commit,
        prefix_admission_commit=execution["prefix_admission_commit"],
        prefix_verified_states=prefix["verified_states"],
        prefix_point_state_classifications=prefix["point_state_classifications"],
        start_frame=start,
        first_fire_time=start / 4,
        runs=1,
        complete_runs=int(complete),
        incomplete_runs=int(not complete),
        invalid_runs=0,
        suffix_actions=len(suffix) - 1,
        attempts=result["attempts"],
        search_queries=result["queries"],
        selected_points=len(points),
        point_state_classifications=metrics["verified_states"] * len(points),
        result=result,
        retention=retention,
        final_absolute_time=trace[-1]["frame"] / 4,
        final_progress=trace[-1]["route"]["rc"],
        elapsed_seconds=time.monotonic() - started,
        peak_rss_bytes=rss(),
        **metrics,
        source_infeasibility=None,
        native_continuation=None,
        real_time_availability=None,
        road_compliance=None,
        information_benefit=None,
        transfer=None,
        competitive_superiority=None,
        new_driving_episodes=0,
        provider_spend=0,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--raw", type=Path, required=True)
    p.add_argument("--raw-commit", required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = check(args.root.resolve(), args.raw.resolve(), args.raw_commit)
    write(args.output, result)
    print(json.dumps(result), flush=True)
