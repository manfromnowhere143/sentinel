"""Independent scalar motion, path joins, proposals and diagnostic accounting.

No producer search, path extractor, bound, guidance or vector geometry imports.
All queried probe states must be in the independently verified mask inventory.
"""

import bisect
from collections import Counter
import copy
import math

from experiments.iter153_action_feasibility.check import near, path_reference, policy
from experiments.iter168_control_connector.check import physical
from experiments.iter172_integrated_rrt.check import outcome
from experiments.iter161_grouping_width_ablation.check import audit_beam, ordering
from .common import encode, require
from .retained import state_key


def row_check(row, previous, case, old, masks):
    state = row["state"]
    expected = outcome(state, case["geometry"])
    require(row["route"]["nearest"] == expected["nearest"], "route_index")
    near([row["route"]["distance"], row["route"]["rc"]], [expected["distance"], expected["rc"]])
    reason = physical(
        previous["state"],
        state,
        row["action"],
        row["frame"],
        dict(case, task=dict(wait_until=0, stop_from=None)),
        old,
    )
    last_checkpoint = max(c["hazard_time"] * 4 for c in case["geometry"]["comparators"].values())
    if reason is None and expected["rc"] >= 1 and row["frame"] < last_checkpoint:
        reason = "premature_completion"
    background = row["background"]
    if reason is None:
        require(isinstance(background, dict), "missing_background")
        require(
            set(background)
            == {"count", "certain_inside", "possible_inside", "decision", "mask_sha256"},
            "background_schema",
        )
        lo, count, hi = [background[k] for k in ("certain_inside", "count", "possible_inside")]
        require(
            all(type(v) is int for v in (lo, count, hi))
            and 0 <= lo <= count <= hi <= len(case["points"]),
            "background_counts",
        )
        reason = "clear" if hi <= 100 else ("collision" if lo > 100 else "numerically_ambiguous")
        require(background["decision"] == reason, "background_label")
        key = state_key(state)
        if key in masks:
            require(background == masks[key]["background"], "scalar_background_binding")
    else:
        require(background is None, "rejected_background")
    require(row["reason"] == reason, "rejection_reason")
    return reason


def path_check(trace, keys, case, old, masks):
    require(0 < len(trace) <= 33 and len(trace) == len(keys), "path_length")
    require(
        trace[0]["state"] == case["geometry"]["reset"] and trace[0]["action"] is None, "path_root"
    )
    for frame, row in enumerate(trace):
        require(
            row["frame"] == row["id"] == frame
            and type(row["frame"]) is int
            and row["parent"] == (frame - 1 if frame else None),
            "path_clock",
        )
        previous = trace[frame - 1] if frame else row
        require(row_check(row, previous, case, old, masks) == "clear", "path_rejected")
        key = state_key(row["state"])
        require(keys[frame] == key and key in masks, "path_mask")
        require(row["background"] == masks[key]["background"], "path_scalar_binding")
    return len(trace)


def path_binding(record, connections, reset):
    table = {r["call"]: r for r in connections}
    require(record["chain"] and record["chain"][-1] == record["call"], "chain_final")
    endpoint = table[record["call"]]["before"]
    cutoff, ambiguous = record["call"], 0
    for number in reversed(record["chain"][:-1]):
        candidates = [
            n
            for n, edge in table.items()
            if n < cutoff
            and edge["result"] is not None
            and len(edge["trace"]) > 1
            and [*edge["trace"][-1]["state"], edge["trace"][-1]["frame"]] == endpoint
        ]
        require(candidates and number == min(candidates), "chain_selection")
        ambiguous += len(candidates) > 1
        require(table[number]["before"][5] < endpoint[5], "chain_clock")
        endpoint, cutoff = table[number]["before"], number
    require(endpoint == [*reset, 0] and ambiguous == record["ambiguous_joins"], "chain_root")
    joined = []
    for number in record["chain"]:
        edge = table[number]
        if not joined:
            joined.append(edge["trace"][0])
        require([*joined[-1]["state"], joined[-1]["frame"]] == edge["before"], "chain_join")
        joined.extend(edge["trace"][1:])
    require(encode(joined) == encode(record["trace"]), "path_source")


def scalar_proposals(state, geometry, old):
    points, arc = path_reference(geometry["route"], dict(offset=0.0, start=0.0, length=10.0), old)
    values = [[float(a), r * math.pi / 12] for a in (-2, 0, 2) for r in (-1, -0.5, 0, 0.5, 1)]
    values += [policy(state, points, arc, dict(speed=v), old) for v in (2.0, 4.0, 6.0)]
    return [list(v) for v in dict.fromkeys(tuple(v) for v in values)]


def scalar_guide(state, geometry):
    points = [(p[1], p[0]) for p in geometry["route"]]
    arc = [0.0]
    for a, b in zip(points, points[1:]):
        arc.append(arc[-1] + math.dist(a, b))
    nearest = min(range(len(points)), key=lambda i: (math.dist(state[:2], points[i]), i))
    goal = math.ceil(0.9 * len(points)) - 1
    station = min(arc[goal], arc[nearest] + 5.0)
    j = min(len(points) - 1, max(1, bisect.bisect_right(arc, station)))
    t = (station - arc[j - 1]) / (arc[j] - arc[j - 1])
    target = [points[j - 1][k] + t * (points[j][k] - points[j - 1][k]) for k in (0, 1)]
    angle = math.atan2(target[1] - state[1], target[0] - state[0]) - state[2]
    return (
        max(0.0, arc[goal] - arc[nearest])
        + 4 * math.dist(state[:2], points[nearest])
        + 2.7 * abs(math.atan2(math.sin(angle), math.cos(angle)))
    )


def probe_check(record, attempts, combined, retained_path, case, old, plan, masks):
    result = record["result"]
    require(
        len(attempts) == result["attempts"] + 1
        and 0 <= result["attempts"] <= plan["per_root_attempts"],
        "probe_accounting",
    )
    start = retained_path[-1]
    require(
        attempts[0]["state"] == start["state"]
        and attempts[0]["frame"] == start["frame"]
        and attempts[0]["action"] is None
        and attempts[0]["parent"] is None,
        "probe_root_identity",
    )
    require(
        result["start_frame"] == start["frame"] and result["target_frame"] == plan["target_frame"],
        "probe_clock",
    )
    for i, row in enumerate(attempts):
        require(type(row["id"]) is int and row["id"] == i, "probe_attempt_order")
        if i:
            require(
                type(row["parent"]) is int
                and 0 <= row["parent"] < i
                and row["frame"] == attempts[row["parent"]]["frame"] + 1,
                "probe_parent",
            )
        parent = row if i == 0 else attempts[row["parent"]]
        if i:
            require(parent["reason"] == "clear", "probe_rejected_parent")
        row_check(row, parent, case, old, masks)
        near(row["guide_distance"], scalar_guide(row["state"], case["geometry"]), 1e-8)
        near(row["effort"], 0.0 if i == 0 else parent["effort"] + sum(a * a for a in row["action"]))
    require(
        sum(r["background"] is not None for r in attempts) == result["queries"], "probe_queries"
    )
    require(dict(Counter(r["reason"] for r in attempts[1:])) == result["counts"], "probe_counts")
    depths = result["depths"]
    require(
        [d["frame"] for d in depths]
        == list(range(start["frame"] + 1, start["frame"] + 1 + len(depths)))
        and all(d["complete"] is True for d in depths[:-1]),
        "probe_depths",
    )
    beam, used = [0], 1
    for depth in depths:
        actual = [r for r in attempts[1:] if r["frame"] == depth["frame"]]
        expected = [
            (parent, a)
            for parent in beam
            for a in scalar_proposals(attempts[parent]["state"], case["geometry"], old)
        ]
        require(len(actual) <= len(expected), "probe_extra_proposal")
        for row, (parent, action) in zip(actual, expected):
            require(row["parent"] == parent and row["id"] == used, "probe_proposal_order")
            near(row["action"], action, 1e-10)
            used += 1
        survivors = [r for r in actual if r["reason"] == "clear"]
        require(depth["survivors"] == len(survivors), "probe_survivors")
        if depth["complete"]:
            require(len(actual) == len(expected), "probe_missing_proposal")
            expected_depth = audit_beam(survivors, plan["beam_width"], "exact")
            require(all(depth[k] == v for k, v in expected_depth.items()), "probe_beam")
            beam = depth["beam"]
        else:
            require(depth is depths[-1] and depth["beam"] == [], "probe_partial_depth")
    require(used == len(attempts), "probe_orphan_attempt")
    stop = result["stop"]
    require(
        type(result["witness"]) is bool and result["witness"] == (stop == "checkpoint_witness"),
        "probe_witness_status",
    )
    valid_target = [
        r for r in attempts if r["frame"] == plan["target_frame"] and r["reason"] == "clear"
    ]
    if stop == "checkpoint_witness":
        require(
            len(valid_target) == 1
            and valid_target[0] is attempts[-1]
            and result["selected"] == attempts[-1]["id"],
            "probe_false_witness",
        )
    else:
        require(not valid_target and result["selected"] is None, "probe_hidden_witness")
        if stop == "attempt_budget":
            require(
                result["attempts"] == plan["per_root_attempts"] and not depths[-1]["complete"],
                "probe_budget_stop",
            )
        elif stop == "beam_empty":
            require(depths[-1]["complete"] is True and not depths[-1]["beam"], "probe_empty_stop")
        else:
            require(stop == "time_budget" and not depths[-1]["complete"], "probe_stop")
    chosen = (
        attempts[result["selected"]]
        if result["witness"]
        else min(
            (r for r in attempts if r["reason"] == "clear"),
            key=lambda r: (-r["frame"], ordering(r)),
        )
    )
    suffix = []
    while chosen is not None:
        suffix.append(chosen)
        chosen = attempts[chosen["parent"]] if chosen["parent"] is not None else None
    suffix.reverse()
    require(record["selected_attempt_ids"] == [r["id"] for r in suffix], "probe_path_ids")
    expected = copy.deepcopy(retained_path + suffix[1:])
    for i, row in enumerate(expected):
        row.update(id=i, parent=i - 1 if i else None)
    require(encode(combined) == encode(expected), "probe_path_binding")
    path_check(combined, record["masks"], case, old, masks)
    require(result["witness"] == (combined[-1]["frame"] == plan["target_frame"]), "probe_terminal")
    return result["witness"]
