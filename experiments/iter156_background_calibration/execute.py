"""Collect accelerated predictions on the prospectively fixed historical inputs."""

import argparse
import hashlib
import json
from pathlib import Path
import platform
import resource
import shutil
import subprocess
import time

import numpy as np

from .background import BackgroundPopulation, box_for_state
from experiments.iter150_cloud_observation.native import file, parse
from experiments.iter155_background_witness.storage import get_arrays, read_json, write_json


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_inputs(root, plan):
    for name, expected in plan["inputs"].items():
        data = file(root, name, 16 * 1024**2, content=True)[1]
        if sha(data) != expected:
            raise ValueError("input_identity:" + name)
    raw155 = root / "experiments/iter155_background_witness/proof/raw"
    witness = read_json(raw155 / "witness.json")
    arrays, _ = get_arrays(raw155, witness["arrays"])
    if len(arrays["selected_xyz"]) != plan["selected_points"]:
        raise ValueError("selected_population_size")
    rows = []
    for trace in plan["traces"]:
        data = file(root, trace["path"], 8 * 1024**2, content=True)[1]
        steps = [parse(line) for line in data.splitlines()]
        steps = [row for row in steps if row.get("event") == "step"]
        if len(steps) != trace["steps"]:
            raise ValueError("trace_step_count")
        for row in steps:
            records = row.get("collision_records")
            native = None
            if records is not None:
                background = [r for r in records if r["kind"] == "background"]
                if len(background) != 1 or type(background[0]["result"]) is not bool:
                    raise ValueError("native_background_type")
                native = background[0]["result"]
            rows.append(
                {
                    "trace": trace["path"],
                    "frame": row["frame"],
                    "time": row["time"],
                    "state": row["after"],
                    "ego_box": row["info"]["ego_box"],
                    "native_collision": row["info"]["collision"],
                    "native_background": native,
                }
            )
    if len(rows) != plan["step_bindings"]:
        raise ValueError("binding_population")
    unique = list(dict.fromkeys(tuple(row["state"]) for row in rows))
    if len(unique) != plan["unique_states"]:
        raise ValueError("state_population")
    return arrays, rows, unique


def collect(root, plan_path, output, source_commit):
    root, plan_path, output = Path(root), Path(plan_path), Path(output)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    if head != source_commit:
        raise ValueError("source_commit")
    subprocess.run(
        ["git", "diff", "--exit-code", "HEAD", "--"],
        cwd=root,
        check=True,
        stdout=subprocess.DEVNULL,
    )
    plan = read_json(plan_path)
    if shutil.disk_usage(root).free < plan["minimum_free_bytes"]:
        raise ValueError("storage_budget")
    start = time.monotonic()
    arrays, rows, unique = read_inputs(root, plan)
    points = arrays["selected_xyz"]
    population = BackgroundPopulation(points, sha(points.tobytes()))
    output.mkdir(parents=True, exist_ok=False)
    records = []
    for index, state in enumerate(unique):
        if time.monotonic() - start > plan["producer_seconds"]:
            raise TimeoutError("producer_deadline")
        box, height, nearest = box_for_state(state, arrays["ground_poses"])
        begin = time.perf_counter()
        result = population.query(box)
        elapsed = time.perf_counter() - begin
        mask = np.packbits(result.mask, bitorder="little").tobytes()
        name = f"mask_{index:03d}.bin"
        with (output / name).open("xb") as stream:
            stream.write(mask)
        records.append(
            {
                "index": index,
                "state": list(state),
                "box": box.tolist(),
                "height": height,
                "ground_nearest_index": nearest,
                "count": result.count,
                "predicate_collision": result.predicate_collision,
                "certain_inside": result.certain_inside,
                "possible_inside": result.possible_inside,
                "ambiguous_points": result.ambiguous_points,
                "decision": result.decision,
                "minimum_absolute_projection_margin": result.minimum_absolute_projection_margin,
                "mask": {"path": name, "bytes": len(mask), "sha256": sha(mask)},
                "query_seconds": elapsed,
            }
        )
    record = {
        "schema": "sentinel.iter156.predictions.v1",
        "status": "completed",
        "source_commit": source_commit,
        "plan_sha256": sha(plan_path.read_bytes()),
        "population_sha256": population.sha256,
        "selected_points": len(points),
        "new_driving_episodes": 0,
        "rows": rows,
        "states": records,
        "elapsed_seconds": time.monotonic() - start,
        "peak_rss_bytes": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        * (1 if platform.system() == "Darwin" else 1024),
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "platform": platform.platform(),
            "processor": platform.processor(),
        },
        "scope": "Previously exposed development prefixes; no new independent scene.",
    }
    if record["peak_rss_bytes"] > plan["max_rss_bytes"]:
        raise ValueError("memory_budget")
    if record["elapsed_seconds"] > plan["producer_seconds"]:
        raise TimeoutError("producer_deadline")
    write_json(output / "predictions.json", record)
    if sum(p.stat().st_size for p in output.iterdir()) > plan["max_output_bytes"]:
        raise ValueError("output_budget")
    print(
        json.dumps(
            {
                key: record[key]
                for key in ("status", "source_commit", "selected_points", "elapsed_seconds")
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args()
    collect(args.root, args.plan, args.output, args.source_commit)
