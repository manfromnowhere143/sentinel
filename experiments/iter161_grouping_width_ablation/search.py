"""Fixed proposals, route guide and constraints; grouping crossed with width."""

from collections import Counter
import math
import struct
import time

from experiments.iter153_action_feasibility.geometry import obstacles, route_outcome
from experiments.iter153_action_feasibility.planner import reference, transition
from experiments.iter158_constraint_aware_search.search import cell, prior_reason, proposals, score
from experiments.iter158_constraint_aware_search.common import require, rss
from experiments.iter159_route_search_qualification.guidance import RouteGuidance


def grouping_key(row, aggregation):
    require(aggregation in {"quantized", "exact"}, "aggregation")
    require(type(row["frame"]) is int and 0 <= row["frame"] <= 401, "key_frame")
    state = row["state"]
    require(
        len(state) == 5 and all(type(v) in (int, float) and math.isfinite(v) for v in state),
        "key_state",
    )
    if aggregation == "quantized":
        return (row["frame"], *cell(state))
    return struct.pack(">q5d", row["frame"], *state)


def choose(rows, width, aggregation):
    require(type(width) is int and width > 0, "width")
    representatives, seen, groups = [], set(), {}
    for row in sorted(rows, key=score):
        key = grouping_key(row, aggregation)
        if key not in seen:
            seen.add(key)
            representatives.append(row)
            groups.setdefault(round(row["state"][3]), []).append(row)
    selected, layer = [], 0
    while len(selected) < width:
        options = sorted([g[layer] for g in groups.values() if len(g) > layer], key=score)
        if not options:
            break
        selected.extend(options[: width - len(selected)])
        layer += 1
    return selected, dict(
        cell_representatives=[r["id"] for r in representatives],
        grouping_removed=len(rows) - len(representatives),
        width_removed=len(representatives) - len(selected),
    )


def search(geometry, old, plan, query, emit, aggregation):
    """No witness, fixture ID, or reference controls are accepted by this API."""
    require(aggregation in {"quantized", "exact"}, "aggregation")
    guide = RouteGuidance(geometry)
    path, arc = reference(geometry["route"], dict(offset=0, start=0, length=10), old)
    boxes = obstacles(geometry)
    state = geometry["reset"]
    reset = dict(
        id=0,
        parent=None,
        frame=0,
        action=None,
        state=state,
        route=route_outcome(state, geometry["route"]),
        effort=0.0,
        background=query(state),
        guide_distance=guide.distance(state),
    )
    reason, _ = prior_reason(state, state, [0, 0], 0, geometry, old, boxes)
    reset["reason"] = reason or reset["background"]["decision"]
    emit("attempt", reset)
    started = time.monotonic()
    nodes, beam, best = {0: reset}, [reset], reset
    counts, attempted, queries, depth = Counter(), 0, 1, 0
    selected, stop = None, "horizon"
    if reset["reason"] != "clear":
        beam, stop = [], "initial_rejected"
    for frame in range(1, plan["max_actions"] + 1) if beam else ():
        survivors, interrupted = [], None
        for parent in beam:
            for action in proposals(parent["state"], path, arc, old):
                if attempted >= plan["attempt_budget"]:
                    interrupted = "attempt_budget"
                    break
                if time.monotonic() - started >= plan["per_run_seconds"]:
                    interrupted = "time_budget"
                    break
                require(rss() <= plan["max_rss_bytes"], "memory_budget")
                attempted += 1
                after = transition(parent["state"], action, old)
                reason, outcome = prior_reason(
                    parent["state"], after, action, frame, geometry, old, boxes
                )
                background = None
                if reason is None:
                    background = query(after)
                    queries += 1
                    reason = background["decision"]
                row = dict(
                    id=attempted,
                    parent=parent["id"],
                    frame=frame,
                    action=action,
                    state=after,
                    route=outcome,
                    effort=parent["effort"] + sum(a * a for a in action),
                    background=background,
                    reason=reason,
                    guide_distance=guide.distance(after),
                )
                emit("attempt", row)
                counts[reason] += 1
                if reason == "clear":
                    nodes[row["id"]] = row
                    survivors.append(row)
            if interrupted:
                break
        if interrupted:
            stop = interrupted
            emit("depth", dict(frame=frame, complete=False, survivors=len(survivors), beam=[]))
            break
        depth = frame
        beam, retention = choose(survivors, plan["beam_width"], aggregation)
        emit(
            "depth",
            dict(
                frame=frame,
                complete=True,
                survivors=len(survivors),
                beam=[n["id"] for n in beam],
                **retention,
            ),
        )
        for row in survivors:
            if (-row["route"]["nearest"], row["frame"], score(row)) < (
                -best["route"]["nearest"],
                best["frame"],
                score(best),
            ):
                best = row
        complete = [n for n in survivors if n["route"]["rc"] >= 1]
        if complete:
            selected, stop = min(complete, key=score), "model_complete"
            break
        if not beam:
            stop = "beam_empty"
            break
    trace, node = [], selected or best
    while node is not None:
        trace.append(node)
        node = nodes[node["parent"]] if node["parent"] is not None else None
    return dict(
        stop=stop,
        attempts=attempted,
        queries=queries,
        counts=dict(counts),
        completed_depth=depth,
        selected=None if selected is None else selected["id"],
        trace=list(reversed(trace)),
        elapsed_seconds=time.monotonic() - started,
    )
