"""Bounded record I/O and identities; no scientific decision logic."""

import hashlib
from pathlib import Path
import platform
import resource
import subprocess

from experiments.iter150_cloud_observation.native import file
from experiments.iter155_background_witness.storage import read_json

BASE = Path("experiments/iter157_constrained_action_library")
OLD = Path("experiments/iter153_action_feasibility")


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root)


def bounded(root, path, cap=64 * 1024**2):
    return file(root, str(path), cap, content=True)[1]


def inputs(root, plan):
    for path, expected in plan["inputs"].items():
        require(sha(bounded(root, path)) == expected, "input_identity:" + path)


def rss():
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * (
        1 if platform.system() == "Darwin" else 1024
    )


def committed_raw(root, raw, commit, plan, data):
    relative = raw.relative_to(root)
    names = (
        git(root, "ls-tree", "-r", "--name-only", commit, "--", str(relative)).decode().splitlines()
    )
    require(set(names) == {str(p.relative_to(root)) for p in raw.iterdir()}, "raw_commit_inventory")
    for name in names:
        require(git(root, "show", f"{commit}:{name}") == bounded(root, name), "raw_not_committed")
    require(
        sum((root / n).stat().st_size for n in names) <= plan["max_output_bytes"], "output_budget"
    )
    source = data["source_commit"]
    require(len(source) == 40 and all(c in "0123456789abcdef" for c in source), "source_encoding")
    require(
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", source, commit], cwd=root, capture_output=True
        ).returncode
        == 0,
        "source_ancestry",
    )
    for path in [str(BASE / "PLAN.json"), *plan["source_files"]]:
        require(git(root, "show", f"{source}:{path}") == bounded(root, path), "source_not_frozen")
    require(data["plan_sha256"] == sha(bounded(root, BASE / "PLAN.json")), "plan_identity")
    return names


def documents(root):
    return (
        read_json(root / BASE / "PLAN.json"),
        read_json(root / OLD / "PLAN.json"),
        read_json(root / OLD / "proof/analysis.json"),
    )


def query_budget(count, maximum):
    require(type(count) is int and 0 < count <= maximum, "query_budget")
