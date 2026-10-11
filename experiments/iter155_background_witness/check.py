"""Independent admission of retained point selection, box geometry and collision counts."""

from pathlib import Path
import subprocess

import numpy as np

from .geometry import count_points, ground_height, vertices
from .storage import digest, get_arrays, read_json
from experiments.iter150_cloud_observation.native import file, parse


def selection(xyz, features, opacity):
    n = len(xyz)
    if (
        xyz.shape != (n, 3)
        or features.ndim != 2
        or features.shape[0] != n
        or not 1 < features.shape[1] <= 32
        or opacity.shape != (n,)
    ):
        raise ValueError("population_shape")
    if any(
        a.dtype != np.dtype("<f4") or not np.isfinite(a).all() for a in (xyz, features, opacity)
    ):
        raise ValueError("population_dtype_or_values")
    if np.any((opacity < 0) | (opacity > 1)):
        raise ValueError("opacity_range")
    labels = np.argmax(features, axis=1)
    return (labels > 1) & (labels != 10) & (opacity > np.float32(0.8))


def historical(root, plan):
    for frame in plan["frames"]:
        data = file(root, frame["trace_path"], 8 * 1024**2, content=True)[1]
        if digest(data) != frame["trace_sha256"]:
            raise ValueError("historical_identity")
        rows = [parse(line) for line in data.splitlines()]
        matches = [r for r in rows if r["event"] == "step" and r["frame"] == frame["frame"]]
        if len(matches) != 1:
            raise ValueError("historical_frame")
        row = matches[0]
        actual = {
            "time": row["time"],
            "state": row["after"],
            "ego_pos": row["info"]["ego_pos"],
            "ego_box": row["info"]["ego_box"],
            "background": row["collision_records"][0]["result"],
        }
        if any(frame[k] != v for k, v in actual.items()):
            raise ValueError("historical_values")
    for index in plan["unique_frames"]:
        replicas = [f for f in plan["frames"] if f["frame"] == index]
        if len(replicas) != 2 or {r["replica"] for r in replicas} != {1, 2}:
            raise ValueError("replica_binding")
        if any(
            replicas[0][key] != replicas[1][key]
            for key in ("time", "state", "ego_pos", "ego_box", "background")
        ):
            raise ValueError("historical_replica_difference")


def verify(root, raw, plan, assets, raw_commit=None):
    root, raw = Path(root), Path(raw)
    historical(root, plan)
    if raw_commit:
        relative = raw.relative_to(root).as_posix()
        names = (
            subprocess.check_output(
                ["git", "ls-tree", "-r", "--name-only", raw_commit, "--", relative], cwd=root
            )
            .decode()
            .splitlines()
        )
        actual = {p.relative_to(root).as_posix() for p in raw.iterdir() if p.is_file()}
        if set(names) != actual:
            raise ValueError("raw_commit_inventory")
        for name in names:
            if (
                subprocess.check_output(["git", "show", raw_commit + ":" + name], cwd=root)
                != (root / name).read_bytes()
            ):
                raise ValueError("raw_not_committed")
    record = read_json(raw / "witness.json")
    if (
        record["status"] != "completed"
        or record["new_driving_episodes"] != 0
        or record["constructor_reset_step_render_calls"] != 0
    ):
        raise ValueError("worker_scope_or_status")
    if record["preflight_files"] != len(assets) or record["postflight_files"] != len(assets):
        raise ValueError("source_inventory")
    config = record["configuration"]
    for name, key in [("scene.pth", "scene_sha256"), ("ground_param.pkl", "ground_sha256")]:
        expected = assets[
            "/datasets/nuscenes-full/hugsim/extracted/scenes/nuscenes/scene-0013/" + name
        ]["sha256"]
        if config[key] != expected:
            raise ValueError("scene_binding")
    arrays, seen = get_arrays(raw, record["arrays"])
    required = {
        "population_xyz",
        "population_features",
        "population_opacity",
        "selection",
        "selected_xyz",
        "ground_poses",
        "box_12",
        "box_13",
        "mask_12",
        "mask_13",
    }
    if set(arrays) != required:
        raise ValueError("array_set")
    sources = {
        "hug_sim.py.txt",
        "score_calculator.py.txt",
        "sim_utils.py.txt",
        "gaussian_model.py.txt",
        "ground_model.py.txt",
    }
    if set(record["sources"]) != sources:
        raise ValueError("source_set")
    for name, row in record["sources"].items():
        identity = file(raw, name, 1024**2)
        if (
            identity != {k: row[k] for k in ("bytes", "sha256")}
            or identity != assets[row["original"]]
        ):
            raise ValueError("source_snapshot")
    allowed = seen | sources | {"witness.json"}
    if {p.name for p in raw.iterdir()} != allowed:
        raise ValueError("extra_or_missing_raw")
    xyz, features, opacity = [
        arrays[n] for n in ("population_xyz", "population_features", "population_opacity")
    ]
    n = len(xyz)
    if not 0 < n <= plan["max_population"] or n != record["population_points"]:
        raise ValueError("population_count")
    selected = selection(xyz, features, opacity)
    selection_raw = arrays["selection"]
    if (
        selection_raw.dtype != np.dtype("u1")
        or selection_raw.shape != (n,)
        or not np.array_equal(selected.astype("u1"), selection_raw)
    ):
        raise ValueError("selection_mask")
    points = arrays["selected_xyz"]
    if (
        points.dtype != np.dtype("<f4")
        or not np.array_equal(points, xyz[selected])
        or len(points) != plan["expected_selected_points"]
        or len(points) != record["selected_points"]
    ):
        raise ValueError("selected_population")
    ground = arrays["ground_poses"]
    if ground.dtype != np.dtype("<f8") or ground.shape != (1252, 4, 4):
        raise ValueError("ground_population")
    if [r["frame"] for r in record["frames"]] != plan["unique_frames"]:
        raise ValueError("frame_set")
    results = []
    status = "supported"
    for entry in record["frames"]:
        frame = entry["frame"]
        old = next(f for f in plan["frames"] if f["frame"] == frame)
        if entry["time"] != old["time"] or entry["rotation"] != [0, old["state"][2], 0]:
            raise ValueError("frame_pose_binding")
        height, nearest = ground_height(ground, old["state"][1], old["state"][0])
        position = [old["state"][1], height, old["state"][0]]
        if (
            max(abs(a - b) for a, b in zip(position, old["ego_pos"])) > plan["ground_tolerance"]
            or max(abs(a - b) for a, b in zip(position, entry["position"]))
            > plan["ground_tolerance"]
        ):
            raise ValueError("ground_or_logged_height")
        expected = vertices(position, old["state"][2], plan["box_dimensions_xyz"])
        box = arrays[f"box_{frame}"]
        if (
            box.shape != (8, 3)
            or box.dtype != np.dtype("<f4")
            or float(np.max(np.abs(box - np.array(expected)))) > plan["vertex_tolerance"]
        ):
            raise ValueError("box_geometry")
        native = arrays[f"mask_{frame}"]
        if (
            native.dtype != np.dtype("u1")
            or native.shape != (len(points),)
            or not np.isin(native, [0, 1]).all()
        ):
            raise ValueError("native_mask_shape")
        count = int(native.sum())
        if (
            type(entry["count"]) is not int
            or count != entry["count"]
            or type(entry["collision"]) is not bool
            or entry["collision"] != (count > 100)
            or entry["points"] != len(points)
        ):
            raise ValueError("native_count_consistency")
        independent = count_points(points.tolist(), box.tolist())
        disagreements = np.flatnonzero(native != np.array(independent["mask"], dtype="u1")).tolist()
        material = sorted(set(disagreements) - set(independent["ambiguous"]))
        if material or entry["collision"] != old["background"]:
            status = "contradicted"
        elif disagreements and status == "supported":
            status = "inconclusive"
        output = {k: v for k, v in independent.items() if k not in ("mask", "ambiguous")}
        output.update(
            frame=frame,
            time=old["time"],
            source_count=count,
            source_collision=entry["collision"],
            historical_collision=old["background"],
            ambiguous_points=len(independent["ambiguous"]),
            mask_disagreements=disagreements,
            material_disagreements=material,
            ground_nearest_index=nearest,
            ground_height=height,
        )
        results.append(output)
    return {
        "status": status,
        "raw_commit": raw_commit,
        "historical_replica_frames": 4,
        "unique_frame_witnesses": 2,
        "new_driving_episodes": 0,
        "population_points": n,
        "selected_points": len(points),
        "frames": results,
        "physical_occupancy": None,
        "road_compliance": None,
        "live_recovery": None,
        "information_benefit": None,
        "numeric_environment": record["numeric_environment"],
        "scope": "Full retained point selection and finite source predicate replay; not physical scene reconstruction validation or a driving outcome.",
    }
