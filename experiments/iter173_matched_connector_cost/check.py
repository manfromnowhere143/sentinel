"""Separate scalar admission and paired estimands; no candidate-generator imports."""

import argparse
import copy
import json
import math
from pathlib import Path
import time

import numpy as np

from experiments.iter153_action_feasibility.check import near
from experiments.iter155_background_witness.geometry import count_points, ground_height, vertices
from experiments.iter168_control_connector.check import physical, verify_trace
from experiments.iter169_full_horizon_control.check import accounting, variables
from experiments.iter172_integrated_rrt.check import connection_check, distance
from .common import BASE, OLD, git, read, require, rss, sha, write
from .records import committed


def expected_proposal(reset, task, number):
    keys = variables(task)
    duration = (task["stop_from"] or task["terminal_frame"]) - task["wait_until"]
    active = task["terminal_frame"] - task["wait_until"]
    if number == 0:
        a = ((0 if task["stop_from"] else task["target"][3]) - reset[3]) / (.25 * max(1, duration))
        r = (task["target"][4] - reset[4]) / (.25 * max(1, active))
        return [max(-1, min(1, a / 2 if k == 0 else r / (math.pi/12))) for _, k in keys]
    if number <= 81:
        n = number - 1
        rate = (0, -1, 1)[n % 3]
        accel = (0, -1, 1)[(n // 3) % 3]
        pr, pa = (n // 9) % 3, n // 27
        signs = [[1, 1, 1, 1], [1, 1, -1, -1], [1, -1, -1, 1]]
        table = [[accel*signs[pa][i], rate*signs[pr][i]] for i in range(4)]
    else:
        vals = []
        for base in [2, 3, 5, 7, 11, 13, 17, 19]:
            integer, denom, value = number-81, 1, 0.0
            while integer:
                digit = integer % base
                integer //= base
                denom *= base
                value += digit / denom
            vals.append(2*value-1)
        table = [vals[i:i+2] for i in range(0, 8, 2)]
    return [table[min(3, 4*(frame-task["wait_until"]-1)//active)][kind] for frame, kind in keys]


def proposal_check(events, reset, task, limit, result):
    requests = [e for e in events if e["kind"] == "request"]
    require(len(requests) <= limit and not result["optimizer"]["started"], "forward_scope")
    for index, req in enumerate(requests):
        require(req["caller"] == ("initial" if index == 0 else "forward_proposal"), "proposal_caller")
        near(req["values"], expected_proposal(reset, task, index), 2e-15)


def bind_requests(root, plan):
    manifest = json.loads(read(root, BASE / "REQUESTS.json"))
    requests, excluded = [], []
    for name in ["bend_left", "bend_right", "chicane_left", "chicane_right"]:
        path = f"experiments/iter172_integrated_rrt/proof/search_raw/{name}/events.jsonl"
        raw = read(root, path)
        require(raw == git(root, "show", plan["request_raw_commit"] + ":" + path), "request_raw_identity")
        for line in raw.splitlines():
            row = json.loads(line)
            if row["kind"] != "connection":
                continue
            if row["result"] is None:
                excluded.append(dict(case=name, call=row["call"], reason=row["stop"]))
                continue
            requests.append(dict(id=f'{name}_{row["call"]:03}', case=name, call=row["call"],
                                 before=row["before"], target=row["target"], task=row["task"],
                                 budget=row["budget"]))
    require(manifest == dict(requests=requests, excluded=excluded), "request_population")
    require(len(requests) == plan["request_count"] == 80 and len(excluded) == 4, "population_size")
    return requests


def masks(trace, case, folder, old, deadline, allow_collision=False):
    collisions = 0
    for i, row in enumerate(trace):
        require(time.monotonic() < deadline, "checker_deadline")
        prev = trace[i-1] if i else row
        require(physical(prev["state"], row["state"], row["action"], row["frame"], case, old) is None,
                "selected_physical")
        state = row["state"]
        height, _ = ground_height(case["ground"], state[1], state[0])
        actual = count_points(case["points"], vertices([state[1], height, state[0]], state[2]))
        packed = np.packbits(np.asarray(actual["mask"], dtype=bool), bitorder="little").tobytes()
        require(read(folder, f'mask_{row["frame"]:03}.bin') == packed, "scalar_mask")
        for key in ["count", "certain_inside", "possible_inside"]:
            require(row["background"][key] == actual[key], "scalar_count")
        require(row["background"]["mask_sha256"] == sha(packed), "scalar_mask_identity")
        label = "clear" if actual["possible_inside"] <= 100 else (
            "collision" if actual["certain_inside"] > 100 else "numerically_ambiguous")
        require(row["background"]["decision"] == row["reason"] == label, "scalar_label")
        collisions += label == "collision"
        require(allow_collision or label == "clear", "selected_background")
    return len(trace), collisions


def request_metrics(trace, request, geometry):
    # Missing edges retain a null gain; the binary improvement outcome is false.
    edge = len(trace) > 1
    gain = distance(request["before"], request["target"]) - distance(
        [*trace[-1]["state"], trace[-1]["frame"]], request["target"]) if edge else None
    checkpoints = sum(any(row["frame"] / 4 == c["hazard_time"] for row in trace[1:])
                      for c in geometry["comparators"].values())
    return dict(admissible=edge, improved=edge and gain > 1e-9, distance_gain=gain,
                checkpoints=checkpoints,
                route_gain=trace[-1]["route"]["rc"]-trace[0]["route"]["rc"] if edge else None)


def cost_curve(events, request, geometry, checkpoints, root_trace):
    evaluations = [e for e in events if e["kind"] == "evaluation"]
    total, candidates, result = 0, [], []
    for cap in checkpoints:
        cap = min(cap, request["budget"])
        candidates = []
        total = 0
        for row in evaluations:
            total += len(row["trace"])-1
            if total > cap:
                break
            if row["selected_prefix"]:
                candidates.append(row)
        def rank(r):
            end = r["trace"][r["selected_prefix"]]
            return (not r["world_complete"], distance([*end["state"], end["frame"]], request["target"]),
                    r["id"], r["selected_prefix"])
        best = min(candidates, key=rank) if candidates else None
        trace = best["trace"][:best["selected_prefix"]+1] if best else root_trace
        result.append(dict(cap=cap, **request_metrics(trace, request, geometry)))
    return result


def verdict(arms, total_controls):
    a, b = arms["shooting"], arms["forward"]
    return (b["constructive_complete"] == total_controls
            and b["improved_requests"] > a["improved_requests"]
            and b["admissible_requests"] >= a["admissible_requests"]
            and b["checkpoint_crossings"] >= a["checkpoint_crossings"])


def check(root, commit):
    started = time.monotonic()
    plan = json.loads(read(root, BASE / "PLAN.json"))
    old = json.loads(read(root, OLD))
    raw = root / BASE / "proof/search_raw"
    execution = committed(root, raw, commit, plan)
    require(execution["children_reaped"] is True, "worker_closure")
    require(json.loads(read(raw, "runtime.json")) == json.loads(read(root, BASE / "RUNTIME.json")), "runtime")
    requests = bind_requests(root, plan)
    cases = json.loads(read(root, BASE / "CASES.json"))
    historical = json.loads(read(root, "experiments/iter168_control_connector/CASES.json"))
    require(cases[:12] == historical and [c["id"] for c in cases] == plan["cases"]
            and len(cases) == plan["constructive_count"] == 14, "constructive_population")
    scenes = json.loads(read(root, "experiments/iter161_grouping_width_ablation/CASES.json"))
    deadline = started + plan["search_checker_seconds"]
    states = points = straight_rejections = 0
    for case in cases:
        folder = raw / (case["id"] + "_witness")
        trace = json.loads(read(folder, "trace.json"))
        require([r["action"] for r in trace[1:]] == case["witness_actions"], "witness_actions")
        metrics = verify_trace(trace, case, old, lambda f: read(folder, f"mask_{f:03}.bin"), True)
        states += metrics["verified_states"]
        points += metrics["verified_states"] * len(case["points"])
        if case["id"].startswith("detour_"):
            folder = raw / (case["id"] + "_straight")
            trace = json.loads(read(folder, "trace.json"))
            require(len(trace) == 17 and all(r["action"] == [0, 0] for r in trace[1:]), "straight_control")
            n, rejects = masks(trace, case, folder, old, deadline, True)
            require(rejects > 0, "detour_obstacle_inactive")
            straight_rejections += 1
            states += n
            points += n*len(case["points"])
    population = [("request", r["id"]) for r in requests] + [("constructive", c["id"]) for c in cases]
    schedule = [(kind, identity, arm) for i, (kind, identity) in enumerate(population)
                for arm in (["shooting", "forward"] if i%2 == 0 else ["forward", "shooting"])]
    require(len(execution["records"]) == len(schedule), "schedule_size")
    admitted = []
    arms = {a:dict(attempts=0, elapsed_seconds=0.0, admissible_requests=0, improved_requests=0,
                   checkpoint_crossings=0, constructive_complete=0) for a in plan["arms"]}
    for (kind, identity, arm), record in zip(schedule, execution["records"]):
        require(time.monotonic() < deadline, "checker_deadline")
        folder = raw / (identity + "_" + arm)
        result = json.loads(read(folder, "result.json"))
        require(result == record and (result["population"], result["id"], result["arm"]) == (kind, identity, arm), "schedule_identity")
        require(0 < result["elapsed_seconds"] <= plan["per_run_seconds"]+2
                and 0 < result["peak_rss_bytes"] <= plan["max_rss_bytes"], "worker_resources")
        events = [json.loads(line) for line in read(folder, "events.jsonl").splitlines()]
        trace = json.loads(read(folder / "selected", "trace.json"))
        if kind == "request":
            req = next(r for r in requests if r["id"] == identity)
            case = next(c for c in scenes if c["id"] == req["case"])
            if arm == "forward":
                proposal_check(events, req["before"][:5], req["task"], plan["max_proposals"], result)
            connection = dict(req, result=result, trace=trace, stop=result["stop"])
            connection_check(connection, events, case, old, plan, req["budget"])
            require(result["materialization_queries"] == len(trace), "materialization_queries")
            n, _ = masks(trace, dict(case, task=req["task"]), folder / "selected", old, deadline)
            metrics = request_metrics(trace, req, case["geometry"])
            metrics["cost_curve"] = cost_curve(events, req, case["geometry"], plan["comparison_checkpoints"], trace[:1])
            arms[arm]["admissible_requests"] += metrics["admissible"]
            arms[arm]["improved_requests"] += metrics["improved"]
            arms[arm]["checkpoint_crossings"] += metrics["checkpoints"]
        else:
            case = next(c for c in cases if c["id"] == identity)
            ev = [e for e in events if e["kind"] == "evaluation"]
            requests_for_check = [e for e in events if e["kind"] == "request"]
            if arm == "forward":
                proposal_check(events, case["geometry"]["reset"], case["task"], plan["max_proposals"], result)
                # The retained accounting checker names any subsequent numeric input
                # 'residual'. Normalize only this interface tag on copies after the
                # independent proposal check; raw provenance remains forward_proposal.
                requests_for_check = copy.deepcopy(requests_for_check)
                for e in requests_for_check:
                    if e["caller"] == "forward_proposal":
                        e["caller"] = "residual"
            local = dict(plan, attempt_budget=plan["constructive_attempt_budget"])
            accounting(ev, requests_for_check, trace, result, case, old, local)
            metrics = verify_trace(trace, case, old, lambda f: read(folder / "selected", f"mask_{f:03}.bin"), result["complete"])
            n = metrics["verified_states"]
            arms[arm]["constructive_complete"] += result["complete"]
        states += n
        points += n * len(case["points"])
        arms[arm]["attempts"] += result["attempts"]
        arms[arm]["elapsed_seconds"] += result["elapsed_seconds"]
        admitted.append(dict(**result, metrics=metrics))
    supported = verdict(arms, len(cases))
    require(rss() <= plan["max_rss_bytes"] and time.monotonic() < deadline, "checker_resources")
    return dict(iteration=173, phase="closed", status="supported" if supported else "contradicted",
                claim="Forward proposals qualify all constructive tasks and increase improved request count without reducing admissible requests or checkpoint crossings under matched caps.",
                source_commit=execution["source_commit"], raw_commit=commit,
                total_requests=len(requests), excluded_unexecuted_requests=4, total_controls=len(cases),
                arms=arms, total_attempts=sum(a["attempts"] for a in arms.values()),
                verified_states=states, point_state_classifications=points,
                straight_controls_rejected=straight_rejections, records=admitted,
                qualified_for_integrated_trial=supported, qualified_for_source_comparison=False,
                source_recovery=None, transfer=None, superiority=None,
                new_driving_episodes=0, provider_spend=0,
                elapsed_seconds=time.monotonic()-started, peak_rss_bytes=rss())


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--raw-commit", required=True)
    a = p.parse_args()
    root = a.root.resolve()
    result = check(root, a.raw_commit)
    write(root / BASE / "proof/admission.json", result)
    print(json.dumps({k:v for k,v in result.items() if k != "records"}), flush=True)
