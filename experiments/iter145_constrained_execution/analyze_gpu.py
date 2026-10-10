"""Recompute bounded smoke results and descriptive timings from retained raw files."""

import hashlib
import json
from pathlib import Path
import statistics

from .gpu_check import verify


def describe(values, deadline):
    return dict(
        count=len(values),
        minimum=min(values),
        median=statistics.median(values),
        maximum=max(values),
        deadline=deadline,
        over_deadline=sum(v > deadline for v in values),
    )


def analyze(root):
    root = Path(root)
    cases = []
    controllers, exchanges, steps, combined, later = [], [], [], [], []
    max_stationarity = 0.0
    renders = actor_advances = foreground_checks = 0
    constructor_reset = []
    for directory in sorted((root / "runs").iterdir()):
        report = verify(directory)
        worker = json.loads((directory / "worker.json").read_text())
        events = [
            json.loads(line) for line in (directory / "trace/events.jsonl").read_text().splitlines()
        ]
        paired = [a + b for a, b in zip(report["exchange_seconds"], report["step_seconds"])]
        controllers.extend(report["controller_ms"])
        exchanges.extend(report["exchange_seconds"])
        steps.extend(report["step_seconds"])
        combined.extend(paired)
        later.extend(paired[1:])
        constructor_reset.append(worker["constructor_seconds"] + worker["summary"]["reset_seconds"])
        renders += len(worker["render_events"])
        foreground_checks += sum(r["kind"] == "foreground" for r in worker["collision_events"])
        for event in events:
            if event["event"] == "control":
                max_stationarity = max(
                    max_stationarity, event["result"]["certificate"]["stationarity_inf"]
                )
            if event["event"] == "actor" and event["value"]["event"] == "consume":
                actor_advances += len(event["value"]["states"])
        cases.append(
            dict(
                episode=report["episode"],
                status=report["status"],
                steps=report["steps"],
                attack_selections=report["attack_selections"],
                controller_ms=describe(report["controller_ms"], 50),
                exchange_seconds=describe(report["exchange_seconds"], 0.25),
                exchange_plus_step_seconds=describe(paired, 0.25),
                events_sha256=hashlib.sha256(
                    (directory / "trace/events.jsonl").read_bytes()
                ).hexdigest(),
            )
        )
    inventory = json.loads((root / "output_inventory.json").read_text())
    output_by_case = [
        sum(
            v["bytes"]
            for k, v in inventory["files"].items()
            if k.startswith("runs/" + r["episode"] + "/")
        )
        for r in cases
    ]
    ply_by_case = [
        sum(
            v["bytes"]
            for k, v in inventory["files"].items()
            if k.startswith("runs/" + r["episode"] + "/") and k.endswith(".ply")
        )
        for r in cases
    ]
    variable_output = [total - fixed for total, fixed in zip(output_by_case, ply_by_case)]
    # Proposal only: a factor of two is an explicit assumption, not a measured bound.
    # Keep the observed slowest first exchange in the all-step maximum calculation.
    conservative_seconds = 2 * 112 * (max(constructor_reset) + 401 * max(combined))
    split_seconds = 2 * 112 * (max(constructor_reset) + max(combined) + 400 * max(later))
    return dict(
        status="supported",
        scope="four nominal 12-step GPU smoke cases",
        raw_commit="7e5976bb9ee4c54dc5f114ca4392d9f16c202510",
        cases=cases,
        steps=sum(r["steps"] for r in cases),
        camera_calls=renders,
        actor_advances=actor_advances,
        foreground_checks=foreground_checks,
        max_stationarity=max_stationarity,
        controller_ms=describe(controllers, 50),
        exchange_seconds=describe(exchanges, 0.25),
        step_seconds=describe(steps, 0.25),
        exchange_plus_step_seconds=describe(combined, 0.25),
        exchange_plus_step_after_first_seconds=describe(later, 0.25),
        timing_scope="Exchange plus step excludes observation hashing, event serialization, and outer-loop overhead; it is a lower bound on complete loop time. First exchange can include client readiness; no separate model-startup timer was retained.",
        output_bytes=inventory["total_bytes"],
        study_projection=dict(
            status="proposed",
            live_admitted=False,
            slots=112,
            max_actions=401,
            safety_factor_assumption=2,
            all_steps_at_observed_max_seconds=conservative_seconds,
            first_step_separated_seconds=split_seconds,
            hourly_upper_usd=3,
            all_steps_at_observed_max_compute_usd=conservative_seconds / 3600 * 3,
            first_step_separated_compute_usd=split_seconds / 3600 * 3,
            crude_output_bytes=2 * 112 * 401 / 12 * max(output_by_case),
            fixed_ply_separated_output_bytes=2
            * 112
            * (max(ply_by_case) + 401 / 12 * max(variable_output)),
            limitations="Four short cases in two scenes do not bound 14 scenarios in three scenes, late trajectory behavior, memory peaks, other arms, or seed 144. Linear output extrapolation includes fixed-size per-case files. The two timing estimates are assumptions, not admitted budgets or costs; setup, analysis, transfer and persistent storage are excluded.",
        ),
        physical_validity="unestablished",
        recovery_result=None,
        live_study_admitted=False,
    )


if __name__ == "__main__":
    print(json.dumps(analyze(Path(__file__).parent / "proof/gpu_raw"), indent=2, allow_nan=False))
