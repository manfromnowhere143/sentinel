"""Rank eligible prefixes by scheduled checkpoint crossings, then target distance."""

import math

from experiments.iter167_planner_terminal_contract.adapter import distance
from .common import require


def checkpoint_frames(geometry, old):
    frames = [c["hazard_time"] / old["dt"] for c in geometry["comparators"].values()]
    require(
        all(math.isfinite(f) and float(f).is_integer() and f >= 0 for f in frames),
        "checkpoint_grid",
    )
    return sorted(set(int(f) for f in frames))


def crossed(frame, origin, checkpoints):
    return sum(origin < f <= frame for f in checkpoints)


def prefix_index(rows, valid, interrupted, world, target, origin, checkpoints):
    if interrupted is not None:
        return 0
    if world:
        return valid
    return min(
        range(1, valid + 1),
        key=lambda k: (
            -crossed(rows[k]["frame"], origin, checkpoints),
            distance([*rows[k]["state"], rows[k]["frame"]], target),
            k,
        ),
        default=0,
    )


def evaluation_rank(row, target, origin, checkpoints):
    k = row["selected_prefix"]
    endpoint = row["trace"][k]
    return (
        not row["world_complete"],
        -crossed(endpoint["frame"], origin, checkpoints),
        distance([*endpoint["state"], endpoint["frame"]], target),
        row["id"],
        k,
    )
