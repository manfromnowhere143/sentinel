"""Validate live pulse execution and replay every controller call from original source."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from experiments.iter137_controller_execution_contract.verify import Replay, array, require
from experiments.iter138_numerical_live_replay.verify_live import read_contract, same_runtime
from experiments.iter139_finite_pulse_recoverability import trace

CONTROLLER_SHA = "7784c0a885bba33414a680d2f943f3a701d7ba38bf29996908c6a7bd4089dc03"
PARAMS = {
    "cpa_margin": 1.5,
    "dt": 0.5,
    "max_gap": 30.0,
    "min_closing": 3.0,
    "min_score": 0.3,
    "release_k": 4,
    "ttc_thresh": 2.5,
}


def validate_linkage(driving, contract):
    trace.validate(driving)
    header, footer = contract[0], contract[-1]
    require(
        header["schema"] == "sentinel.iter139.controller_trace.v1"
        and header["mode"] == "numerical",
        "controller schema/mode",
    )
    require(
        header["identity"] == driving[0]["identity"]
        and header["controller_sha256"] == CONTROLLER_SHA,
        "controller identity",
    )
    require(
        header["threadpools"] and all(p["num_threads"] == 1 for p in header["threadpools"]),
        "threadpool bound",
    )
    require(
        footer == dict(end="completed", frames=len(driving) - 2) and len(contract) == len(driving),
        "controller count",
    )
    cases = []
    for frame, row in zip(driving[1:-1], contract[1:-1]):
        require(
            set(row)
            == {
                "frame",
                "time",
                "receipt",
                "complete_call_ns",
                "client_roundtrip_ns",
                "incoming_typed",
                "pulse_active",
            },
            "contract fields",
        )
        require(
            type(row["frame"]) is int
            and row["frame"] == frame["frame"]
            and row["time"] == frame["time"],
            "frame linkage",
        )
        incoming = row["incoming_typed"]
        require(incoming["dtype"] in ("<f4", "<f8"), "incoming dtype")
        expected = array(np.asarray(frame["incoming_plan"], dtype=incoming["dtype"]))
        require(incoming == expected and incoming["shape"] == [6, 2], "typed incoming linkage")
        require(
            type(row["pulse_active"]) is bool
            and row["pulse_active"] == trace.pulse_active(driving[0], frame["time"]),
            "pulse timing",
        )
        r = row["receipt"]
        require(r["status"] == "completed" and r["mode"] == "numerical", "controller failure/mode")
        n = r["numerical"]
        plan = n["input"]["plan"]
        require(
            plan["dtype"] == incoming["dtype"] and plan["shape"] == [6, 2], "executed dtype/shape"
        )
        require(plan["values"] == frame["executed_plan"], "executed plan linkage")
        require(
            n["input"]["velocity"] == frame["before"]["ego_velo"]
            and n["input"]["steering"] == frame["before"]["ego_steer"],
            "state linkage",
        )
        require(n["control"] == frame["control"], "applied action linkage")
        require(
            type(row["complete_call_ns"]) is int
            and row["complete_call_ns"] >= r["timing"]["adapter_ns"],
            "complete call timing",
        )
        require(
            type(row["client_roundtrip_ns"]) is int and row["client_roundtrip_ns"] >= 0,
            "client timing",
        )
        require(
            hashlib.sha256(trace.canonical(n)).hexdigest() == r["numerical_sha256"],
            "numerical digest",
        )
        cases.append(
            dict(
                id=str(frame["frame"]),
                dtype=plan["dtype"],
                plan=frame["executed_plan"],
                velocity=frame["before"]["ego_velo"],
                steering=frame["before"]["ego_steer"],
            )
        )
    return cases


def monitor_check(driving, decisions):
    trace.plain(decisions)
    require(len(decisions) == len(driving) - 2, "monitor count")
    for row, d in zip(driving[1:-1], decisions):
        require(
            "trace_error" not in d and d.get("trace_version") == "iter48_hugsim_union_v1",
            "monitor schema/error",
        )
        require(
            d.get("params") == PARAMS
            and type(d.get("frame_index")) is int
            and d["frame_index"] == row["frame"]
            and d.get("ts") == row["time"],
            "monitor configuration/alignment",
        )
        require(type(d.get("brake")) is bool, "monitor brake state")
        expected = [[0.0, 0.0]] * 6 if d["brake"] else d["traj"]
        require(trace.difference(row["incoming_plan"], expected) is None, "monitor delivery")
    return sum(d["brake"] for d in decisions)


def numeric(row):
    return dict(
        incoming_typed=row["incoming_typed"],
        pulse_active=row["pulse_active"],
        numerical=row["receipt"]["numerical"],
    )


def compare_prefix(a, b, ca, cb):
    require(
        a[0]["arm"] == "reference" and a[0]["identity"] == b[0]["identity"], "comparison identity"
    )
    require(same_runtime(ca, cb), "runtime equality")
    if b[0]["arm"] == "reference":
        require(trace.difference(a, b) is None, "reference trace divergence")
        require(
            [numeric(r) for r in ca[1:-1]] == [numeric(r) for r in cb[1:-1]],
            "reference numerical divergence",
        )
        return "matched"
    index = int(b[0]["onset"] * 4)
    if len(a) - 2 <= index or len(b) - 2 <= index:
        return "unobserved"
    require(
        trace.difference(a[1 : index + 1], b[1 : index + 1]) is None, "pre-action trace divergence"
    )
    require(
        [numeric(r) for r in ca[1 : index + 1]] == [numeric(r) for r in cb[1 : index + 1]],
        "pre-action numerical divergence",
    )
    for key in ("time", "before", "observation_sha256", "incoming_plan"):
        require(
            trace.difference(a[index + 1][key], b[index + 1][key]) is None,
            "onset input divergence: " + key,
        )
    require(
        ca[index + 1]["incoming_typed"] == cb[index + 1]["incoming_typed"],
        "onset typed input divergence",
    )
    return "matched"


def outcomes(reference, branch):
    left, rows = reference[1:-1], branch[1:-1]
    collisions = [r["after"]["timestamp"] for r in rows if r["collision"]]
    targets = [r for r in left if r["collision"]]
    require(targets, "reference has no collision")
    target = targets[0]
    t = target["after"]["timestamp"]
    final = rows[-1]
    route = branch[-1]["reason"] == "route_complete"
    horizon_row = next((r for r in rows if r["after"]["timestamp"] == t), None)
    progress = (
        horizon_row["route_completion"]
        if horizon_row
        else final["route_completion"]
        if route and final["after"]["timestamp"] <= t
        else None
    )
    through_hazard = progress is not None
    hazard_collision = any(x <= t for x in collisions)
    hazard_free = not hazard_collision if through_hazard or hazard_collision else None
    active = [r for r in rows if trace.pulse_active(branch[0], r["time"])]
    s, d = branch[0]["onset"], branch[0]["duration"]
    resumed = s is not None and any(r["time"] >= s + d for r in rows)
    complete_pulse = s is not None and len(active) == int(d * 4) and resumed
    progress_ok = progress >= target["route_completion"] - 0.05 if progress is not None else None
    useful = (
        not collisions
        and route
        and progress_ok is True
        and complete_pulse
        and len(active) * 0.25 <= 2
    )
    return dict(
        collision_observed=bool(collisions),
        first_collision_time=collisions[0] if collisions else None,
        terminal_reason=branch[-1]["reason"],
        terminal_time=final["after"]["timestamp"],
        final_route_completion=final["route_completion"],
        reference_hazard_time=t,
        reference_hazard_progress=target["route_completion"],
        hazard_progress=progress,
        observed_hazard_horizon=through_hazard,
        collision_free_through_hazard=hazard_free,
        hazard_progress_bar_met=progress_ok,
        onset_reached=s is not None and any(r["time"] == s for r in rows),
        assigned_override_frames=int(d * 4) if d else 0,
        realized_override_frames=len(active),
        changed_plan_frames=sum(r["incoming_plan"] != r["executed_plan"] for r in active),
        override_seconds=len(active) * 0.25,
        resumption_observed=resumed,
        complete_pulse_observed=complete_pulse,
        useful_recovery=bool(useful),
        censored=branch[-1]["reason"] == "truncated",
    )


def validate_episode(directory, replay):
    p = Path(directory)
    driving = trace.load_trace(p / "iter139_trace.jsonl")
    contract = read_contract(p / "controller139.jsonl")
    cases = validate_linkage(driving, contract)
    for case, row in zip(cases, contract[1:-1]):
        replay.check(row["receipt"], case, "numerical")
    raw = (p / "sentinel_iter48_decisions.jsonl").read_bytes()
    require(len(raw) <= 16 * 1024**2 and raw.endswith(b"\n"), "monitor file size/truncation")
    decisions = [
        json.loads(x, object_pairs_hook=trace._pairs, parse_constant=trace._bad_constant)
        for x in raw.splitlines()
    ]
    brakes = monitor_check(driving, decisions)
    rows = contract[1:-1]

    def quantiles(values):
        v = sorted(values)
        return {
            k: v[(len(v) * q + 99) // 100 - 1]
            for k, q in [("p50", 50), ("p95", 95), ("p99", 99), ("max", 100)]
        }

    summary = dict(
        frames=len(cases),
        actual_dtypes=sorted({r["incoming_typed"]["dtype"] for r in rows}),
        monitor_brake_requests=brakes,
        stop_reasons={
            reason: sum(r["receipt"]["numerical"]["stop_reason"] == reason for r in rows)
            for reason in ("converged", "deadline", "iteration_limit")
        },
        complete_call_ms=quantiles([r["complete_call_ns"] / 1e6 for r in rows]),
        client_roundtrip_ms=quantiles([r["client_roundtrip_ns"] / 1e6 for r in rows]),
        adapter_ms=quantiles([r["receipt"]["timing"]["adapter_ns"] / 1e6 for r in rows]),
        solver_ms=quantiles([r["receipt"]["timing"]["solver_ns"] / 1e6 for r in rows]),
        complete_call_over_50ms=sum(r["complete_call_ns"] > 50_000_000 for r in rows),
        solver_over_50ms=sum(r["receipt"]["timing"]["solver_ns"] > 50_000_000 for r in rows),
        terminal_reason=driving[-1]["reason"],
        terminal_time=driving[-2]["after"]["timestamp"],
        route_completion=driving[-2]["route_completion"],
        files={
            name: hashlib.sha256((p / name).read_bytes()).hexdigest()
            for name in [
                "iter139_trace.jsonl",
                "controller139.jsonl",
                "sentinel_iter48_decisions.jsonl",
            ]
        },
    )
    return driving, contract, summary


def main():
    from experiments.iter139_finite_pulse_recoverability import independent

    parser = argparse.ArgumentParser()
    parser.add_argument("reference", type=Path)
    parser.add_argument("candidate", type=Path, nargs="?")
    args = parser.parse_args()
    replay = Replay()
    a, ca, sa = validate_episode(args.reference, replay)
    result = dict(status="validated", reference=sa)
    if args.candidate:
        b, cb, sb = validate_episode(args.candidate, replay)
        prefix = compare_prefix(a, b, ca, cb)
        secondary = independent.check(
            args.reference / "iter139_trace.jsonl", args.candidate / "iter139_trace.jsonl"
        )
        require(secondary["prefix"] == prefix, "independent prefix disagreement")
        result.update(candidate=sb, prefix=prefix, independent=secondary)
        if b[0]["arm"] == "reference":
            result["verdict"] = (
                "REPLAY_MATCHED"
                if any(r["collision"] for r in a[1:-1])
                else "NO_RECOVERABILITY_TARGET"
            )
        else:
            endpoint = outcomes(a, b)
            require(endpoint == secondary["outcomes"], "independent outcome disagreement")
            result["outcomes"] = endpoint
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
