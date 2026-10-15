"""Fixed stepwise-control continuation probes; never an integrated RRT repair."""

from collections import Counter
import time

from experiments.iter153_action_feasibility.geometry import obstacles, route_outcome
from experiments.iter153_action_feasibility.planner import reference, transition
from experiments.iter158_constraint_aware_search.search import prior_reason, proposals, score
from experiments.iter159_route_search_qualification.guidance import RouteGuidance
from experiments.iter161_grouping_width_ablation.search import choose
from .common import require, rss


def probe(state, start_frame, geometry, old, plan, query, deadline):
    """The API receives no case ID, witness controls or previous search outcomes."""
    require(type(start_frame) is int and 0 < plan["target_frame"] - start_frame <= 8, "probe_clock")
    guide = RouteGuidance(geometry)
    path, arc = reference(geometry["route"], dict(offset=0, start=0, length=10), old)
    boxes = obstacles(geometry)
    root = dict(
        id=0,
        parent=None,
        frame=start_frame,
        action=None,
        state=state,
        route=route_outcome(state, geometry["route"]),
        effort=0.0,
        guide_distance=float(guide.distance(state)),
        background=query(state),
        reason="clear",
    )
    reason, _ = prior_reason(state, state, [0.0, 0.0], start_frame, geometry, old, boxes)
    require(reason is None and root["background"]["decision"] == "clear", "probe_root")
    attempts, depths, beam = [root], [], [root]
    queries, stop, selected, best = 1, None, None, root
    last_checkpoint = max(c["hazard_time"] / 0.25 for c in geometry["comparators"].values())
    for frame in range(start_frame + 1, plan["target_frame"] + 1):
        survivors = []
        for parent in beam:
            for action in proposals(parent["state"], path, arc, old):
                if len(attempts) - 1 >= plan["per_root_attempts"]:
                    stop = "attempt_budget"
                    break
                if time.monotonic() >= deadline:
                    stop = "time_budget"
                    break
                require(rss() <= plan["max_rss_bytes"], "probe_memory")
                after = transition(parent["state"], action, old)
                reason, outcome = prior_reason(
                    parent["state"], after, action, frame, geometry, old, boxes
                )
                if reason is None and outcome["rc"] >= 1 and frame < last_checkpoint:
                    reason = "premature_completion"
                background = None
                if reason is None:
                    background = query(after)
                    queries += 1
                    reason = background["decision"]
                row = dict(
                    id=len(attempts),
                    parent=parent["id"],
                    frame=frame,
                    action=action,
                    state=after,
                    route=outcome,
                    effort=parent["effort"] + sum(a * a for a in action),
                    guide_distance=float(guide.distance(after)),
                    background=background,
                    reason=reason,
                )
                attempts.append(row)
                if reason == "clear":
                    survivors.append(row)
                    if (-frame, score(row)) < (-best["frame"], score(best)):
                        best = row
                    if frame == plan["target_frame"]:
                        selected, stop = row, "checkpoint_witness"
                        break
            if stop:
                break
        if stop:
            depths.append(dict(frame=frame, complete=False, survivors=len(survivors), beam=[]))
            break
        beam, retention = choose(survivors, plan["beam_width"], "exact")
        depths.append(
            dict(
                frame=frame,
                complete=True,
                survivors=len(survivors),
                beam=[r["id"] for r in beam],
                **retention,
            )
        )
        if not beam:
            stop = "beam_empty"
            break
    require(stop is not None, "probe_missing_stop")
    trace, cursor = [], selected or best
    while cursor is not None:
        trace.append(cursor)
        cursor = attempts[cursor["parent"]] if cursor["parent"] is not None else None
    return dict(
        start_frame=start_frame,
        target_frame=plan["target_frame"],
        attempts=len(attempts) - 1,
        queries=queries,
        stop=stop,
        witness=selected is not None,
        selected=None if selected is None else selected["id"],
        counts=dict(Counter(r["reason"] for r in attempts[1:])),
        depths=depths,
        trace=list(reversed(trace)),
        attempt_records=attempts,
    )
