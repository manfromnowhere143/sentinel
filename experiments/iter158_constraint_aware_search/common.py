"""Bounded I/O and source bindings only; shared with independent admission."""

import hashlib
import json
from pathlib import Path
import platform
import resource
import subprocess

from experiments.iter150_cloud_observation.native import file
from experiments.iter155_background_witness.storage import get_arrays, read_json

BASE = Path("experiments/iter158_constraint_aware_search")
OLD = Path("experiments/iter153_action_feasibility")
RAW155 = Path("experiments/iter155_background_witness/proof/raw")


def require(value, reason):
    if not value:
        raise ValueError(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encode(value):
    return (
        json.dumps(value, sort_keys=True, allow_nan=False, separators=(",", ":")) + "\n"
    ).encode()


def write(path, value):
    with Path(path).open("xb") as stream:
        stream.write(encode(value))


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root)


def read(root, name, limit=128 * 1024**2):
    return file(root, str(name), limit, content=True)[1]


def rss():
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * (
        1 if platform.system() == "Darwin" else 1024
    )


def inputs(root, plan):
    for name, identity in plan["inputs"].items():
        require(sha(read(root, name)) == identity, "input_identity:" + name)
    geometry = read_json(root / OLD / "proof/search_000/geometry.json")
    old = read_json(root / OLD / "PLAN.json")
    arrays, _ = get_arrays(root / RAW155, read_json(root / RAW155 / "witness.json")["arrays"])
    return geometry, old, arrays


def source_check(root, plan, source):
    require(len(source) == 40 and all(c in "0123456789abcdef" for c in source), "source_encoding")
    for name in [str(BASE / "PLAN.json"), *plan["source_files"]]:
        require(
            git(root, "show", source + ":" + name) == read(root, name), "source_changed:" + name
        )


def raw_check(root, raw, commit, plan):
    relative = raw.relative_to(root).as_posix()
    names = git(root, "ls-tree", "-r", "--name-only", commit, "--", relative).decode().splitlines()
    require(set(names) == {p.relative_to(root).as_posix() for p in raw.iterdir()}, "raw_inventory")
    total = 0
    for name in names:
        data = read(root, name)
        total += len(data)
        require(git(root, "show", commit + ":" + name) == data, "raw_not_committed")
    require(total <= plan["max_output_bytes"], "output_budget")
    return names
