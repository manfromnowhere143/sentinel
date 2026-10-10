"""Scalar replay of released monitor decisions conditional on retained accepted objects."""

import math
from experiments.iter145_constrained_execution.independent import check, close

PARAMS = dict(
    cpa_margin=1.5,
    dt=0.5,
    max_gap=30.0,
    min_closing=3.0,
    min_score=0.3,
    release_k=4,
    ttc_thresh=2.5,
)


def replay(rows):
    tracks, braking, clear = {}, False, 0
    fired_count, brake_count, releases = 0, 0, 0
    for frame, row in enumerate(rows):
        check(
            row["params"] == PARAMS and row["frame_index"] == frame and row["ts"] == frame / 4,
            "monitor parameters/clock",
        )
        check(row["pre_braking"] is braking and row["pre_clear"] == clear, "monitor prior state")
        rotation, translation = row["l2g_r_mat"], row["l2g_t"]

        def world(x, y):
            return [rotation[k][0] * x + rotation[k][1] * y + translation[k] for k in range(2)]

        trajectory = [world(*point) for point in row["traj"]]
        cpa = ttc = 1e9
        current = {}
        for obj in row["objs"]:
            x, y = obj["bev"]
            key = obj["id"]
            check(
                key not in current
                and obj["score"] >= PARAMS["min_score"]
                and math.hypot(x, y) <= 30,
                "monitor accepted object",
            )
            position = world(x, y)
            close(position, obj["world"])
            velocity = [0.0, 0.0]
            if key in tracks:
                previous, time = tracks[key]
                delta = row["ts"] - time
                if delta > 1e-3:
                    velocity = [(v - p) / delta for v, p in zip(position, previous)]
            close(velocity, obj["vel"])
            current[key] = (position, row["ts"])
            for knot, ego in enumerate(trajectory, 1):
                cpa = min(
                    cpa,
                    math.hypot(
                        *(e - (p + v * knot * 0.5) for e, p, v in zip(ego, position, velocity))
                    ),
                )
            delta = [a - b for a, b in zip(translation[:2], position)]
            gap = math.hypot(*delta)
            if gap > 1e-3:
                closing = sum(a * b for a, b in zip(velocity, delta)) / gap
                if closing > 3:
                    ttc = min(ttc, gap / closing)
        tracks = current
        fired = cpa < 1.5 or ttc < 2.5
        release = False
        if fired:
            braking, clear = True, 0
        elif braking:
            clear += 1
            if clear >= 4:
                braking, clear, release = False, 0, True
        close(row["min_cpa"], cpa)
        close(row["min_ttc"], ttc)
        check(
            row["fired"] is fired
            and row["brake"] is braking
            and row["post_braking"] is braking
            and row["post_clear"] == clear
            and row["release"] is release,
            "monitor decision replay",
        )
        fired_count += fired
        brake_count += braking
        releases += release
    return dict(
        frames=len(rows),
        firings=fired_count,
        braking_frames=brake_count,
        releases=releases,
        scope="Decision replay conditional on logged accepted objects; detector filtering/completeness not independently established.",
    )
