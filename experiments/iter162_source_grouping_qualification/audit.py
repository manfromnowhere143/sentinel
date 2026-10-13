"""Witness-free replay of recorded selection stages; no producer import.

Derived from the admitted Iter161 audit; no fabricated source witness is needed.
Unselected collision and guide labels remain producer evidence.
"""

from collections import Counter
import json

from experiments.iter161_grouping_width_ablation.check import audit_beam
from .common import read, require


def audit_run(folder, result, plan):
    attempts = [json.loads(line) for line in read(folder, "attempts.jsonl").splitlines()]
    depths = [json.loads(line) for line in read(folder, "depths.jsonl").splitlines()]
    require(len(attempts) == result["attempts"] + 1, "attempt_count")
    require(0 <= result["attempts"] <= plan["attempt_budget"], "attempt_budget")
    require(sum(r["background"] is not None for r in attempts) == result["queries"], "query_count")
    require(Counter(r["reason"] for r in attempts[1:]) == result["counts"], "counts")
    require(attempts[0]["reason"] == "clear", "initial_rejected")
    beam, by_frame = [0], {}
    for i, row in enumerate(attempts):
        require(type(row["id"]) is int and row["id"] == i, "attempt_order")
        if i:
            require(type(row["parent"]) is int and 0 <= row["parent"] < i, "parent_order")
            require(row["frame"] == attempts[row["parent"]]["frame"] + 1, "parent_depth")
        by_frame.setdefault(row["frame"], []).append(row)
    require([d["frame"] for d in depths] == list(range(1, len(depths) + 1)), "depth_sequence")
    require(set(by_frame) == {0, *(d["frame"] for d in depths)}, "attempt_depth_scope")
    require(all(type(d["complete"]) is bool for d in depths), "complete_type")
    require(all(d["complete"] is True for d in depths[:-1]), "partial_depth")
    require(len(depths) <= plan["max_actions"], "depth_budget")
    for depth in depths:
        rows = by_frame.get(depth["frame"], [])
        require(all(r["parent"] in beam for r in rows), "expanded_pruned_parent")
        survivors = [r for r in rows if r["reason"] == "clear"]
        require(len(survivors) == depth["survivors"], "survivor_count")
        expected = audit_beam(survivors, result["width"], result["aggregation"])
        if depth["complete"]:
            require(depth["beam"] == expected["beam"], "beam_replay")
            require(
                depth["cell_representatives"] == expected["cell_representatives"], "grouping_replay"
            )
            require(
                all(
                    type(depth[k]) is int and depth[k] == expected[k]
                    for k in ("grouping_removed", "width_removed")
                ),
                "retention_partition",
            )
            beam = expected["beam"]
        else:
            require(set(depth) == {"frame", "complete", "survivors", "beam"}, "partial_fields")
            require(depth["beam"] == [], "partial_beam")
    require(sum(d["complete"] for d in depths) == result["completed_depth"], "completed_depth")
    trace = json.loads(read(folder / "selected", "trace.json"))
    require(all(row == attempts[row["id"]] for row in trace), "trace_binding")
    stop = result["stop"]
    require(
        stop in {"model_complete", "beam_empty", "horizon", "attempt_budget", "time_budget"}, "stop"
    )
    if stop == "model_complete":
        require(
            result["selected"] == trace[-1]["id"] and trace[-1]["route"]["rc"] >= 1,
            "selected_identity",
        )
        require(trace[-1]["frame"] == result["completed_depth"], "selected_depth")
    else:
        require(result["selected"] is None and trace[-1]["route"]["rc"] < 1, "false_completion")
    if stop in {"attempt_budget", "time_budget"}:
        require(depths and depths[-1]["complete"] is False, "budget_partial_depth")
    if stop == "time_budget":
        require(result["elapsed_seconds"] >= plan["per_run_seconds"], "false_time_budget")
    if stop == "beam_empty":
        require(depths[-1]["complete"] and not depths[-1]["beam"], "false_beam_empty")
    if stop == "attempt_budget":
        require(result["attempts"] == plan["attempt_budget"], "false_budget")
    if stop == "horizon":
        require(result["completed_depth"] == plan["max_actions"], "false_horizon")
    return (
        trace,
        dict(
            grouping_removed=sum(d.get("grouping_removed", 0) for d in depths),
            width_removed=sum(d.get("width_removed", 0) for d in depths),
            retained=sum(len(d["beam"]) for d in depths),
            partial_depth_survivors=sum(d["survivors"] for d in depths if not d["complete"]),
        ),
    )
