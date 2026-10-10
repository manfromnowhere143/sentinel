"""Bounded inventory for the installed UnifiedMap loader; no cache construction."""

import json
import os
from pathlib import Path
import socket
import stat
import time
from .resources import file_identity
from experiments.iter144_timed_trajectory.trajectory import ContractError

ROOTS = (
    "/root/.unified_data_cache",
    "/datasets/nuscenes-full/v1.0-trainval",
    "/datasets/nuscenes-full/maps",
)
TABLES = (
    "attribute",
    "calibrated_sensor",
    "category",
    "ego_pose",
    "instance",
    "log",
    "map",
    "sample",
    "sample_annotation",
    "sample_data",
    "scene",
    "sensor",
    "visibility",
)
LOCATIONS = (
    "boston-seaport",
    "singapore-hollandvillage",
    "singapore-onenorth",
    "singapore-queenstown",
)


def required_paths():
    paths = {ROOTS[1] + "/" + name + ".json" for name in TABLES}
    cache = ROOTS[0] + "/nusc_trainval"
    paths.add(cache + "/scenes_list.dill")
    for scene in ("scene-0013", "scene-0038"):
        for dt in ("0.10", "0.50"):
            for name in (
                "scene_metadata_dt" + dt + ".dill",
                "agent_data_dt" + dt + ".feather",
                "scene_index_dt" + dt + ".pkl",
            ):
                paths.add(cache + "/" + scene + "/" + name)
    for location in LOCATIONS:
        for suffix in (".pb", "_kdtrees.dill", "_rtrees.dill", "_2.00px_m.dill"):
            paths.add(cache + "/maps/" + location + suffix)
        paths.add(ROOTS[2] + "/expansion/" + location + ".json")
    return paths


def validate(binding):
    if not isinstance(binding, dict) or (
        binding.get("schema") != "sentinel.iter145.map_inventory.v1"
        or binding.get("observation_kind") != "host_readback"
        or binding.get("roots") != list(ROOTS)
        or binding.get("scope") != "complete_regular_file_trees"
        or binding.get("status") != "supported"
    ):
        raise ContractError("map_binding_header")
    files = binding.get("files")
    if not isinstance(files, dict) or not required_paths() <= set(files):
        raise ContractError("map_binding_dependencies")
    for name, row in files.items():
        if not any(name.startswith(root + "/") for root in ROOTS) or ".." in Path(name).parts:
            raise ContractError("map_binding_path")
        h = row.get("sha256")
        if (
            type(row.get("bytes")) is not int
            or row["bytes"] <= 0
            or not isinstance(h, str)
            or len(h) != 64
            or any(c not in "0123456789abcdef" for c in h)
        ):
            raise ContractError("map_binding_identity")
    if binding.get("file_count") != len(files) or binding.get("total_bytes") != sum(
        r["bytes"] for r in files.values()
    ):
        raise ContractError("map_binding_totals")
    return True


def inventory_tree(root):
    found = []
    for base, dirs, files in os.walk(root, followlinks=False):
        for name in dirs:
            if (Path(base) / name).is_symlink():
                raise ContractError("map_directory_symlink")
        for name in sorted(files):
            p = Path(base) / name
            if not stat.S_ISREG(p.lstat().st_mode):
                raise ContractError("map_nonregular_file")
            found.append(str(p))
            if len(found) > 100000:
                raise ContractError("map_inventory_file_cap")
    return sorted(found)


def collect():
    if socket.gethostname().split(".")[0] != "sentinel-gpu":
        raise ContractError("map_host")
    start = time.monotonic()
    paths = {root: inventory_tree(root) for root in ROOTS}
    records = {}
    for names in paths.values():
        for name in names:
            if time.monotonic() - start > 600:
                raise ContractError("map_inventory_deadline")
            records[name] = file_identity(Path(name))
    if any(inventory_tree(root) != names for root, names in paths.items()):
        raise ContractError("map_inventory_changed")
    result = dict(
        schema="sentinel.iter145.map_inventory.v1",
        observation_kind="host_readback",
        roots=list(ROOTS),
        scope="complete_regular_file_trees",
        status="supported",
        observed_epoch=time.time(),
        files=records,
        file_count=len(records),
        total_bytes=sum(r["bytes"] for r in records.values()),
        elapsed_seconds=time.monotonic() - start,
        limitation="File identity closure only; loader execution and route validity require qualification.",
    )
    validate(result)
    return result


def main():
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    with a.output.open("x") as out:
        try:
            result = collect()
        except Exception as e:
            json.dump(dict(status="failed", reason=f"{type(e).__name__}:{e}"), out, indent=2)
            raise
        json.dump(result, out, indent=2)
        out.write("\n")


if __name__ == "__main__":
    main()
