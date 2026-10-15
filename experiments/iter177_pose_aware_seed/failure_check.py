"""Post-outcome admission of an invalid run and its retained boundary witness.

No producer, seed, adapter, native planner or vector geometry is imported.
This does not admit the three earlier producer outcomes as qualification results.
"""

import argparse
import json
import math
from pathlib import Path
import time

import numpy as np

from experiments.iter153_action_feasibility.check import motion
from experiments.iter155_background_witness.geometry import count_points, ground_height, vertices
from .check import connection_check
from .common import BASE, encode, git, read, require, rss, sha, source_check, write

SOURCE = "5762157a1ae612fd6c6c2b1c89bba9701f2150cd"
RAW = "314840a3b996860bf5d5a48b51c09254c359fdf1"
FILES = [str(BASE/name) for name in ["failure_check.py", "FAILURE_PROTOCOL.md",
                                    "proof/producer_supervision.json"]]+[
                                        "tests/test_iter177_failure_diagnosis.py"]


def scope(failure, completed_cases, has_execution, supervision):
    require(failure["status"] == "invalid"
            and failure["error"] == "ValueError:worker_failed:chicane_right", "failure_signature")
    require(completed_cases == ["bend_left", "bend_right", "chicane_left"]
            and not has_execution, "incomplete_schedule")
    require(supervision["status"] == "invalid" and supervision["returncode"] == 1
            and supervision["process_reaped"] is True, "producer_closure")


def diagnose(events, case, old, plan):
    require(events[-1]["kind"] == "connection" and events[-1]["call"] == 1
            and sum(row["kind"] == "connection" for row in events) == 1, "diagnostic_population")
    connection = events[-1]
    attempts, _ = connection_check(connection, events[:-1], case, old, plan, plan["attempt_budget"])
    require(connection["result"]["selected_evaluation"] == 1
            and connection["result"]["selected_prefix"] == 5, "selected_witness")
    trace = connection["trace"]
    require(len(trace) == 6, "witness_length")
    reconstructed = trace[0]["state"]
    for row in trace:
        if row["action"] is not None:
            reconstructed = motion(reconstructed, row["action"])
        # Boundary arithmetic is exact; trig motion retains its existing scalar
        # tolerance in connection_check, including across supported host runtimes.
        require(reconstructed[3:] == row["state"][3:], "exact_boundary_actuators")
        state = row["state"]
        height, _ = ground_height(case["ground"], state[1], state[0])
        background = count_points(case["points"], vertices([state[1], height, state[0]], state[2]))
        packed = np.packbits(np.asarray(background["mask"], dtype=bool), bitorder="little").tobytes()
        for key in ["count", "certain_inside", "possible_inside"]:
            require(background[key] == row["background"][key], "scalar_background_count")
        require(sha(packed) == row["background"]["mask_sha256"], "scalar_background_mask")
        require(background["possible_inside"] <= 100
                and row["background"]["decision"] == row["reason"] == "clear", "witness_clear")
    speed, steering = reconstructed[3:]
    require(6 < speed <= 6+1e-12 and abs(steering) <= math.pi/3, "boundary_witness")
    return dict(case="chicane_right", call=1, frame=trace[-1]["frame"],
                initial_speed=trace[0]["state"][3], selected_acceleration=trace[1]["action"][0],
                speed=speed, excess_over_six=speed-6, ulps_above_six=(speed-6)/math.ulp(6.),
                scalar_motion_and_physical_checks=True, strict_next_root_domain=False,
                attempts_checked=attempts, verified_states=len(trace),
                point_state_classifications=len(trace)*len(case["points"]))


def check(root, raw_commit, checker_source):
    started = time.monotonic()
    require(raw_commit == RAW, "raw_identity")
    for name in FILES:
        require(read(root, name) == git(root, "show", checker_source+":"+name), "checker_source")
    git(root, "merge-base", "--is-ancestor", RAW, checker_source)
    plan = json.loads(read(root, BASE/"PLAN.json"))
    source_check(root, plan, SOURCE)
    raw = root/BASE/"proof/search_raw"
    names = git(root, "ls-tree", "-r", "--name-only", RAW, "--", str(BASE/"proof/search_raw")).decode().splitlines()
    require(set(names) == {str(p.relative_to(root)) for p in raw.rglob("*") if p.is_file()}, "raw_inventory")
    total = 0
    for name in names:
        data = read(root, name)
        total += len(data)
        require(data == git(root, "show", RAW+":"+name), "raw_changed")
        require(time.monotonic()-started < 900, "checker_deadline")
    require(total <= plan["max_output_bytes"], "raw_bytes")
    initialized = json.loads(read(raw, "initialized.json"))
    require(initialized["source_commit"] == SOURCE and initialized["plan_sha256"] == sha(encode(plan)),
            "initialized_identity")
    producer_cases = [name for name in plan["cases"] if (raw/name/"result.json").is_file()]
    failure = json.loads(read(raw, "failure.json"))
    supervision = json.loads(read(root, BASE/"proof/producer_supervision.json"))
    scope(failure, producer_cases, (raw/"execution.json").exists(), supervision)
    require(b"ValueError: reset_bounds" in read(raw/"chicane_right", "stderr.txt"), "worker_failure_signature")
    cases = json.loads(read(root, "experiments/iter161_grouping_width_ablation/CASES.json"))
    case = next(c for c in cases if c["id"] == "chicane_right")
    events = [json.loads(line) for line in read(raw/"chicane_right", "events.jsonl").splitlines()]
    old = json.loads(read(root, "experiments/iter153_action_feasibility/PLAN.json"))
    witness = diagnose(events, case, old, plan)
    require(rss() <= 2**30 and time.monotonic()-started < 900, "checker_resources")
    return dict(iteration=177, phase="closed", status="invalid", analysis_status="exploratory",
                claim="The integrated released control-RRT with one pose-aware initial proposal completes all four original cases under unchanged constraints and budgets.",
                source_commit=SOURCE, raw_commit=RAW, checker_source=checker_source,
                qualified_for_source_comparison=False, retained_complete_cases=2, retained_total_cases=4,
                complete_cases=None, total_cases=4, unadmitted_producer_records=len(producer_cases),
                failed_workers=1, diagnosed_requests=1, verified_states=witness["verified_states"],
                point_state_classifications=witness["point_state_classifications"], witness=witness,
                source_recovery=None, superiority=None, transfer=None, new_driving_episodes=0,
                provider_spend=0, elapsed_seconds=time.monotonic()-started, peak_rss_bytes=rss(),
                boundary="Invalid initialized schedule, no retry. Three prior result files remain producer evidence. One retained accepted endpoint is scalar-checked and exceeds the strict next-root speed bound by two ulps. The unlogged next callback input is not independently reconstructed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--raw-commit", required=True)
    parser.add_argument("--checker-source", required=True)
    args = parser.parse_args()
    result = check(args.root.resolve(), args.raw_commit, args.checker_source)
    write(args.root.resolve()/BASE/"proof/admission.json", result)
    print(json.dumps({k:v for k,v in result.items() if k != "claim"}))
