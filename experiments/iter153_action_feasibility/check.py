"""Independent scalar policy, dynamics, rectangle support and outcome reconstruction."""

import argparse
import bisect
import json
import math
from pathlib import Path

from experiments.iter147_full_horizon_execution.coordinator import raw_identity
from experiments.iter151_recovery_canary.records import record
from .inputs import BASE, digest, document, load, require


def near(a, b, tolerance=1e-9):
    if isinstance(b, (list, tuple)):
        require(isinstance(a, (list, tuple)) and len(a) == len(b), "numeric_shape")
        for x, y in zip(a, b):
            near(x, y, tolerance)
    else:
        require(
            type(a) in (int, float) and math.isfinite(a) and abs(a - b) <= tolerance,
            "numeric_replay",
        )


def motion(state, action):
    x, y, h, v, d = state
    v, d = v + action[0] / 4, d + action[1] / 4
    return [x + v * math.cos(h) / 4, y + v * math.sin(h) / 4, h + v * math.tan(d) / 10.8, v, d]


def gap(first, second):
    """Analytic rectangle support functions: no producer polygons or projection arrays."""
    axes = []
    for box in (first, second):
        c, s = math.cos(box[4]), math.sin(box[4])
        axes.extend([(c, s), (-s, c)])
    answers = []
    for nx, ny in axes:
        radii = []
        for box in (first, second):
            c, s = math.cos(box[4]), math.sin(box[4])
            radii.append(box[3] / 2 * abs(nx * c + ny * s) + box[2] / 2 * abs(-nx * s + ny * c))
        center = abs((second[0] - first[0]) * nx + (second[1] - first[1]) * ny)
        answers.append(center - sum(radii))
    return max(answers)


def swept(a, b, dimensions, obstacles, plan):
    require(abs(b[2] - a[2]) <= math.pi, "sweep_heading_domain")
    n = plan["sweep_subdivisions"]
    radius = math.sqrt(dimensions[0] ** 2 + dimensions[1] ** 2) / 2
    allowance = math.hypot(b[0] - a[0], b[1] - a[1]) / (2 * n)
    allowance += 2 * radius * math.sin(abs(b[2] - a[2]) / (4 * n))
    for j in range(n):
        t = (j + 0.5) / n
        p = [a[k] * (1 - t) + b[k] * t for k in range(3)]
        ego = [p[0], p[1], dimensions[0], dimensions[1], p[2]]
        for obj in obstacles:
            if gap(ego, obj) <= allowance + plan["foreground_margin"]:
                return False
    return True


def population(plan):
    values = [(v, 0.0, 0.0, 10.0) for v in plan["candidate_speeds"]]
    values += [
        (v, d, s, n)
        for v in plan["candidate_speeds"]
        for d in plan["candidate_offsets"]
        for s in plan["shift_starts"]
        for n in plan["shift_lengths"]
    ]
    return [
        dict(id=f"maneuver_{i:03d}", speed=v, offset=d, start=s, length=n)
        for i, (v, d, s, n) in enumerate(values)
    ]


def path_reference(route, spec, plan):
    points = []
    for lateral, forward in route:
        point = (forward, lateral)
        if not points or math.dist(point, points[-1]) > 1e-12:
            points.append(point)
    require(len(points) > 1, "reference_count")
    arc = [0.0]
    for a, b in zip(points, points[1:]):
        arc.append(arc[-1] + math.dist(a, b))
    result = []
    for i, point in enumerate(points):
        before, after = points[max(0, i - 1)], points[min(len(points) - 1, i + 1)]
        dx, dy = after[0] - before[0], after[1] - before[1]
        length = math.hypot(dx, dy)
        require(length > 1e-12, "reference_tangent")
        start = max(0, min(1, (arc[i] - spec["start"]) / spec["length"]))
        end = max(0, min(1, (arc[i] - plan["return_start"]) / plan["return_length"]))
        q = 10 * start**3 - 15 * start**4 + 6 * start**5
        r = 1 - (10 * end**3 - 15 * end**4 + 6 * end**5)
        offset = spec["offset"] * q * r
        result.append([point[0] - dy / length * offset, point[1] + dx / length * offset])
    length = [0.0]
    for a, b in zip(result, result[1:]):
        length.append(length[-1] + math.dist(a, b))
    return result, length


def policy(state, points, lengths, spec, plan):
    k = min(range(len(points)), key=lambda i: (math.dist(points[i], state[:2]), i))
    station = min(lengths[-1], lengths[k] + plan["lookahead"])
    j = min(len(lengths) - 1, bisect.bisect_right(lengths, station))
    denominator = lengths[j] - lengths[j - 1]
    require(denominator > 0, "reference_interval")
    t = (station - lengths[j - 1]) / denominator
    target = [points[j - 1][c] + t * (points[j][c] - points[j - 1][c]) for c in (0, 1)]
    dx, dy = target[0] - state[0], target[1] - state[1]
    distance = math.hypot(dx, dy)
    steer = (
        0
        if distance <= 1e-12
        else math.atan(2.7 * 2 * math.sin(math.atan2(dy, dx) - state[2]) / distance)
    )
    steer = max(-math.pi / 3, min(math.pi / 3, steer))
    return [
        max(-2, min(2, 4 * (spec["speed"] - state[3]))),
        max(-math.pi / 12, min(math.pi / 12, 4 * (steer - state[4]))),
    ]


def verify_trial(raw, geometry, spec, plan, replica):
    require(
        set(raw)
        == {
            "schema",
            "candidate",
            "replica",
            "geometry_sha256",
            "plan_sha256",
            "states",
            "actions",
            "rows",
            "stop",
            "producer",
            *plan["required_unknowns"],
        },
        "trial_fields",
    )
    require(raw["schema"] == "sentinel.iter153.trial.v1", "trial_schema")
    require(
        raw["candidate"] == spec and type(raw["replica"]) is int and raw["replica"] == replica,
        "trial_identity",
    )
    require(
        raw["geometry_sha256"] == digest(geometry) and raw["plan_sha256"] == digest(plan),
        "trial_binding",
    )
    require(all(raw[k] is None for k in plan["required_unknowns"]), "unobserved_claim")
    states, actions, rows = raw["states"], raw["actions"], raw["rows"]
    require(
        len(states) == len(actions) + 1 and len(rows) == len(actions) <= plan["max_actions"],
        "trial_cardinality",
    )
    near(states[0], geometry["reset"], 0)
    dims = geometry["ego_dimensions"]
    require(
        len(dims) == 3
        and all(type(v) in (int, float) and math.isfinite(v) and v > 0 for v in dims),
        "checker_dimensions",
    )
    objects = [[o[0], -o[1], o[3], o[4], -o[6]] for o in geometry["obstacles"]]
    require(objects and all(len(o) == 5 and min(o[2:4]) > 0 for o in objects), "checker_geometry")
    path, lengths = path_reference(geometry["route"], spec, plan)
    initial = [states[0][0], states[0][1], dims[0], dims[1], states[0][2]]
    stop = "initial_contact" if any(gap(initial, obj) <= 0 for obj in objects) else None
    clear, progress_rows = True, []
    for i, action in enumerate(actions):
        require(stop is None, "continued_after_terminal")
        near(action, policy(states[i], path, lengths, spec, plan))
        predicted = motion(states[i], action)
        near(states[i + 1], predicted)
        x, y, h, v, d = states[i + 1]
        yaw = v * math.tan(d) / 2.7
        valid = bool(
            abs(action[0]) <= 2 + 1e-12
            and abs(action[1]) <= math.pi / 12 + 1e-12
            and abs(d) <= math.pi / 3 + 1e-12
            and -1e-12 <= v <= 6 + 1e-12
            and abs(yaw) <= 0.95 + 1e-12
            and abs(v * yaw) <= 4.89 + 1e-12
        )
        box = [x, y, dims[0], dims[1], h]
        collision = any(gap(box, obj) <= 0 for obj in objects)
        clear = clear and swept(states[i], states[i + 1], dims, objects, plan)
        distances = [math.hypot(p[0] - y, p[1] - x) for p in geometry["route"]]
        nearest = min(range(len(distances)), key=lambda k: (distances[k], k))
        rc, distance = (nearest + 1) / (0.9 * len(distances)), distances[nearest]
        row = rows[i]
        require(type(row["nearest"]) is int and row["nearest"] == nearest, "route_index")
        near([row["time"], row["rc"], row["distance"]], [(i + 1) / 4, rc, distance])
        require(
            row["foreground_collision"] is collision and row["controls_valid"] is valid,
            "outcome_flags",
        )
        progress_rows.append(dict(time=(i + 1) / 4, rc=rc))
        if not valid or collision or distance > 10 or rc >= 1:
            stop = (
                "controls_invalid"
                if not valid
                else "foreground_contact"
                if collision
                else "off_route"
                if distance > 10
                else "model_complete"
            )
    if stop is None:
        require(len(actions) == plan["max_actions"], "unexpected_partial")
        stop = "censored"
    require(raw["stop"] == stop, "stop_reason")
    complete = stop == "model_complete"
    progress = {}
    for name, comparator in geometry["comparators"].items():
        row = next((r for r in progress_rows if r["time"] == comparator["hazard_time"]), None)
        progress[name] = (
            True
            if complete and rows[-1]["time"] < comparator["hazard_time"]
            else None
            if row is None
            else row["rc"] >= comparator["rc"] - 0.05
        )
    expected = dict(
        model_complete=complete,
        swept_clear=clear,
        progress=progress,
        eligible=complete and clear and all(v is True for v in progress.values()),
    )
    require(digest(raw["producer"]) == digest(expected), "producer_verdict")
    return dict(
        candidate=spec,
        stop=stop,
        actions=len(actions),
        completion_time=len(actions) / 4 if complete else None,
        **expected,
        background_collision=None,
        road_compliance=None,
        live_recovery=None,
        information_benefit=None,
    )


def inventory(directory, specs, replicas):
    expected = {"initialized.json", "geometry.json", "execution.json"}
    expected |= {f"{s['id']}_{r}.json" for s in specs for r in range(1, replicas + 1)}
    require({p.name for p in Path(directory).iterdir()} == expected, "raw_inventory")


def verify_search(root, directory, commit):
    root, directory = Path(root).resolve(), Path(directory).resolve()
    identity = raw_identity(root, commit, directory)
    geometry = load(root)
    require(document(directory / "geometry.json") == geometry, "extracted_geometry")
    plan = document(root / BASE / "PLAN.json")
    start, execution = (
        document(directory / "initialized.json"),
        document(directory / "execution.json"),
    )
    require(
        start["plan_sha256"] == digest(plan)
        and start["source_sha256"] == digest(document(root / BASE / "SOURCE.json")),
        "execution_binding",
    )
    require(
        execution["status"] == "completed"
        and execution["retained_trials"] == 150
        and execution["uninitialized_trials"] == 0
        and 0 < execution["elapsed_seconds"] <= 600,
        "execution_incomplete",
    )
    specs = population(plan)
    inventory(directory, specs, plan["replicas"])
    summaries, total = [], 0
    for spec in specs:
        originals = []
        for replica in (1, 2):
            raw = document(directory / f"{spec['id']}_{replica}.json")
            result = verify_trial(raw, geometry, spec, plan, replica)
            total += result["actions"]
            originals.append({k: v for k, v in raw.items() if k != "replica"})
        require(originals[0] == originals[1], "replica_disagreement")
        summaries.append(result)
    eligible = sorted(
        [r for r in summaries if r["eligible"]],
        key=lambda r: (r["completion_time"], abs(r["candidate"]["offset"]), r["candidate"]["id"]),
    )
    return dict(
        status="supported",
        raw_commit=commit,
        raw_inventory_sha256=identity,
        candidates=75,
        replicas=2,
        verified_model_actions=total,
        eligible_model_candidates=len(eligible),
        selected=eligible[0] if eligible else None,
        results=summaries,
        background_collision=None,
        road_compliance=None,
        live_recovery=None,
        information_benefit=None,
        scope="Finite privileged-state reduced-model search. No live simulator recovery or physical/road guarantee.",
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--raw", type=Path, required=True)
    p.add_argument("--commit", required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = verify_search(args.root, args.raw, args.commit)
    record(args.output, result)
    print(json.dumps({k: v for k, v in result.items() if k not in ("results", "selected")}))
