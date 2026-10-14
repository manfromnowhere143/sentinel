"""Independent scalar physics and historical selection replay after raw commitment."""

import argparse
import json
from pathlib import Path
import struct
import time

import numpy as np

from experiments.iter155_background_witness.geometry import count_points
from experiments.iter162_source_grouping_qualification.check import (
    verify_population,
    completion_check,
)
from experiments.iter164_monitor_time_continuation.audit import audit_run
from experiments.iter164_monitor_time_continuation.continuation import concatenate
from .candidates import candidates, prefix_for
from .common import BASE, inputs, read, require, rss, write
from .records import committed
from .path_check import verify_path


class ScalarCache:
    """Cache only this checker's exact vertices against one fixed point population."""

    def __init__(self, points):
        self.points, self.entries, self.evaluated, self.reused = points, {}, 0, 0

    def __call__(self, points, box):
        require(points is self.points, "cache_population")
        key = struct.pack(">24d", *(v for point in box for v in point))
        if key not in self.entries:
            actual = count_points(points, box)
            packed = np.packbits(actual["mask"], bitorder="little").tobytes()
            self.entries[key] = (
                {k: actual[k] for k in ("count", "certain_inside", "possible_inside")},
                packed,
            )
            self.evaluated += 1
        else:
            self.reused += 1
        counts, packed = self.entries[key]
        return dict(
            **counts,
            mask=np.unpackbits(np.frombuffer(packed, dtype="u1"), bitorder="little")[: len(points)],
        )


def check(root, commit):
    started = time.monotonic()
    plan = json.loads(read(root, BASE / "PLAN.json"))
    raw = root / BASE / "proof/search_raw"
    execution = committed(root, raw, commit, plan)
    geometry, old, arrays = inputs(root, plan)
    points = verify_population(arrays, plan, execution).tolist()
    ground = arrays["ground_poses"].tolist()
    del arrays
    cache = ScalarCache(points)
    schedule, nodes = candidates(root)
    require(schedule == json.loads(read(root, BASE / "CANDIDATES.json")), "candidate_schedule")
    require(len(execution["records"]) == len(schedule), "schedule_length")
    records = []
    deadline = started + plan["search_checker_seconds"]
    for entry, recorded in zip(schedule, execution["records"]):
        require(all(recorded[k] == v for k, v in entry.items()), "schedule_order")
        name = f"{entry['cohort']}_{entry['node_id']:04d}"
        require(recorded["name"] == name, "record_name")
        if recorded["status"] == "censored":
            require(not (raw / name).exists(), "censored_directory")
            records.append(recorded)
            continue
        folder = raw / name
        result = json.loads(read(folder, "result.json"))
        require(
            result == recorded and result["aggregation"] == "exact" and result["width"] == 24,
            "record_binding",
        )
        require(0 < result["elapsed_seconds"] <= plan["per_run_seconds"] + 5, "run_time")
        prefix = prefix_for(root, nodes, entry["node_id"])
        branch = dict(frame=27, time=6.75, state=prefix[-1]["state"])
        suffix, retention = audit_run(folder, result, plan, branch)
        joined = json.loads(read(folder / "joined", "trace.json"))
        require(joined == concatenate(prefix, suffix), "joined_binding")
        complete = result["stop"] == "model_complete"
        metrics = verify_path(
            joined,
            geometry,
            old,
            points,
            ground,
            lambda i: read(folder / "joined", f"mask_{i:03d}.bin", 40000),
            complete,
            deadline,
            classifier=cache,
        )
        for row in suffix:
            require(
                read(folder / "selected", f"mask_{row['frame']:03d}.bin", 40000)
                == read(folder / "joined", f"mask_{row['frame']:03d}.bin", 40000),
                "suffix_mask",
            )
        completion_check(metrics, complete, len(geometry["comparators"]))
        require(
            result["materialization_queries"] == len(joined) + len(suffix), "materialization_count"
        )
        records.append(
            dict(
                **result,
                **metrics,
                complete=complete,
                retention=retention,
                final_progress=joined[-1]["route"]["rc"],
                final_time=joined[-1]["frame"] / 4,
            )
        )
        require(rss() <= plan["max_rss_bytes"], "checker_memory")
        print(
            json.dumps(
                dict(
                    name=name,
                    complete=complete,
                    scalar_states=cache.evaluated,
                    reused_states=cache.reused,
                )
            ),
            flush=True,
        )
    discarded = [r for r in records if r["cohort"] == "discarded" and r["status"] == "observed"]
    require(time.monotonic() <= deadline, "checker_deadline")
    return dict(
        iteration=165,
        phase="closed",
        status="supported"
        if any(r["complete"] for r in discarded)
        else ("contradicted" if len(discarded) == 25 else "inconclusive"),
        claim="At least one of all 25 discarded frame-27 maximum-braking prefixes yields an independently admitted complete exact/24 continuation within its frozen budget.",
        source_commit=execution["source_commit"],
        raw_commit=commit,
        records=records,
        scalar_evaluated_states=cache.evaluated,
        scalar_reused_states=cache.reused,
        point_state_classifications=cache.evaluated * len(points),
        attempts=sum(r.get("attempts", 0) for r in records),
        search_queries=sum(r.get("queries", 0) for r in records),
        elapsed_seconds=time.monotonic() - started,
        peak_rss_bytes=rss(),
        global_infeasibility=None,
        causal_explanation_of_original_miss=None,
        native_recovery=None,
        superiority=None,
        new_driving_episodes=0,
        provider_spend=0,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--raw-commit", required=True)
    a = p.parse_args()
    root = a.root.resolve()
    result = check(root, a.raw_commit)
    write(root / BASE / "proof/admission.json", result)
    print(json.dumps({k: v for k, v in result.items() if k != "records"}), flush=True)
