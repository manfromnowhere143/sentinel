"""Typed delivery, original-source controller replay, paired comparison and outcomes."""

import argparse
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from experiments.iter137_controller_execution_contract.verify import Replay, array, require
from experiments.iter138_numerical_live_replay.verify_live import read_contract, same_runtime
from experiments.iter139_finite_pulse_recoverability import verify_live as prior
from experiments.iter139_finite_pulse_recoverability import trace as old_trace
from experiments.iter141_nominal_continuation import trace

FILES = (
    "iter141_trace.jsonl",
    "controller141.jsonl",
    "delivery141.jsonl",
    "sentinel_iter48_decisions.jsonl",
)


def read(path, maximum=64 * 1024**2):
    p = Path(path)
    require(not p.is_symlink() and p.is_file() and p.stat().st_size <= maximum, "file bound")
    raw = p.read_bytes()
    require(len(raw) <= maximum and raw.endswith(b"\n"), "file truncation/size")
    rows = [
        json.loads(x, object_pairs_hook=trace._pairs, parse_constant=trace._bad_constant)
        for x in raw.splitlines()
    ]
    trace.plain(rows)
    return rows, raw.splitlines()


def control_envelope(control, steering):
    require(
        len(control) == 2 and all(type(v) in (float, int) and math.isfinite(v) for v in control),
        "control finite",
    )
    require(type(steering) in (float, int) and math.isfinite(steering), "steering finite")
    a, rate = control
    require(abs(a) <= 3 + 1e-9 and abs(rate) <= 0.4 + 1e-9, "effective control bounds")
    require(
        abs(steering) <= math.pi / 3 + 1e-9 and abs(steering + rate * 0.25) <= math.pi / 3 + 1e-9,
        "steering state bounds",
    )
    return abs(a) > 2  # declared Gym acceleration space, not the research envelope


def normalize_contract(contract):
    c = deepcopy(contract)
    require(c[0]["schema"] == "sentinel.iter141.controller_trace.v1", "contract schema")
    c[0]["schema"] = "sentinel.iter139.controller_trace.v1"
    return c


def validate_linkage(driving, contract, delivery, decisions, decision_bytes):
    cases = prior.validate_linkage(trace.normalized(driving), normalize_contract(contract))
    require(len(delivery) == len(decisions) == len(cases), "delivery/monitor count")
    violations = 0
    for f, c, d, m, raw in zip(driving[1:-1], contract[1:-1], delivery, decisions, decision_bytes):
        require(
            set(d)
            == {
                "schema",
                "frame",
                "time",
                "mode",
                "nominal",
                "proposed",
                "delivered",
                "monitor_sha256",
            },
            "delivery fields",
        )
        require(
            d["schema"] == "sentinel.iter141.delivery.v1"
            and type(d["frame"]) is int
            and d["frame"] == f["frame"]
            and d["time"] == f["time"]
            and d["mode"] == driving[0]["arm"],
            "delivery alignment",
        )
        for key in ("nominal", "proposed", "delivered"):
            v = d[key]
            require(v["dtype"] in ("<f4", "<f8") and v["shape"] == [6, 2], "typed delivery shape")
            require(v == array(np.asarray(v["values"], dtype=v["dtype"])), "typed delivery bytes")
        require(
            "trace_error" not in m
            and m.get("trace_version") == "iter48_hugsim_union_v1"
            and m.get("params") == prior.PARAMS
            and type(m.get("frame_index")) is int
            and m["frame_index"] == f["frame"]
            and m.get("ts") == f["time"]
            and type(m.get("brake")) is bool,
            "monitor config/error/alignment",
        )
        require(hashlib.sha256(raw).hexdigest() == d["monitor_sha256"], "monitor digest")
        require(m["traj"] == d["nominal"]["values"], "nominal monitor linkage")
        nominal = np.asarray(d["nominal"]["values"], dtype=d["nominal"]["dtype"])
        proposed = np.zeros_like(nominal) if m["brake"] else nominal
        require(d["proposed"] == array(proposed), "monitor proposed plan")
        expected = d["nominal"] if d["mode"] == "nominal" else d["proposed"]
        require(
            d["delivered"]
            == expected
            == c["incoming_typed"]
            == c["receipt"]["numerical"]["input"]["plan"],
            "delivered controller linkage",
        )
        violations += control_envelope(f["control"], f["before"]["ego_steer"])
        require(abs(f["after"]["ego_steer"]) <= math.pi / 3 + 1e-9, "observed steering bound")
    return cases, violations


def quantiles(values):
    v = sorted(values)
    return {
        k: v[(len(v) * q + 99) // 100 - 1]
        for k, q in [("p50", 50), ("p95", 95), ("p99", 99), ("max", 100)]
    }


def validate_episode(directory, replay):
    p = Path(directory)
    driving, _ = read(p / FILES[0], 16 * 1024**2)
    contract = read_contract(p / FILES[1])
    delivery, _ = read(p / FILES[2], 16 * 1024**2)
    decisions, raw = read(p / FILES[3], 16 * 1024**2)
    cases, violations = validate_linkage(driving, contract, delivery, decisions, raw)
    for case, row in zip(cases, contract[1:-1]):
        replay.check(row["receipt"], case, "numerical")
    rows = contract[1:-1]
    summary = dict(
        frames=len(cases),
        actual_dtypes=sorted({r["incoming_typed"]["dtype"] for r in rows}),
        monitor_brake_requests=sum(m["brake"] for m in decisions),
        action_contrast_frames=sum(d["nominal"] != d["proposed"] for d in delivery),
        declined_replacement_frames=sum(
            d["nominal"] != d["proposed"] and d["mode"] == "nominal" for d in delivery
        ),
        declared_gym_acceleration_violations=violations,
        declared_gym_steering_rate_violations=sum(
            abs(f["control"][1]) > math.pi / 12 for f in driving[1:-1]
        ),
        declared_gym_any_violation_frames=sum(
            abs(f["control"][0]) > 2 or abs(f["control"][1]) > math.pi / 12 for f in driving[1:-1]
        ),
        stop_reasons={
            s: sum(r["receipt"]["numerical"]["stop_reason"] == s for r in rows)
            for s in ("converged", "deadline", "iteration_limit")
        },
        terminal_reason=driving[-1]["reason"],
        terminal_time=driving[-2]["after"]["timestamp"],
        route_completion=driving[-2]["route_completion"],
        files={name: hashlib.sha256((p / name).read_bytes()).hexdigest() for name in FILES},
    )
    timings = dict(
        complete_call=[r["complete_call_ns"] for r in rows],
        client_roundtrip=[r["client_roundtrip_ns"] for r in rows],
        adapter=[r["receipt"]["timing"]["adapter_ns"] for r in rows],
        solver=[r["receipt"]["timing"]["solver_ns"] for r in rows],
    )
    for key, values in timings.items():
        summary[key + "_ms"] = quantiles([v / 1e6 for v in values])
        summary[key + "_over_50ms"] = sum(v > 50_000_000 for v in values)
    return driving, contract, delivery, summary


def compare(a, b, ca, cb, da, db):
    require(a[0]["identity"] == b[0]["identity"] and same_runtime(ca, cb), "comparison runtime")
    if a[0]["arm"] == b[0]["arm"]:
        require(trace.difference(a, b) is None, "replica trace divergence")
        require(
            [prior.numeric(c) for c in ca[1:-1]] == [prior.numeric(c) for c in cb[1:-1]],
            "replica numerical divergence",
        )
        require(da == db, "replica delivery divergence")
        return dict(prefix="matched", first_contrast=None, comparison="replica")
    require(a[0]["arm"] == "reference" and b[0]["arm"] == "nominal", "comparison arms")
    index = next((i for i, d in enumerate(db) if d["nominal"] != d["proposed"]), None)
    if index is None:
        # An absent contrast still requires the complete observed common prefix.
        n = min(len(da), len(db))
        require(trace.difference(a[1 : n + 1], b[1 : n + 1]) is None, "no-contrast prefix")
        require(
            [prior.numeric(c) for c in ca[1 : n + 1]] == [prior.numeric(c) for c in cb[1 : n + 1]],
            "no-contrast numerical prefix",
        )
        return dict(prefix="unobserved", first_contrast=None, comparison="branch")
    require(index < len(da), "contrast beyond observed reference")
    require(trace.difference(a[1 : index + 1], b[1 : index + 1]) is None, "prefix trace divergence")
    require(
        [prior.numeric(c) for c in ca[1 : index + 1]]
        == [prior.numeric(c) for c in cb[1 : index + 1]],
        "prefix numerical divergence",
    )
    for key in ("time", "before", "observation_sha256"):
        require(
            trace.difference(a[index + 1][key], b[index + 1][key]) is None, "contrast state " + key
        )
    for i in range(index + 1):
        for key in ("nominal", "proposed", "monitor_sha256"):
            require(da[i][key] == db[i][key], "contrast typed monitor input")
    return dict(prefix="matched", first_contrast=index, comparison="branch")


def historical(a, ca, path):
    old = old_trace.load_trace(Path(path) / "iter139_trace.jsonl")
    old_c = read_contract(Path(path) / "controller139.jsonl")
    require(trace.difference(a[1:], old[1:]) is None, "historical reference trace")
    require(
        [prior.numeric(c) for c in ca[1:-1]] == [prior.numeric(c) for c in old_c[1:-1]],
        "historical reference numerical",
    )
    left, right = deepcopy(ca), deepcopy(old_c)
    left[0]["schema"] = right[0]["schema"]
    left[0]["identity"] = right[0]["identity"]
    require(same_runtime(left, right), "historical runtime")
    # The permitted source identity changes are only the driver and instrumented client.
    for key, value in a[0]["identity"].items():
        if key not in ("driver_sha256", "client_sha256"):
            require(value == old[0]["identity"][key], "historical identity")
    return "matched"


def outcomes(a, b, delivery):
    target = next((f for f in a[1:-1] if f["collision"]), None)
    require(target is not None, "reference collision absent")
    t = target["after"]["timestamp"]
    rows = b[1:-1]
    last = rows[-1]
    collisions = [f["after"]["timestamp"] for f in rows if f["collision"]]
    route = b[-1]["reason"] == "route_complete"
    h = next((f for f in rows if f["after"]["timestamp"] == t), None)
    p = (
        h["route_completion"]
        if h
        else last["route_completion"]
        if route and last["after"]["timestamp"] <= t
        else None
    )
    bar = p >= target["route_completion"] - 0.05 if p is not None else None
    contrast = any(d["nominal"] != d["proposed"] for d in delivery)
    return dict(
        collision_observed=bool(collisions),
        first_collision_time=collisions[0] if collisions else None,
        terminal_reason=b[-1]["reason"],
        terminal_time=last["after"]["timestamp"],
        final_route_completion=last["route_completion"],
        reference_hazard_time=t,
        reference_hazard_progress=target["route_completion"],
        hazard_progress=p,
        observed_hazard_horizon=p is not None,
        collision_free_through_hazard=False
        if any(c <= t for c in collisions)
        else True
        if p is not None
        else None,
        hazard_progress_bar_met=bar,
        action_contrast_observed=contrast,
        useful_recovery=bool(not collisions and route and bar is True and contrast),
        censored=b[-1]["reason"] == "truncated",
    )


def main():
    from experiments.iter141_nominal_continuation import independent

    p = argparse.ArgumentParser()
    p.add_argument("reference", type=Path)
    p.add_argument("candidate", type=Path, nargs="?")
    p.add_argument("--historical", type=Path, required=True)
    p.add_argument("--nominal-replica", type=Path)
    args = p.parse_args()
    replay = Replay()
    a, ca, da, sa = validate_episode(args.reference, replay)
    result = dict(status="validated", reference=sa, historical=historical(a, ca, args.historical))
    if args.candidate:
        b, cb, db, sb = validate_episode(args.candidate, replay)
        result.update(candidate=sb, **compare(a, b, ca, cb, da, db))
        secondary = independent.check(args.reference, args.candidate)
        require(secondary["prefix"] == result["prefix"], "independent prefix")
        if b[0]["arm"] == "reference":
            result.update(
                historical_candidate=historical(b, cb, args.historical),
                verdict="REPLAY_MATCHED"
                if any(f["collision"] for f in a[1:-1])
                else "NO_RECOVERABILITY_TARGET",
            )
        else:
            endpoint = outcomes(a, b, db)
            require(endpoint == secondary["outcomes"], "independent outcomes")
            result["outcomes"] = endpoint
        result["independent"] = secondary
        if args.nominal_replica:
            n, cn, dn, sn = validate_episode(args.nominal_replica, replay)
            result["nominal_replica"] = compare(n, b, cn, cb, dn, db)
            result["independent_nominal_replica"] = independent.check(
                args.nominal_replica, args.candidate
            )
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
