"""Primary preregistered contact, motion and actor-response diagnostic."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import platform

import numpy
import shapely

from experiments.iter140_contact_actuation.geometry import SourceGeometry
from experiments.iter140_contact_actuation.inputs import (
    ARMS,
    OLD,
    SOURCE,
    load_inputs,
    source_contract,
    strict_json,
    traces,
)


def phase(header, t):
    if header["onset"] is None:
        return "reference"
    if t < header["onset"]:
        return "before_pulse"
    return "during_pulse" if t < header["onset"] + header["duration"] else "resumed"


def residuals(frame):
    b, a = frame["before"], frame["after"]
    acc, rate = frame["control"]
    dt = a["timestamp"] - b["timestamp"]
    v, steer = b["ego_velo"] + acc * dt, b["ego_steer"] + rate * dt
    x, y, yaw = b["ego_box"][0], b["ego_box"][1], b["ego_box"][6]
    return dict(
        dt=abs(dt - 0.25),
        acceleration=abs(a["accelerate"] - acc),
        steer_rate=abs(a["steer_rate"] - rate),
        speed=abs(a["ego_velo"] - v),
        steering=abs(a["ego_steer"] - steer),
        x=abs(a["ego_box"][0] - (x + v * math.cos(yaw) * dt)),
        y=abs(a["ego_box"][1] - (y + v * math.sin(yaw) * dt)),
        heading=abs(a["ego_box"][6] - (yaw - v * math.tan(steer) / 2.7 * dt)),
        box_x=abs(a["ego_box"][0] - a["ego_pos"][2]),
        box_y=abs(a["ego_box"][1] + a["ego_pos"][0]),
    )


def terminal_relation(frame):
    b, a = frame["before"], frame["after"]
    if len(a["obj_boxes"]) != 1 or len(b["obj_boxes"]) != 1:
        return None
    e, o, ep, op = a["ego_box"], a["obj_boxes"][0], b["ego_box"], b["obj_boxes"][0]
    delta = [o[i] - e[i] for i in (0, 1)]
    long = delta[0] * math.cos(e[6]) + delta[1] * math.sin(e[6])
    lateral = -delta[0] * math.sin(e[6]) + delta[1] * math.cos(e[6])
    ev = [(e[i] - ep[i]) / 0.25 for i in (0, 1)]
    ov = [(o[i] - op[i]) / 0.25 for i in (0, 1)]
    rv = [ov[i] - ev[i] for i in (0, 1)]
    return dict(
        longitudinal_offset_m=long,
        lateral_offset_m=lateral,
        actor_center_side="behind" if long < -1e-6 else "ahead" if long > 1e-6 else "level",
        heading_difference_rad=math.atan2(math.sin(o[6] - e[6]), math.cos(o[6] - e[6])),
        ego_center_velocity_mps=ev,
        actor_center_velocity_mps=ov,
        relative_center_velocity_mps=rv,
        relative_center_speed_mps=math.hypot(*rv),
        center_closing_rate_mps=(math.hypot(op[0] - ep[0], op[1] - ep[1]) - math.hypot(*delta))
        / 0.25,
        interval_seconds=0.25,
        scope="last-interval center displacement, not physical impact severity or contact-face attribution",
    )


def compare_actors(reference, candidate):
    ref = {r["after"]["timestamp"]: r["after"]["obj_boxes"] for r in reference[1:-1]}
    first_exact, first_tolerance = None, None
    max_center, max_heading, compared = 0.0, 0.0, 0
    unresolved = False
    for r in candidate[1:-1]:
        t, objs = r["after"]["timestamp"], r["after"]["obj_boxes"]
        if t not in ref:
            continue
        if len(objs) != 1 or len(ref[t]) != 1:
            unresolved = True
            continue
        a, b = objs[0], ref[t][0]
        compared += 1
        if a != b and first_exact is None:
            first_exact = t
        if max(abs(x - y) for x, y in zip(a, b)) > 1e-6 and first_tolerance is None:
            first_tolerance = t
        max_center = max(max_center, math.hypot(a[0] - b[0], a[1] - b[1]))
        max_heading = max(
            max_heading, abs(math.atan2(math.sin(a[6] - b[6]), math.cos(a[6] - b[6])))
        )
    return dict(
        compared_post_action_states=compared,
        first_exact_difference_time=first_exact,
        first_over_1e_6_difference_time=first_tolerance,
        max_center_displacement_m=max_center if compared else None,
        max_wrapped_heading_difference_rad=max_heading if compared else None,
        correspondence_unresolved=unresolved,
    )


def episode(rows, geometry):
    frames = rows[1:-1]
    checks, timeline, problems = [], [], []
    for i, r in enumerate(frames):
        if i and r["before"] != frames[i - 1]["after"]:
            problems.append(dict(frame=i, reason="state continuity"))
        residual = residuals(r)
        if max(residual.values()) > 1e-9:
            problems.append(dict(frame=i, reason="state integration", residuals=residual))
        checks.append(residual)
        before = geometry.measure(r["before"]["ego_box"], r["before"]["obj_boxes"])
        after = geometry.measure(r["after"]["ego_box"], r["after"]["obj_boxes"])
        timeline.append(
            dict(
                frame=i,
                time=r["time"],
                after_time=r["after"]["timestamp"],
                phase=phase(rows[0], r["time"]),
                before=before,
                after=after,
                collision=r["collision"],
                control=r["control"],
                before_speed=r["before"]["ego_velo"],
                after_speed=r["after"]["ego_velo"],
                before_steering=r["before"]["ego_steer"],
                after_steering=r["after"]["ego_steer"],
                ego_xy=r["after"]["ego_box"][:2],
                actor_boxes=r["after"]["obj_boxes"],
                raw_progress=r["route_completion"],
                kinematic_residuals=residual,
            )
        )
    phases = {}
    for name in ("reference", "before_pulse", "during_pulse", "resumed"):
        group = [r for r in timeline if r["phase"] == name]
        phases[name] = (
            None
            if not group
            else dict(
                frames=len(group),
                start_time=group[0]["time"],
                end_time=group[-1]["after_time"],
                start_speed=group[0]["before_speed"],
                end_speed=group[-1]["after_speed"],
                min_acceleration=min(x["control"][0] for x in group),
                max_acceleration=max(x["control"][0] for x in group),
                min_steer_rate=min(x["control"][1] for x in group),
                max_steer_rate=max(x["control"][1] for x in group),
            )
        )
    fg = [r["after_time"] for r in timeline if r["after"]["foreground"]]
    mismatch = [r["frame"] for r in timeline if r["collision"] != r["after"]["foreground"]]
    single = all(len(r[point]["obj_boxes"]) == 1 for r in frames for point in ("before", "after"))
    return dict(
        frames=len(frames),
        terminal_time=frames[-1]["after"]["timestamp"],
        first_foreground_time=fg[0] if fg else None,
        foreground_positive_after_states=len(fg),
        collision_foreground_mismatch_frames=mismatch,
        source_inferred_single_actor=single,
        max_kinematic_residuals={k: max(r[k] for r in checks) for k in checks[0]},
        problems=problems,
        phases=phases,
        terminal_relation=terminal_relation(frames[-1]) if single else None,
        timeline=timeline,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    base = args.root / "experiments/iter140_contact_actuation"
    raw_manifest = (base / "INPUTS.json").read_bytes()
    blobs = load_inputs(args.root, strict_json(raw_manifest))
    contract = source_contract(blobs)
    rows = traces(blobs)
    geometry = SourceGeometry(
        blobs[OLD + "/proof/score_calculator.py.txt"],
        blobs[SOURCE + "/sim/hugsim_env/envs/hug_sim.py.txt"],
    )
    reports = {}
    for arm in ARMS:
        report = episode(rows[arm], geometry)
        report["actor_comparison"] = compare_actors(rows["reference_a"], rows[arm])
        log = blobs[OLD + "/proof/live/" + arm + "/driver.log"].decode().splitlines()
        report["environment_collision_log"] = [
            s for s in log if s in ("Collision with foreground", "Collision with background")
        ]
        reports[arm] = report
    output = dict(
        status="primary_analysis_pending_independent_replay",
        input_manifest_sha256=hashlib.sha256(raw_manifest).hexdigest(),
        source_contract=contract,
        geometry_function_ast_sha256=geometry.ast_hashes,
        environment=dict(
            python=platform.python_version(),
            numpy=numpy.__version__,
            shapely=shapely.__version__,
            geos=shapely.geos_version_string,
        ),
        episodes=reports,
    )
    with args.output.open("x") as f:
        json.dump(output, f, indent=2, sort_keys=True, allow_nan=False)
        f.write("\n")
    print(
        json.dumps(
            dict(
                status=output["status"],
                episodes=len(reports),
                frames=sum(r["frames"] for r in reports.values()),
            )
        )
    )


if __name__ == "__main__":
    main()
