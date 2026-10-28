"""Frozen source and array loading; no control policy."""

import json
from pathlib import Path
from experiments.iter158_constraint_aware_search.common import (
    encode,
    git,
    read,
    require,
    rss,
    sha,
    write,
)
from experiments.iter155_background_witness.storage import get_arrays

BASE = Path("experiments/iter193_history_delay")
HISTORY = Path("experiments/iter164_monitor_time_continuation")
PREVIOUS = Path("experiments/iter192_integrated_feedback")
PLANNER = Path("experiments/iter189_uniform_timing_eligibility/PLAN.json")
OLD = Path("experiments/iter153_action_feasibility/PLAN.json")


def source_check(root, plan, source):
    require(len(source) == 40 and all(c in "0123456789abcdef" for c in source), "source_encoding")
    for name in [str(BASE / "PLAN.json"), *plan["source_files"]]:
        require(
            read(root, name) == git(root, "show", source + ":" + name), "source_changed:" + name
        )


def load_source(root):
    history = json.loads(read(root, HISTORY / "PLAN.json"))
    for name, expected in history["inputs"].items():
        require(sha(read(root, name)) == expected, "history_input:" + name)
    folder = root / "experiments/iter155_background_witness/proof/raw"
    witness = json.loads(read(folder, "witness.json"))
    arrays, _ = get_arrays(
        folder, {k: witness["arrays"][k] for k in ("selected_xyz", "ground_poses")}
    )
    geometry = json.loads(
        read(root, "experiments/iter153_action_feasibility/proof/search_000/geometry.json")
    )
    old = json.loads(read(root, OLD))
    from experiments.iter164_monitor_time_continuation.history import extract

    replicas = extract(root, history)
    prefix = json.loads(read(root, HISTORY / "proof/prefix_raw/replica_0/trace.json"))
    for replica in replicas:
        require(
            [r["state"] for r in prefix] == replica["states"]
            and [r["action"] for r in prefix] == replica["actions"],
            "history_binding",
        )
    require(len(prefix) == 26, "historical_population")
    return (
        dict(
            id=history["scene"],
            geometry=geometry,
            points=arrays["selected_xyz"].tolist(),
            ground=arrays["ground_poses"].tolist(),
        ),
        old,
        prefix,
    )


__all__ = [
    "BASE",
    "HISTORY",
    "PREVIOUS",
    "PLANNER",
    "OLD",
    "encode",
    "git",
    "read",
    "require",
    "rss",
    "sha",
    "write",
    "source_check",
    "load_source",
]
