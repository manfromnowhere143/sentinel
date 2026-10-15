"""Independent selection arithmetic; no producer selector or dynamics imports."""

import math

from experiments.iter172_integrated_rrt.check import distance
from .common import require


def count_checkpoints(frame, origin, case, old):
    times = {c["hazard_time"] for c in case["geometry"]["comparators"].values()}
    require(
        all(math.isfinite(t) and t >= 0 and float(t / old["dt"]).is_integer() for t in times),
        "checkpoint_grid",
    )
    lower, upper = origin * old["dt"], frame * old["dt"]
    return len([t for t in times if lower < t and t <= upper])


def selection_index(row, connection, case, old):
    if row["interrupted"] is not None:
        return 0
    if row["world_complete"]:
        return row["valid_prefix"]
    best, best_key = 0, None
    for k in range(1, row["eligibility"]["eligible_prefix"] + 1):
        node = row["trace"][k]
        key = (
            -count_checkpoints(node["frame"], connection["before"][5], case, old),
            distance([*node["state"], node["frame"]], connection["target"]),
            k,
        )
        if best_key is None or key < best_key:
            best, best_key = k, key
    return best


def selection_rank(row, connection, case, old):
    k = row["selected_prefix"]
    node = row["trace"][k]
    return (
        not row["world_complete"],
        -count_checkpoints(node["frame"], connection["before"][5], case, old),
        distance([*node["state"], node["frame"]], connection["target"]),
        row["id"],
        k,
    )


def change_summary(connection, events, case, old):
    """Parent-181 choice on the same generated records; no counterfactual tree."""
    from experiments.iter181_checkpoint_prefix_selection.selection_check import (
        selection_index as parent_index,
    )

    if connection["result"] is None:
        return None
    candidates = []
    for row in events:
        if row["kind"] != "evaluation" or row["interrupted"] is not None:
            continue
        k = parent_index(row, connection, case, old)
        if k:
            clone = dict(row, selected_prefix=k)
            candidates.append(
                (
                    selection_rank(clone, connection, case, old),
                    row["id"],
                    k,
                    row["trace"][k]["frame"],
                )
            )
    if not candidates:
        return None
    chosen = min(candidates)
    result = connection["result"]
    if (chosen[1], chosen[2]) == (result["selected_evaluation"], result["selected_prefix"]):
        return None
    return dict(
        call=connection["call"],
        parent_rule_evaluation=chosen[1],
        parent_rule_prefix=chosen[2],
        parent_rule_frame=chosen[3],
        candidate_evaluation=result["selected_evaluation"],
        candidate_prefix=result["selected_prefix"],
        candidate_frame=connection["trace"][-1]["frame"],
        scope="Same candidate-generated noninterrupted records, without the eligibility filter; no counterfactual tree or parent timing claim.",
    )
