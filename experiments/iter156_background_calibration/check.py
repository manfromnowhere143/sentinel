"""Separate scalar admission of full masks, source geometry and native labels."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import platform
import resource
import statistics
import subprocess
import time

import numpy as np

from experiments.iter150_cloud_observation.native import file, parse
from experiments.iter155_background_witness.check import selection
from experiments.iter155_background_witness.geometry import count_points, ground_height, vertices
from experiments.iter155_background_witness.storage import get_arrays, read_json, write_json


def sha(data):
    return hashlib.sha256(data).hexdigest()


def check(root, plan_path, raw, raw_commit):
    """Imports no candidate query, producer, or native simulator."""
    root, plan_path, raw = Path(root), Path(plan_path), Path(raw)
    plan = read_json(plan_path)
    for name, expected in plan["inputs"].items():
        data = file(root, name, 16 * 1024**2, content=True)[1]
        if sha(data) != expected:
            raise ValueError("input_identity:" + name)
    relative = raw.relative_to(root).as_posix()
    names = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", raw_commit, "--", relative],
        cwd=root,
        text=True,
    ).splitlines()
    if set(names) != {p.relative_to(root).as_posix() for p in raw.iterdir()}:
        raise ValueError("raw_commit_inventory")
    for name in names:
        if (
            subprocess.check_output(["git", "show", raw_commit + ":" + name], cwd=root)
            != (root / name).read_bytes()
        ):
            raise ValueError("raw_not_committed")
    data = read_json(raw / "predictions.json", 16 * 1024**2)
    if sum(p.stat().st_size for p in raw.iterdir()) > plan["max_output_bytes"]:
        raise ValueError("output_budget")
    if (
        type(data["peak_rss_bytes"]) is not int
        or not 0 < data["peak_rss_bytes"] <= plan["max_rss_bytes"]
        or not 0 < data["elapsed_seconds"] <= plan["producer_seconds"]
    ):
        raise ValueError("producer_resource_budget")
    source_commit = data["source_commit"]
    if len(source_commit) != 40 or any(c not in "0123456789abcdef" for c in source_commit):
        raise ValueError("source_commit_encoding")
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", source_commit, raw_commit], cwd=root, check=True
    )
    for name in [plan_path.relative_to(root).as_posix(), *plan["source_files"]]:
        committed = subprocess.check_output(["git", "show", source_commit + ":" + name], cwd=root)
        actual = file(root, name, 16 * 1024**2, content=True)[1]
        if committed != actual:
            raise ValueError("source_not_frozen:" + name)
    expected_names = {relative + "/predictions.json"} | {
        relative + f"/mask_{index:03d}.bin" for index in range(plan["unique_states"])
    }
    if set(names) != expected_names:
        raise ValueError("raw_file_set")
    if data["status"] != "completed" or data["new_driving_episodes"] != 0:
        raise ValueError("producer_scope")
    if data["plan_sha256"] != sha(plan_path.read_bytes()):
        raise ValueError("plan_identity")
    raw155 = root / "experiments/iter155_background_witness/proof/raw"
    arrays, _ = get_arrays(raw155, read_json(raw155 / "witness.json")["arrays"])
    points = arrays["selected_xyz"]
    selected = selection(
        arrays["population_xyz"], arrays["population_features"], arrays["population_opacity"]
    )
    if not np.array_equal(selected.astype("u1"), arrays["selection"]) or not np.array_equal(
        points, arrays["population_xyz"][selected]
    ):
        raise ValueError("selected_population")
    if len(points) != plan["selected_points"] or sha(points.tobytes()) != data["population_sha256"]:
        raise ValueError("population_identity")
    # Reconstruct source bindings directly, not from the producer's rows.
    bindings = []
    for trace in plan["traces"]:
        blob = file(root, trace["path"], 8 * 1024**2, content=True)[1]
        steps = [parse(line) for line in blob.splitlines()]
        steps = [r for r in steps if r.get("event") == "step"]
        if len(steps) != trace["steps"]:
            raise ValueError("trace_step_count")
        if [r["frame"] for r in steps] != list(range(1, len(steps) + 1)):
            raise ValueError("trace_frame_order")
        for r in steps:
            native = None
            if "collision_records" in r:
                values = [c for c in r["collision_records"] if c["kind"] == "background"]
                if len(values) != 1 or type(values[0]["result"]) is not bool:
                    raise ValueError("native_boolean")
                if values[0]["time"] != r["time"]:
                    raise ValueError("native_time_binding")
                native = values[0]["result"]
            if type(r["info"]["collision"]) is not bool:
                raise ValueError("composite_boolean")
            bindings.append(
                {
                    "trace": trace["path"],
                    "frame": r["frame"],
                    "time": r["time"],
                    "state": r["after"],
                    "ego_box": r["info"]["ego_box"],
                    "native_collision": r["info"]["collision"],
                    "native_background": native,
                }
            )
    if data["rows"] != bindings or len(bindings) != plan["step_bindings"]:
        raise ValueError("binding_population")
    unique = list(dict.fromkeys(tuple(r["state"]) for r in bindings))
    if len(unique) != plan["unique_states"] or len(data["states"]) != len(unique):
        raise ValueError("state_population")
    point_list = points.tolist()
    results, disagreements = [], []
    label_counts = {
        "direct_background": sum(r["native_background"] is not None for r in bindings),
        "negative_composite_implication": sum(
            r["native_background"] is None and not r["native_collision"] for r in bindings
        ),
        "unattributed_collision": sum(
            r["native_background"] is None and r["native_collision"] for r in bindings
        ),
    }
    if label_counts != plan["label_counts"]:
        raise ValueError("label_population")
    start = time.monotonic()
    for index, (state, observed) in enumerate(zip(unique, data["states"])):
        if time.monotonic() - start > plan["checker_seconds"]:
            raise TimeoutError("checker_deadline")
        if observed["index"] != index or observed["state"] != list(state):
            raise ValueError("state_order")
        if (
            type(observed["query_seconds"]) not in (int, float)
            or not math.isfinite(observed["query_seconds"])
            or observed["query_seconds"] <= 0
        ):
            raise ValueError("timing_value")
        height, nearest = ground_height(arrays["ground_poses"], state[1], state[0])
        if nearest != observed["ground_nearest_index"] or abs(height - observed["height"]) > 1e-10:
            raise ValueError("ground_geometry")
        box = vertices([state[1], height, state[0]], state[2])
        if np.max(np.abs(np.array(box) - np.array(observed["box"]))) > 1e-6:
            raise ValueError("vertex_geometry")
        # Evaluate the exact retained candidate vertices, after separate geometry check.
        begin = time.perf_counter()
        scalar = count_points(point_list, observed["box"])
        scalar_seconds = time.perf_counter() - begin
        mask_row = observed["mask"]
        if mask_row["path"] != f"mask_{index:03d}.bin":
            raise ValueError("mask_path")
        packed = file(raw, mask_row["path"], (len(points) + 7) // 8, content=True)[1]
        if len(packed) != mask_row["bytes"] or sha(packed) != mask_row["sha256"]:
            raise ValueError("mask_identity")
        mask = np.unpackbits(np.frombuffer(packed, dtype="u1"), bitorder="little")
        if len(mask) != ((len(points) + 7) // 8) * 8 or np.any(mask[len(points) :]):
            raise ValueError("mask_encoding")
        if not np.array_equal(mask[: len(points)], scalar["mask"]):
            raise ValueError("full_mask_disagreement")
        for key in ("count", "certain_inside", "possible_inside"):
            if type(observed[key]) is not int or observed[key] != scalar[key]:
                raise ValueError("scalar_" + key)
        expected_decision = (
            "collision"
            if scalar["certain_inside"] > 100
            else ("clear" if scalar["possible_inside"] <= 100 else "numerically_ambiguous")
        )
        if (
            type(observed["predicate_collision"]) is not bool
            or observed["predicate_collision"] != scalar["collision"]
            or observed["ambiguous_points"] != len(scalar["ambiguous"])
            or observed["decision"] != expected_decision
        ):
            raise ValueError("predicate_or_ambiguity")
        matched = [r for r in bindings if tuple(r["state"]) == state]
        for row in matched:
            expected_ego = [state[0], -state[1], -height, 1.6, 3.0, 1.5, -state[2]]
            if (
                len(row["ego_box"]) != 7
                or max(abs(x - y) for x, y in zip(row["ego_box"], expected_ego)) > 1e-10
            ):
                raise ValueError("historical_height")
            native = row["native_background"]
            if native is not None and native != scalar["collision"]:
                disagreements.append(
                    {**row, "comparison": "direct_background", "model_count": scalar["count"]}
                )
            elif native is None and not row["native_collision"] and scalar["collision"]:
                disagreements.append(
                    {
                        **row,
                        "comparison": "negative_composite_implication",
                        "model_count": scalar["count"],
                    }
                )
        results.append(
            {
                "index": index,
                "bindings": len(matched),
                "count": scalar["count"],
                "decision": expected_decision,
                "ambiguous_points": len(scalar["ambiguous"]),
                "scalar_seconds": scalar_seconds,
                "accelerated_seconds": observed["query_seconds"],
            }
        )
        print(json.dumps(results[-1]), flush=True)
    uncertain = [r["index"] for r in results if r["decision"] == "numerically_ambiguous"]
    peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * (
        1 if platform.system() == "Darwin" else 1024
    )
    if peak > plan["max_rss_bytes"]:
        raise ValueError("memory_budget")
    if time.monotonic() - start > plan["checker_seconds"]:
        raise TimeoutError("checker_deadline")
    return {
        "schema": "sentinel.iter156.admission.v1",
        "status": "contradicted"
        if disagreements
        else ("inconclusive" if uncertain else "supported"),
        "raw_commit": raw_commit,
        "source_commit": data["source_commit"],
        "step_bindings": len(bindings),
        "unique_states": len(unique),
        "selected_points": len(points),
        "full_scalar_mask_comparisons": len(results),
        "label_counts": label_counts,
        "native_boolean_disagreements": disagreements,
        "numerically_ambiguous_states": uncertain,
        "states": results,
        "elapsed_seconds": time.monotonic() - start,
        "peak_rss_bytes": peak,
        "timing": {
            "accelerated_median_seconds": statistics.median(
                r["accelerated_seconds"] for r in results
            ),
            "scalar_median_seconds": statistics.median(r["scalar_seconds"] for r in results),
            "accelerated_range_seconds": [
                min(r["accelerated_seconds"] for r in results),
                max(r["accelerated_seconds"] for r in results),
            ],
            "scalar_range_seconds": [
                min(r["scalar_seconds"] for r in results),
                max(r["scalar_seconds"] for r in results),
            ],
            "scope": "Separate local producer/checker processes; exploratory cost, no real-time guarantee.",
        },
        "physical_occupancy": None,
        "road_compliance": None,
        "useful_recovery": None,
        "information_benefit": None,
        "new_driving_episodes": 0,
        "independent_scenes": 1,
        "scope": "Previously exposed one-scene calibration. Native full masks remain two Iter155 witnesses.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--raw-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = check(args.root, args.plan, args.raw, args.raw_commit)
    write_json(args.output, result)
    print(json.dumps({"status": result["status"], "step_bindings": result["step_bindings"]}))
