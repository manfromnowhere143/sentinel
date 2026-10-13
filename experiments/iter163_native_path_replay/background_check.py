"""Separate scalar replay of actual native query inputs and every retained mask bit."""

import hashlib
import math
from pathlib import Path
import re

from experiments.iter150_cloud_observation.native import file, parse
from experiments.iter155_background_witness.geometry import count_points, ground_height, vertices
from experiments.iter155_background_witness.storage import get_arrays

BASE = "experiments/iter163_native_path_replay"


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def population(root):
    root = Path(root)
    binding = parse(file(root, BASE + "/BACKGROUND.json", 1024**2, content=True)[1])
    arrays, _ = get_arrays(root / binding["raw_path"], binding["arrays"])
    return binding, arrays["selected_xyz"].tolist(), arrays["ground_poses"].tolist()


def decode(value, size):
    require(type(value) is str and re.fullmatch("[0-9a-f]*", value) is not None, "mask_encoding")
    require(len(value) == 2 * ((size + 7) // 8), "mask_length")
    raw = bytes.fromhex(value)
    require(size % 8 == 0 or raw[-1] >> (size % 8) == 0, "mask_padding")
    return [bool(raw[i // 8] & (1 << (i % 8))) for i in range(size)]


def query(row, state, ego_pos, points, ground, expected_sha):
    require(
        type(ego_pos) is list
        and len(ego_pos) == 3
        and all(type(v) in (int, float) and math.isfinite(v) for v in ego_pos),
        "native_position",
    )
    require(
        row["population_sha256"] == expected_sha
        and row["population_dtype"] == "<f4"
        and row["points"] == len(points)
        and row["mask_encoding"] == "packbits_little_zero_padding",
        "native_population_identity",
    )
    observed = decode(row["mask_hex"], len(points))
    require(type(row["count"]) is int and row["count"] == sum(observed), "native_mask_count")
    require(
        type(row["result"]) is bool and row["result"] == (sum(observed) > 100), "native_mask_result"
    )
    height, nearest = ground_height(ground, state[1], state[0])
    position = [state[1], height, state[0]]
    expected_box = vertices(position, state[2])
    independent = count_points(points, row["box"])
    ground_error = max(abs(a - b) for a, b in zip(position, ego_pos))
    vertex_error = max(abs(a - b) for p, q in zip(expected_box, row["box"]) for a, b in zip(p, q))
    differences = [i for i, (a, b) in enumerate(zip(observed, independent["mask"])) if a != b]
    ambiguous = set(independent["ambiguous"])
    material = [i for i in differences if i not in ambiguous]
    geometry_matches = ground_error <= 1e-10 and vertex_error <= 1e-6
    decision_ambiguous = independent["certain_inside"] <= 100 < independent["possible_inside"]
    status = (
        "contradicted"
        if material or not geometry_matches
        else "inconclusive"
        if differences or decision_ambiguous
        else "supported"
    )
    return dict(
        status=status,
        time=row["time"],
        points=len(points),
        native_count=row["count"],
        scalar_count=independent["count"],
        collision=row["result"],
        certain_inside=independent["certain_inside"],
        possible_inside=independent["possible_inside"],
        ambiguous_points=len(ambiguous),
        mask_disagreements=len(differences),
        material_disagreements=len(material),
        ground_nearest_index=nearest,
        ground_error=ground_error,
        vertex_error=vertex_error,
        geometry_matches=geometry_matches,
        scalar_mask_sha256=hashlib.sha256(bytes(independent["mask"])).hexdigest(),
    )


def verify(root, rows, worker):
    binding, points, ground = population(root)
    require(
        worker["background_source_ast_sha256"] == binding["predicate_ast_sha256"],
        "predicate_binding",
    )
    steps = [r for r in rows if r["event"] == "step"]
    native = [r for r in worker["collision_events"] if r["kind"] == "background"]
    require(len(steps) == len(native), "background_inventory")
    reports = []
    for step, row in zip(steps, native):
        require(row["time"] == step["time"], "background_clock")
        reports.append(
            query(
                row,
                step["after"],
                step["info"]["ego_pos"],
                points,
                ground,
                binding["arrays"]["selected_xyz"]["sha256"],
            )
        )
    statuses = {r["status"] for r in reports}
    return dict(
        status="contradicted"
        if "contradicted" in statuses
        else "inconclusive"
        if "inconclusive" in statuses
        else "supported",
        executed_queries=len(reports),
        point_state_classifications=len(points) * len(reports),
        frames=reports,
        scope="Every executed native query; reset has no native background call; no continuous-clearance claim",
    )
