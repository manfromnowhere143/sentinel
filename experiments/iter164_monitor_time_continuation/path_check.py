"""Scalar selected-path admission; deliberately imports no search/vector query."""

import math
import time

import numpy as np

from experiments.iter153_action_feasibility.check import gap, motion, near, swept
from experiments.iter155_background_witness.geometry import count_points, ground_height, vertices
from .common import require, sha


def verify_path(
    trace, geometry, old, points, ground, masks, complete, deadline, allow_rejections=False
):
    require(isinstance(trace, list) and 0 < len(trace) <= old["max_actions"] + 1, "trace_length")
    near(trace[0]["state"], geometry["reset"], 0)
    require(
        trace[0]["id"] == 0 and trace[0]["parent"] is None and trace[0]["action"] is None,
        "reset_identity",
    )
    obstacles = [[o[0], -o[1], o[3], o[4], -o[6]] for o in geometry["obstacles"]]
    dims = geometry["ego_dimensions"]
    max_count, progress_checks, rejections = 0, 0, []
    for frame, row in enumerate(trace):
        require(time.monotonic() < deadline, "checker_deadline")
        require(type(row["frame"]) is int and row["frame"] == frame, "frame_sequence")
        reasons = []
        state = row["state"]
        require(
            len(state) == 5 and all(type(v) in (int, float) and math.isfinite(v) for v in state),
            "state_domain",
        )
        x, y, heading, speed, steering = state
        if frame:
            previous = trace[frame - 1]
            require(row["parent"] == previous["id"], "parent_chain")
            require(previous["route"]["rc"] < 1, "continued_after_completion")
            action = row["action"]
            require(
                len(action) == 2
                and all(type(v) in (int, float) and math.isfinite(v) for v in action),
                "action_domain",
            )
            near(state, motion(previous["state"], action))
            yaw = speed * math.tan(steering) / 2.7
            control_ok = (
                abs(action[0]) <= 2 + 1e-12
                and abs(action[1]) <= math.pi / 12 + 1e-12
                and abs(steering) <= math.pi / 3 + 1e-12
                and -1e-12 <= speed <= 6 + 1e-12
                and abs(yaw) <= 0.95 + 1e-12
                and abs(speed * yaw) <= 4.89 + 1e-12
            )
            if not control_ok:
                reasons.append("controls")
        box2 = [x, y, dims[0], dims[1], heading]
        if not all(gap(box2, obstacle) > 0 for obstacle in obstacles):
            reasons.append("foreground")
        prior_state = trace[frame - 1]["state"] if frame else state
        if not swept(prior_state, state, dims, obstacles, old):
            reasons.append("foreground_sweep")
        distances = [math.hypot(p[0] - y, p[1] - x) for p in geometry["route"]]
        nearest = min(range(len(distances)), key=lambda i: (distances[i], i))
        rc = (nearest + 1) / (0.9 * len(distances))
        require(row["route"]["nearest"] == nearest, "route_index")
        near([row["route"]["distance"], row["route"]["rc"]], [distances[nearest], rc])
        if distances[nearest] > 10:
            reasons.append("route_distance")
        for comparator in geometry["comparators"].values():
            if frame / 4 == comparator["hazard_time"]:
                progress_checks += 1
                if rc < comparator["rc"] - old["progress_slack"]:
                    reasons.append("progress")
        height, _ = ground_height(ground, y, x)
        box = vertices([y, height, x], heading)
        actual = count_points(points, box)
        packed = np.packbits(np.asarray(actual["mask"], dtype=bool), bitorder="little").tobytes()
        require(masks(frame) == packed, "scalar_mask")
        claimed = row["background"]
        require(isinstance(claimed, dict), "missing_background")
        require(
            all(
                type(claimed[k]) is int and claimed[k] == actual[k]
                for k in ("count", "certain_inside", "possible_inside")
            ),
            "scalar_counts",
        )
        require(claimed["mask_sha256"] == sha(packed), "mask_identity")
        decision = (
            "clear"
            if actual["possible_inside"] <= 100
            else ("collision" if actual["certain_inside"] > 100 else "numerically_ambiguous")
        )
        require(claimed["decision"] == decision, "background_decision")
        if decision != "clear":
            reasons.append(decision)
        require(row["reason"] == (reasons[0] if reasons else "clear"), "rejection_reason")
        if reasons:
            rejections.append(dict(frame=frame, reasons=reasons))
            require(allow_rejections, "path_rejected")
        max_count = max(max_count, actual["count"])
    require(
        type(complete) is bool and (trace[-1]["route"]["rc"] >= 1) is complete, "false_completion"
    )
    return dict(
        verified_states=len(trace),
        selected_actions=len(trace) - 1,
        max_background_count=max_count,
        progress_checks=progress_checks,
        rejections=rejections,
        eligible=not rejections,
    )
