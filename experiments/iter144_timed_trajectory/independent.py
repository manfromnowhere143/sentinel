"""Independent stdlib replay: no imports from trajectory, dynamics, runtime or solver."""

import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

FRAME = "hugsim.local_ab.heading_from_positive_a_toward_b"
BASE = "experiments/iter144_timed_trajectory"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def number(x):
    require(type(x) in (int, float) and math.isfinite(x), "missing/nonfinite numeric evidence")
    return x


def close(a, b, tol=1e-8):
    if isinstance(b, (list, tuple)):
        require(isinstance(a, (list, tuple)) and len(a) == len(b), "numeric shape")
        for x, y in zip(a, b):
            close(x, y, tol)
    else:
        require(abs(number(a) - number(b)) <= tol, "numeric mismatch")


def read(path):
    require(
        not path.is_symlink() and path.is_file() and path.stat().st_size < 32 * 1024 * 1024,
        "file bounds",
    )

    def unique(pairs):
        obj = {}
        for k, v in pairs:
            require(k not in obj, "duplicate JSON key")
            obj[k] = v
        return obj

    def bad(x):
        raise ValueError("invalid JSON constant " + x)

    return json.loads(path.read_bytes(), object_pairs_hook=unique, parse_constant=bad)


def digest(record):
    return hashlib.sha256(
        json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def principal(a):
    return math.atan2(math.sin(a), math.cos(a))


def interpolation(rows, when):
    for i, row in enumerate(rows):
        if row[0] == when:
            return row[1:]
        if row[0] > when:
            require(i > 0, "extrapolation")
            prior = rows[i - 1]
            f = (when - prior[0]) / (row[0] - prior[0])
            values = [prior[j] + (row[j] - prior[j]) * f for j in range(1, 5)]
            values[2] = principal(prior[3] + principal(row[3] - prior[3]) * f)
            return values
    raise ValueError("extrapolation")


def check_trajectory(row):
    require(
        row["schema"] == "sentinel.timed_trajectory.v1" and row["frame"] == FRAME,
        "trajectory contract",
    )
    require(row["units"] == ["s", "m", "m", "rad", "m/s"], "trajectory units")
    require(
        all(isinstance(row[k], str) and row[k] for k in ["episode", "owner", "branch"]), "identity"
    )
    origin = number(row["origin"])
    times = row["times"]
    states = row["states"]
    close(times, [origin + i / 4 for i in range(20)], 0)
    require(len(states) == 20, "trajectory row count")
    for state in states:
        require(len(state) == 4, "state shape")
        for x in state:
            number(x)
    if row["branch"] in ("spline", "low_speed"):
        source = row["source_rows"]
        require(len(source) == 19, "source rows")
        interval = 5 / 19 if row["branch"] == "spline" else 1 / 4
        for i, r in enumerate(source, 1):
            require(len(r) == 7, "source time channel")
            for x in r:
                number(x)
            close(r[6], interval * i, 1e-6)
        knots = [[origin, *states[0]]] + [
            [origin + r[6], r[0], r[1], principal(r[4]), r[2]] for r in source
        ]
        for when, actual in zip(times, states):
            expected = interpolation(knots, when)
            close(actual[:2] + actual[3:], expected[:2] + expected[3:])
            close(principal(actual[2] - expected[2]), 0)
    elif row["branch"] in ("fallback", "constant_forecast"):
        a, b, h, v = states[0]
        require(row["source_rows"] == [], "invented source rows")
        for i, state in enumerate(states):
            close(state, [a + v * math.cos(h) * i / 4, b + v * math.sin(h) * i / 4, h, v])
    else:
        require(row["branch"] == "synthetic_reference", "unknown trajectory branch")


def check_selection(record):
    candidates = record["candidates"]
    require(len(candidates) > 0, "empty candidates")
    ego = record["ego"]
    neighbors = record["neighbors"]
    for row in [*candidates, ego, *neighbors]:
        check_trajectory(row)
        require(
            row["times"] == ego["times"] and row["episode"] == ego["episode"],
            "common time and episode",
        )
    require(
        ego["owner"] == "ego"
        and all(n["owner"] not in ("ego", record["actor"]) for n in neighbors),
        "neighbor identities",
    )
    require(
        all(p["owner"] == record["actor"] and p["origin"] == record["time"] for p in candidates),
        "selection identity",
    )
    values = []
    for p in candidates:
        distances = [math.dist(a[:2], b[:2]) for a, b in zip(p["states"], ego["states"])]
        nearby = sum(
            min(math.dist(a[:2], b[:2]) for a, b in zip(p["states"], n["states"])) < 2
            for n in neighbors
        )
        values.append(min(distances) + nearby / 10)
    close(record["costs"], values)
    require(
        type(record["selected"]) is int and record["selected"] == values.index(min(values)),
        "selection policy",
    )
    require(record["tie_policy"] == "lowest_index", "tie policy")
    return candidates[record["selected"]]


def step(state, requested):
    x, y, h, v, d = map(number, state)
    a, r = map(number, requested)
    a = sorted([-2.0, a, 2.0])[1]
    r = sorted([-math.pi / 12, r, math.pi / 12])[1]
    d1 = sorted([-math.pi / 3, d + r / 4, math.pi / 3])[1]
    r = 4 * (d1 - d)
    v1 = v + a / 4
    return [
        x + v1 * math.cos(h) / 4,
        y + v1 * math.sin(h) / 4,
        h + v1 * math.tan(d1) / 10.8,
        v1,
        d1,
    ], [a, r]


def check_solver(record):
    check_trajectory(record["reference"])
    require(digest(record["reference"]) == record["reference_id"], "reference content identity")
    require(len(record["states"]) == 20 and len(record["inputs"]) == 19, "solver horizon")
    close(record["states"][0], record["initial_state"])
    for current, u, next_state in zip(record["states"], record["inputs"], record["states"][1:]):
        expected, applied = step(current, u)
        close(next_state, expected)
        close(u, applied)
    close(record["proposed"], record["inputs"][0])
    close(record["applied"], step(record["initial_state"], record["proposed"])[1])
    require(record["stop_reason"] in ("converged", "iteration_limit"), "stop reason")
    require(
        type(record["iterations"]) is int and 1 <= record["iterations"] <= 100, "iteration count"
    )
    require(len(record["norms"]) == record["iterations"], "norm count")
    for n in record["norms"]:
        require(number(n) >= 0, "norm")
    require(
        record["stop_reason"] == ("converged" if record["norms"][-1] < 1e-6 else "iteration_limit"),
        "stopping evidence",
    )
    if record["stop_reason"] == "iteration_limit":
        require(record["iterations"] == 100, "iteration cap")
    require(
        0 < number(record["solver_ns"]) <= number(record["complete_call_ns"]), "latency separation"
    )


def check_events(events, selections, native_rows, initial):
    require(len(events) == 23, "reset plus two installs plus twenty consumes")
    require(
        events[0] == dict(event="reset", time=0.0, state=events[0]["state"], advanced=False),
        "reset event",
    )
    close(
        events[0]["state"],
        [initial[0], initial[1], principal(initial[2] + math.pi / 2), initial[3]],
    )
    installs = [e for e in events if e["event"] == "install"]
    consumes = [e for e in events if e["event"] == "consume"]
    require([e["time"] for e in installs] == [0.0, 2.5], "replan schedule")
    require([e["time"] for e in consumes] == [i / 4 for i in range(1, 21)], "consumption times")
    require([s["time"] for s in selections] == [0.0, 2.5], "selection schedule")
    plans = [check_selection(s) for s in selections]
    for ins, p in zip(installs, plans):
        require(ins["plan_id"] == digest(p) and ins["branch"] == p["branch"], "install identity")
    for i, e in enumerate(consumes, 1):
        j = 0 if i <= 10 else 1
        p = plans[j]
        index = i - j * 10
        require(e["plan_id"] == digest(p) and e["plan_origin"] == j * 2.5, "consumption identity")
        close(e["state"], p["states"][index])
        native = [
            e["state"][0],
            e["state"][1],
            principal(e["state"][2] - math.pi / 2),
            e["state"][3],
        ]
        close(native_rows[i - 1], native)
    close(plans[0]["states"][0], events[0]["state"])
    close(plans[1]["states"][0], consumes[9]["state"])


def validate(raw, root):
    require(
        raw["schema"] == "sentinel.iter144.raw.v1" and raw["fixture_status"] == "completed",
        "complete raw data",
    )
    require(
        raw["environment"]["device"] == "cpu" and raw["environment"]["torch_threads"] == 1,
        "execution envelope",
    )
    binding = read(root / BASE / "INPUTS.json")["files"]
    addition = read(root / BASE / "SOURCE_ADDITION.json")
    binding[addition["path"]] = addition
    require(set(raw["inputs"]) == set(binding), "input inventory")
    for name, record in binding.items():
        path = root / name
        require(not path.is_symlink(), "symlink source")
        data = path.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        require(
            len(data) == record["bytes"] and sha == record["sha256"] == raw["inputs"][name],
            "input identity",
        )
    expected = [
        (b, v, y)
        for b, v in [("spline", 4.0), ("low_speed", 1.0), ("fallback", 4.0)]
        for y in [-0.4, 0.0, 0.4]
    ]
    require(
        [(r["branch"], r["velocity"], r["yaw"]) for r in raw["straight"]] == expected,
        "straight fixture inventory",
    )
    max_speed_error = 0.0
    for r in raw["straight"]:
        initial = r["initial"]
        close(initial, [1.0, 2.0, r["yaw"], r["velocity"]])
        require([x["time"] for x in r["rows"]] == [i / 4 for i in range(21)], "straight timestamps")
        for row in r["rows"]:
            tm = row["time"]
            a, b, y, v = initial
            close(row["actor"], [a - v * math.sin(y) * tm, b + v * math.cos(y) * tm, y, v], 1e-5)
        for a, b in zip(r["rows"], r["rows"][1:]):
            error = abs(math.dist(a["actor"][:2], b["actor"][:2]) * 4 - r["velocity"])
            max_speed_error = max(max_speed_error, error)
            require(error < 1e-5, "constant speed displacement")
        check_events(r["events"], r["selections"], [x["actor"] for x in r["rows"][1:]], initial)
        require(
            all(s["candidates"][s["selected"]]["branch"] == r["branch"] for s in r["selections"]),
            "branch fixture identity",
        )
    require(
        [(r["velocity"], r["yaw"]) for r in raw["full_sampler"]]
        == list(itertools.product([0.0, 1.0, 4.0], [-0.4, 0.0, 0.4])),
        "full sampler inventory",
    )
    total_candidates = 0
    for r in raw["full_sampler"]:
        check_selection(r["selection"])
        total_candidates += len(r["selection"]["candidates"])
    require(len(raw["ego"]) == 32, "ego inventory")
    expected = list(
        itertools.product(
            [0.0, 4.0], [0.0, 0.3], [0.0, 0.2], [(0.0, 0.0), (2.0, 0.2), (-2.0, -0.2), (3.0, 0.4)]
        )
    )
    for r, (v, h, d, u) in zip(raw["ego"], expected):
        close(r["state"], [0.0, 0.0, h, v, d])
        close(r["requested"], u)
        out, applied = step(r["state"], u)
        close(r["after"], out)
        close(r["applied"], applied)
    require(len(raw["jacobians"]) == 8, "Jacobian fixture count")
    jac_error = 0.0
    expected = list(
        itertools.product(
            [(1.0, 0.1), (3.0, 0.4), (-3.0, -0.4), (0.0, 0.2)], [0.0, math.pi / 3 - 0.01]
        )
    )
    for r, (u, d) in zip(raw["jacobians"], expected):
        close(r["state"], [0.0, 0.0, 0.3, 4.0, d])
        close(r["requested"], u)
        close(r["epsilon"], 1e-6, 0)
        for field, perturbations, base in [
            ("A", "perturbed_state", r["state"]),
            ("B", "perturbed_input", r["requested"]),
        ]:
            count = len(base)
            require(len(r[perturbations]) == count and len(r[field]) == 5, "Jacobian shape")
            require(all(len(row) == count for row in r[field]), "Jacobian columns")
            for j, p in enumerate(r[perturbations]):
                plus = list(base)
                minus = list(base)
                plus[j] += 1e-6
                minus[j] -= 1e-6
                args1 = (plus, r["requested"]) if field == "A" else (r["state"], plus)
                args2 = (minus, r["requested"]) if field == "A" else (r["state"], minus)
                close(p["plus"], step(*args1)[0])
                close(p["minus"], step(*args2)[0])
                for k in range(5):
                    derivative = (p["plus"][k] - p["minus"][k]) / 2e-6
                    err = abs(number(r[field][k][j]) - derivative)
                    jac_error = max(err, jac_error)
                    require(err <= 1e-5, "Jacobian mismatch")
    expected = list(itertools.product([0.0, 4.0], [False, True], [1, 2]))
    require(
        [(r["velocity"], r["curved"], r["replica"]) for r in raw["solver"]] == expected,
        "solver inventory",
    )
    for row in raw["solver"]:
        check_solver(row["record"])
        params = row["configuration"]["solver"]
        require(
            params["discretization_time"] == 0.25 and params["max_solve_time"] is None,
            "numerical mode",
        )
        close([params["max_acceleration"], params["max_steering_angle_rate"]], [2.0, math.pi / 12])
    for a, b in zip(raw["solver"][::2], raw["solver"][1::2]):
        for key in ("proposed", "applied", "inputs", "states", "norms"):
            close(a["record"][key], b["record"][key], 1e-10)
        require(
            a["record"]["stop_reason"] == b["record"]["stop_reason"]
            and a["record"]["iterations"] == b["record"]["iterations"],
            "replica stops",
        )
    integration = raw["integration"]
    require(len(integration["rows"]) == 20, "integration count")
    close(integration["initial_actor"], [2.0, 5.0, 0.3, 4.0])
    last = [0.0, 0.0, 0.0, 4.0, 0.0]
    for i, r in enumerate(integration["rows"]):
        require(r["tick"] == i, "integration order")
        check_solver(r["controller"])
        p = r["application"]
        close(p["before"], last)
        close(p["requested"], r["controller"]["proposed"])
        close([p["observation_time"], p["application_time"]], [i / 4, (i + 1) / 4])
        out, applied = step(last, p["requested"])
        close(p["applied"], applied)
        close(p["predicted"], out)
        close(p["after"], out)
        close(r["controller"]["initial_state"], last)
        close(r["controller"]["reference"]["origin"], i / 4, 0)
        last = p["after"]
    check_events(
        integration["events"],
        integration["selections"],
        [r["actor"] for r in integration["rows"]],
        integration["initial_actor"],
    )
    require(integration["stop_reason"] == "fixture_horizon", "integration stopping reason")
    all_solver = [r["record"] for r in raw["solver"]] + [
        r["controller"] for r in integration["rows"]
    ]
    return dict(
        status="supported",
        verdict="TIMED_TRAJECTORY_CPU_CONTRACT_SUPPORTED",
        independent_validation="passed",
        straight_sequences=9,
        straight_consumptions=180,
        full_sampler_fixtures=9,
        full_sampler_candidates=total_candidates,
        ego_transitions=32,
        jacobian_fixtures=8,
        max_jacobian_absolute_error=jac_error,
        max_straight_speed_absolute_error=max_speed_error,
        solver_replicate_pairs=4,
        integration_steps=20,
        solver_calls=len(all_solver),
        stop_reasons={
            reason: sum(r["stop_reason"] == reason for r in all_solver)
            for reason in ["converged", "iteration_limit"]
        },
        solver_ns_range=[
            min(r["solver_ns"] for r in all_solver),
            max(r["solver_ns"] for r in all_solver),
        ],
        complete_call_ns_range=[
            min(r["complete_call_ns"] for r in all_solver),
            max(r["complete_call_ns"] for r in all_solver),
        ],
        complete_calls_over_50ms=sum(r["complete_call_ns"] > 50_000_000 for r in all_solver),
        physical_qualification="unestablished",
        full_simulator_qualification="unestablished",
        cloud_access=False,
        live_episodes=0,
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--raw", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    try:
        result = validate(read(a.raw), a.root)
        code = 0
    except (KeyError, ValueError, TypeError, IndexError) as e:
        result = dict(status="invalid", verdict="TIMED_TRAJECTORY_REPLAY_REJECTED", error=str(e))
        code = 2
    with a.output.open("x") as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write("\n")
    print(json.dumps(result))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
