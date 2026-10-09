"""Independent stdlib geometry and raw-state replay; no primary analyzer imports."""

import argparse
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import sys


def box_valid(b):
    if (
        type(b) is not list
        or len(b) != 7
        or any(type(v) not in (int, float) or not math.isfinite(v) for v in b)
        or min(b[3:6]) <= 0
    ):
        raise ValueError("independent invalid box")


def gap(a, b):
    """Maximum unit-axis gap, using center/extent projection, not polygon vertices."""
    box_valid(a)
    box_valid(b)
    delta = (b[0] - a[0], b[1] - a[1])
    axes = [
        (math.cos(t), math.sin(t)) for t in (a[6], a[6] + math.pi / 2, b[6], b[6] + math.pi / 2)
    ]
    result = []
    for nx, ny in axes:
        radii = []
        for box in (a, b):
            c, s = math.cos(box[6]), math.sin(box[6])
            radii.append(box[4] / 2 * abs(nx * c + ny * s) + box[3] / 2 * abs(-nx * s + ny * c))
        result.append(abs(delta[0] * nx + delta[1] * ny) - sum(radii))
    return max(result)


def corners(b):
    c, s = math.cos(b[6]), math.sin(b[6])
    return [
        (b[0] + u * c - v * s, b[1] + u * s + v * c)
        for u, v in [
            (-b[4] / 2, -b[3] / 2),
            (b[4] / 2, -b[3] / 2),
            (b[4] / 2, b[3] / 2),
            (-b[4] / 2, b[3] / 2),
        ]
    ]


def cross(a, b, p):
    return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])


def area_and_distance(a, b):
    """Convex clipping and point-to-edge distance, independent of GEOS."""
    pa, pb = corners(a), corners(b)
    poly = pa[:]
    for i, c in enumerate(pb):
        d = pb[(i + 1) % 4]
        result = []
        if not poly:
            break
        for j, q in enumerate(poly):
            p = poly[j - 1]
            u, v = cross(c, d, p), cross(c, d, q)
            if (u >= 0) != (v >= 0):
                t = u / (u - v)
                result.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
            if v >= 0:
                result.append(q)
        poly = result
    area = (
        abs(sum(poly[i - 1][0] * q[1] - q[0] * poly[i - 1][1] for i, q in enumerate(poly))) / 2
        if poly
        else 0.0
    )
    if gap(a, b) <= 0:
        return area, 0.0

    def segment(p, u, v):
        dx, dy = v[0] - u[0], v[1] - u[1]
        t = max(0, min(1, ((p[0] - u[0]) * dx + (p[1] - u[1]) * dy) / (dx * dx + dy * dy)))
        return math.hypot(p[0] - u[0] - t * dx, p[1] - u[1] - t * dy)

    distance = min(
        segment(p, q[i - 1], q[i])
        for points, q in [(pa, pb), (pb, pa)]
        for p in points
        for i in range(4)
    )
    return area, distance


def close(actual, expected, tol=1e-9):
    if expected is None or type(expected) in (bool, str, int):
        assert type(actual) is type(expected) and actual == expected, (actual, expected)
    elif isinstance(expected, float):
        assert (
            type(actual) in (int, float) and math.isfinite(actual) and abs(actual - expected) <= tol
        ), (actual, expected)
    elif isinstance(expected, list):
        assert isinstance(actual, list) and len(actual) == len(expected)
        for a, e in zip(actual, expected):
            close(a, e, tol)
    else:
        assert isinstance(actual, dict) and set(actual) == set(expected)
        for k, v in expected.items():
            close(actual[k], v, tol)


def integration(f):
    p, q = f["before"], f["after"]
    a, r = f["control"]
    dt = q["timestamp"] - p["timestamp"]

    # Decimal separately checks the linear state equations; transcendental terms use math.
    def D(x):
        return Decimal(str(x))

    velocity = D(p["ego_velo"]) + D(a) * D(dt)
    steering = D(p["ego_steer"]) + D(r) * D(dt)
    theta = p["ego_box"][6]
    expected_xy = [
        p["ego_box"][0] + float(velocity) * math.cos(theta) * dt,
        p["ego_box"][1] + float(velocity) * math.sin(theta) * dt,
    ]
    heading = theta - float(velocity) * math.tan(float(steering)) * dt / 2.7
    return dict(
        dt=abs(dt - 0.25),
        acceleration=abs(q["accelerate"] - a),
        steer_rate=abs(q["steer_rate"] - r),
        speed=float(abs(D(q["ego_velo"]) - velocity)),
        steering=float(abs(D(q["ego_steer"]) - steering)),
        x=abs(q["ego_box"][0] - expected_xy[0]),
        y=abs(q["ego_box"][1] - expected_xy[1]),
        heading=abs(q["ego_box"][6] - heading),
        box_x=abs(q["ego_box"][0] - q["ego_pos"][2]),
        box_y=abs(q["ego_box"][1] + q["ego_pos"][0]),
    )


def relation(f):
    start, end = f["before"], f["after"]
    e0, e1 = start["ego_box"], end["ego_box"]
    o0, o1 = start["obj_boxes"][0], end["obj_boxes"][0]
    x, y = o1[0] - e1[0], o1[1] - e1[1]
    polar = math.atan2(y, x) - e1[6]
    length = math.hypot(x, y)
    longitudinal, lateral = length * math.cos(polar), length * math.sin(polar)
    velocities = []
    for old, new in [(e0, e1), (o0, o1)]:
        velocities.append([4.0 * (new[i] - old[i]) for i in range(2)])
    relative = [b - a for a, b in zip(*velocities)]
    return dict(
        longitudinal_offset_m=longitudinal,
        lateral_offset_m=lateral,
        actor_center_side="behind"
        if longitudinal < -1e-6
        else "ahead"
        if longitudinal > 1e-6
        else "level",
        heading_difference_rad=(o1[6] - e1[6] + math.pi) % (2 * math.pi) - math.pi,
        ego_center_velocity_mps=velocities[0],
        actor_center_velocity_mps=velocities[1],
        relative_center_velocity_mps=relative,
        relative_center_speed_mps=math.hypot(*relative),
        center_closing_rate_mps=4 * (math.dist(o0[:2], e0[:2]) - length),
        interval_seconds=0.25,
        scope="last-interval center displacement, not physical impact severity or contact-face attribution",
    )


def phase_name(header, t):
    start = header["onset"]
    if start is None:
        return "reference"
    if t >= start + header["duration"]:
        return "resumed"
    return "before_pulse" if t < start else "during_pulse"


def comparison(ref, rows):
    pairs = []
    for f in rows[1:-1]:
        for r in ref[1:-1]:
            if r["after"]["timestamp"] == f["after"]["timestamp"]:
                pairs.append(
                    (f["after"]["timestamp"], r["after"]["obj_boxes"], f["after"]["obj_boxes"])
                )
    valid = [(t, a[0], b[0]) for t, a, b in pairs if len(a) == len(b) == 1]
    exact = [t for t, a, b in valid if a != b]
    differing = [t for t, a, b in valid if any(abs(u - v) > 1e-6 for u, v in zip(a, b))]
    return dict(
        compared_post_action_states=len(valid),
        first_exact_difference_time=min(exact) if exact else None,
        first_over_1e_6_difference_time=min(differing) if differing else None,
        max_center_displacement_m=max(math.dist(a[:2], b[:2]) for _, a, b in valid)
        if valid
        else None,
        max_wrapped_heading_difference_rad=max(
            abs((a[6] - b[6] + math.pi) % (2 * math.pi) - math.pi) for _, a, b in valid
        )
        if valid
        else None,
        correspondence_unresolved=len(pairs) != len(valid),
    )


def check_episode(rows, report):
    frames = rows[1:-1]
    assert report["frames"] == len(frames) and len(report["timeline"]) == len(frames)
    ambiguities = []
    max_area_difference = max_distance_difference = 0.0
    all_residuals = []
    positives = []
    single = all(len(f[key]["obj_boxes"]) == 1 for f in frames for key in ("before", "after"))
    assert report["source_inferred_single_actor"] == single
    for i, f in enumerate(frames):
        assert f["frame"] == i and f["time"] == i * 0.25
        if i:
            assert f["before"] == frames[i - 1]["after"], "independent state continuity"
        r = report["timeline"][i]
        check = integration(f)
        assert max(check.values()) <= 1e-9, "independent state integration"
        all_residuals.append(check)
        close(r["kinematic_residuals"], check)
        close(r["time"], f["time"])
        close(r["after_time"], f["after"]["timestamp"])
        close(r["phase"], phase_name(rows[0], f["time"]))
        for field, expected in [
            ("frame", i),
            ("collision", f["collision"]),
            ("control", f["control"]),
            ("before_speed", f["before"]["ego_velo"]),
            ("after_speed", f["after"]["ego_velo"]),
            ("before_steering", f["before"]["ego_steer"]),
            ("after_steering", f["after"]["ego_steer"]),
            ("ego_xy", f["after"]["ego_box"][:2]),
            ("actor_boxes", f["after"]["obj_boxes"]),
            ("raw_progress", f["route_completion"]),
        ]:
            close(r[field], expected)
        for point in ("before", "after"):
            s = f[point]
            objects = s["obj_boxes"]
            assert len(r[point]["actors"]) == len(objects)
            hits = []
            for j, obj in enumerate(objects):
                signed = gap(s["ego_box"], obj)
                detail = r[point]["actors"][j]
                assert detail["index"] == j
                if abs(signed) <= 1e-9:
                    ambiguities.append(dict(frame=i, point=point, index=j, gap_m=signed))
                else:
                    assert detail["intersects"] == (signed < 0), "independent geometry disagreement"
                area, distance = area_and_distance(s["ego_box"], obj)
                max_area_difference = max(
                    max_area_difference, abs(area - detail["overlap_area_m2"])
                )
                max_distance_difference = max(
                    max_distance_difference, abs(distance - detail["distance_m"])
                )
                close(detail["overlap_area_m2"], area)
                close(detail["distance_m"], distance)
                hits.append(signed <= 0)
            if not any(abs(gap(s["ego_box"], o)) <= 1e-9 for o in objects):
                assert r[point]["foreground"] == any(hits)
            if point == "after" and any(hits):
                positives.append(s["timestamp"])
    close(
        report["max_kinematic_residuals"],
        {k: max(r[k] for r in all_residuals) for k in all_residuals[0]},
    )
    assert report["problems"] == []
    close(report["terminal_time"], frames[-1]["after"]["timestamp"])
    close(report["first_foreground_time"], positives[0] if positives else None)
    close(report["foreground_positive_after_states"], len(positives))
    mismatch = [
        i for i, f in enumerate(frames) if (f["after"]["timestamp"] in positives) != f["collision"]
    ]
    close(report["collision_foreground_mismatch_frames"], mismatch)
    assert set(report["phases"]) == {"reference", "before_pulse", "during_pulse", "resumed"}
    for name, value in report["phases"].items():
        group = [f for f in frames if phase_name(rows[0], f["time"]) == name]
        expected = (
            None
            if not group
            else dict(
                frames=len(group),
                start_time=group[0]["time"],
                end_time=group[-1]["after"]["timestamp"],
                start_speed=group[0]["before"]["ego_velo"],
                end_speed=group[-1]["after"]["ego_velo"],
                min_acceleration=min(f["control"][0] for f in group),
                max_acceleration=max(f["control"][0] for f in group),
                min_steer_rate=min(f["control"][1] for f in group),
                max_steer_rate=max(f["control"][1] for f in group),
            )
        )
        close(value, expected)
    close(report["terminal_relation"], relation(frames[-1]) if single else None)
    terminal_supported = (
        not mismatch and positives == [frames[-1]["after"]["timestamp"]] and frames[-1]["collision"]
    )
    return dict(
        frames=len(frames),
        checked_box_states=sum(len(f[p]["obj_boxes"]) for f in frames for p in ("before", "after")),
        ambiguities=ambiguities,
        single_actor=single,
        terminal_contact_supported=terminal_supported,
        max_area_difference_m2=max_area_difference,
        max_distance_difference_m=max_distance_difference,
        max_kinematic_residual=max(max(r.values()) for r in all_residuals),
    )


def read_json(raw):
    def unique(items):
        out = {}
        for k, v in items:
            if k in out:
                raise ValueError("duplicate key")
            out[k] = v
        return out

    def bad(x):
        raise ValueError("nonfinite JSON")

    return json.loads(raw, object_pairs_hook=unique, parse_constant=bad)


def run(root, primary):
    base = root / "experiments/iter140_contact_actuation"
    manifest_bytes = (base / "INPUTS.json").read_bytes()
    manifest = read_json(manifest_bytes)
    assert primary["input_manifest_sha256"] == hashlib.sha256(manifest_bytes).hexdigest()
    blobs = {}
    for name, record in manifest["files"].items():
        parts = Path(name)
        assert not parts.is_absolute() and ".." not in parts.parts
        p = root
        for component in parts.parts:
            p /= component
            assert not p.is_symlink()
        assert p.is_file() and p.stat().st_size == record["bytes"] <= 16 * 1024 * 1024
        raw = p.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == record["sha256"]
        blobs[name] = raw
    scenario_path = (
        "/datasets/nuscenes-full/hugsim/extracted/scenarios/nuscenes/scene-0411-hard-00.yaml"
    )
    host = read_json(
        read_json(
            blobs["experiments/iter136_hugsim_recoverability_canary/proof/host_runtime_1.json"]
        )["stdout"]
    )
    scenario = host["files"][scenario_path]["text"]
    scenario_sha = hashlib.sha256(scenario.encode()).hexdigest()
    assert scenario_sha == "9f38bbdcdc49fe6ac5274a967b9a209417d621f67060357b97deacb887cf67a9"
    runtime = read_json(
        blobs["experiments/iter139_finite_pulse_recoverability/proof/runtime_manifest.json"]
    )
    assert runtime["files"][scenario_path] == scenario_sha
    assert (
        scenario.splitlines().count("  - AttackPlanner") == 1
        and scenario.splitlines().count("- - 0") == 1
    )
    traces = {}
    for name, raw in blobs.items():
        if name.endswith("/iter139_trace.jsonl"):
            traces[name.split("/live/")[1].split("/")[0]] = [
                read_json(line) for line in raw.splitlines()
            ]
    expected = {
        "reference_a",
        "reference_b",
        "pulse_0_1",
        "pulse_0_2",
        "pulse_2_1",
        "pulse_2_2",
        "pulse_4_1",
        "pulse_4_2",
    }
    assert set(traces) == set(primary["episodes"]) == expected
    assert traces["reference_a"] == traces["reference_b"]
    checked = {}
    for arm, rows in traces.items():
        r = primary["episodes"][arm]
        checked[arm] = check_episode(rows, r)
        close(r["actor_comparison"], comparison(traces["reference_a"], rows))
        rawlog = (
            blobs[
                "experiments/iter139_finite_pulse_recoverability/proof/live/" + arm + "/driver.log"
            ]
            .decode()
            .splitlines()
        )
        close(
            r["environment_collision_log"],
            [s for s in rawlog if s in ["Collision with foreground", "Collision with background"]],
        )
    complete = all(
        r["single_actor"] and r["terminal_contact_supported"] and not r["ambiguities"]
        for r in checked.values()
    )
    return dict(
        status="supported" if complete else "inconclusive",
        verdict="CONTACT_ACTUATION_RECONSTRUCTED" if complete else "CONTACT_ACTUATION_INCONCLUSIVE",
        episodes=checked,
        total_frames=sum(r["frames"] for r in checked.values()),
        scope="independent stdlib SAT, clipping, Decimal state arithmetic, terminal geometry and actor-path comparison on one disclosed development case",
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--primary", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    try:
        report = run(a.root, read_json(a.primary.read_bytes()))
        report["primary_sha256"] = hashlib.sha256(a.primary.read_bytes()).hexdigest()
        code = 0
    except (ValueError, AssertionError, KeyError, TypeError, OSError) as exc:
        report = dict(
            status="invalid",
            verdict="CONTACT_ACTUATION_INVALID",
            error_type=type(exc).__name__,
            error=str(exc),
        )
        code = 2
    with a.output.open("x") as f:
        json.dump(report, f, indent=2, sort_keys=True, allow_nan=False)
        f.write("\n")
    print(json.dumps(report, sort_keys=True))
    return code


if __name__ == "__main__":
    sys.exit(main())
