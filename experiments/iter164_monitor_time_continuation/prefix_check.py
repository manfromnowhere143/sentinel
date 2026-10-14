"""Independent historical and full scalar prefix qualification before search."""

import argparse
import json
from pathlib import Path
import time

from experiments.iter162_source_grouping_qualification.check import verify_population
from .binding import bind_history
from .common import BASE, inputs, read, require, rss, write
from .path_check import verify_path
from .records import committed


def check(root, raw, commit):
    started = time.monotonic()
    plan = json.loads(read(root, BASE / "PLAN.json"))
    execution = committed(root, raw, commit, plan)
    require(execution["stage"] == "prefix", "stage")
    geometry, old, arrays = inputs(root, plan)
    points = verify_population(arrays, plan, execution).tolist()
    ground = arrays["ground_poses"].tolist()
    del arrays
    deadline = started + plan["prefix_checker_seconds"]
    records, traces = [], []
    expected = {"initialized.json", "execution.json"}
    require(len(execution["records"]) == len(plan["histories"]) == 2, "prefix_record_count")
    for index, spec in enumerate(plan["histories"]):
        folder = raw / f"replica_{index}"
        trace = json.loads(read(folder, "trace.json"))
        binding = bind_history(root, spec, trace, geometry, plan)
        result = verify_path(
            trace,
            geometry,
            old,
            points,
            ground,
            lambda frame: read(folder, f"mask_{frame:03d}.bin", 40000),
            False,
            deadline,
            allow_rejections=True,
        )
        observed = execution["records"][index]
        require(
            observed
            == dict(
                episode=spec["episode"],
                states=len(trace),
                queries=2 * len(trace),
                eligible=result["eligible"],
            ),
            "prefix_record_binding",
        )
        records.append(dict(**binding, **result))
        traces.append(trace)
        expected |= {
            f"replica_{index}/trace.json",
            *(f"replica_{index}/mask_{frame:03d}.bin" for frame in range(len(trace))),
        }
        require(rss() <= plan["max_rss_bytes"], "checker_memory")
        print(
            json.dumps(
                dict(
                    episode=spec["episode"],
                    eligible=result["eligible"],
                    verified_states=result["verified_states"],
                )
            ),
            flush=True,
        )
    require(traces[0] == traces[1], "prefix_replica_agreement")
    require(
        {p.relative_to(raw).as_posix() for p in raw.rglob("*") if p.is_file()} == expected,
        "raw_file_set",
    )
    require(time.monotonic() <= deadline, "checker_deadline")
    supported = all(r["eligible"] for r in records)
    return dict(
        iteration=164,
        status="supported" if supported else "contradicted",
        phase="prefix_qualified" if supported else "prefix_rejected",
        source_commit=execution["source_commit"],
        raw_commit=commit,
        records=records,
        branch=dict(
            frame=plan["start_frame"], time=plan["start_frame"] / 4, state=traces[0][-1]["state"]
        ),
        verified_states=sum(r["verified_states"] for r in records),
        point_state_classifications=sum(r["verified_states"] for r in records) * len(points),
        population_sha256=plan["population_sha256"],
        elapsed_seconds=time.monotonic() - started,
        peak_rss_bytes=rss(),
        new_driving_episodes=0,
        provider_spend=0,
        scope="Two retained historical prefixes, not new episodes or a continuation result",
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
    print(json.dumps({k: v for k, v in result.items() if k != "records"}), flush=True)
