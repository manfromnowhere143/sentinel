"""Independent scalar continuation admission; no producer/vector-query imports."""

import argparse
import json
import math
from pathlib import Path
import time

from experiments.iter153_action_feasibility.check import gap, motion, near, swept
from experiments.iter155_background_witness.geometry import count_points, ground_height, vertices
from .common import (
    BASE,
    PREVIOUS,
    OLD,
    encode,
    git,
    read,
    require,
    rss,
    sha,
    source_check,
    validate_inputs,
    write,
)


def scalar(before, state, action, frame, case, old):
    geometry = case["geometry"]
    x, y, heading, speed, steering = state
    distances = [math.hypot(p[0] - y, p[1] - x) for p in geometry["route"]]
    nearest = min(range(len(distances)), key=lambda i: (distances[i], i))
    route = dict(
        nearest=nearest, distance=distances[nearest], rc=(nearest + 1) / (0.9 * len(distances))
    )
    predicates = dict.fromkeys(
        (
            "controls",
            "foreground",
            "foreground_sweep",
            "route_distance",
            "progress",
            "background",
            "completion",
        )
    )
    objects = [[o[0], -o[1], o[3], o[4], -o[6]] for o in geometry["obstacles"]]
    dims = geometry["ego_dimensions"]
    reason = None
    if frame:
        yaw = speed * math.tan(steering) / 2.7
        predicates["controls"] = (
            abs(action[0]) <= 2 + 1e-12
            and abs(action[1]) <= math.pi / 12 + 1e-12
            and abs(steering) <= math.pi / 3 + 1e-12
            and -1e-12 <= speed <= 6 + 1e-12
            and abs(yaw) <= 0.95 + 1e-12
            and abs(speed * yaw) <= 4.89 + 1e-12
        )
        if not predicates["controls"]:
            reason = "controls"
    if reason is None:
        predicates["foreground"] = all(
            gap([x, y, dims[0], dims[1], heading], o) > 0 for o in objects
        )
        if not predicates["foreground"]:
            reason = "foreground"
    if reason is None and frame:
        predicates["foreground_sweep"] = swept(before, state, dims, objects, old)
        if not predicates["foreground_sweep"]:
            reason = "foreground_sweep"
    if reason is None:
        predicates["route_distance"] = distances[nearest] <= 10
        if not predicates["route_distance"]:
            reason = "route_distance"
    if reason is None:
        due = [c for c in geometry["comparators"].values() if frame / 4 == c["hazard_time"]]
        if due:
            predicates["progress"] = all(
                route["rc"] >= c["rc"] - old["progress_slack"] for c in due
            )
            if not predicates["progress"]:
                reason = "progress"
    background, packed = None, None
    if reason is None:
        height, _ = ground_height(case["ground"], y, x)
        actual = count_points(case["points"], vertices([y, height, x], heading))
        packed_array = bytearray((len(actual["mask"]) + 7) // 8)
        for i, value in enumerate(actual["mask"]):
            if value:
                packed_array[i // 8] |= 1 << (i % 8)
        packed = bytes(packed_array)
        decision = (
            "clear"
            if actual["possible_inside"] <= 100
            else ("collision" if actual["certain_inside"] > 100 else "numerically_ambiguous")
        )
        background = {k: actual[k] for k in ("count", "certain_inside", "possible_inside")}
        background.update(decision=decision, mask_sha256=sha(packed))
        predicates["background"] = decision == "clear"
        if decision != "clear":
            reason = "background_" + decision
        else:
            predicates["completion"] = route["rc"] >= 1
    return dict(
        route=route, predicates=predicates, background=background, reason=reason or "clear"
    ), packed


def verify(trace, pair, arm, case, old, masks, deadline):
    require(
        trace["pair"] == pair["id"] and trace["case"] == pair["case"] and trace["arm"] == arm,
        "trace_identity",
    )
    history = pair[arm + "_prefix"]
    commands = [r["action"] for r in history[1:]] + pair["suffix"]
    rows = trace["rows"]
    require(0 < len(rows) <= len(commands) + 1, "trace_length")
    near(rows[0]["state"], case["geometry"]["reset"], 0)
    queried, classifications, checkpoints, max_count = [], 0, 0, None
    stopped = False
    for frame, row in enumerate(rows):
        require(time.monotonic() < deadline, "checker_deadline")
        require(not stopped, "continued_after_terminal")
        require(type(row["frame"]) is int and row["frame"] == frame, "absolute_frame")
        require(row["action"] == (None if not frame else commands[frame - 1]), "fixed_command")
        state = row["state"]
        require(
            len(state) == 5 and all(type(v) in (int, float) and math.isfinite(v) for v in state),
            "state_domain",
        )
        before = rows[frame - 1]["state"] if frame else state
        if frame:
            near(state, motion(before, row["action"]))
        if frame <= pair["frame"]:
            require(
                {k: row[k] for k in ("frame", "state", "action")} == history[frame],
                "prefix_binding",
            )
        actual, packed = scalar(before, state, row["action"], frame, case, old)
        near(
            [row["route"]["distance"], row["route"]["rc"]],
            [actual["route"]["distance"], actual["route"]["rc"]],
        )
        require(row["route"]["nearest"] == actual["route"]["nearest"], "route_index")
        require(encode(row["predicates"]) == encode(actual["predicates"]), "predicate_vector")
        require(row["reason"] == actual["reason"], "first_failure")
        require(encode(row["background"]) == encode(actual["background"]), "scalar_background")
        if packed is not None:
            require(masks(frame) == packed, "scalar_mask")
            queried.append(frame)
            classifications += len(case["points"])
            max_count = max(max_count or 0, actual["background"]["count"])
        if actual["predicates"]["progress"] is not None:
            checkpoints += 1
        if frame <= pair["frame"]:
            require(
                actual["reason"] == "clear" and not actual["predicates"]["completion"],
                "invalid_prefix",
            )
        stopped = actual["reason"] != "clear" or actual["predicates"]["completion"] is True
    if actual["reason"] != "clear":
        stop = actual["reason"]
    elif actual["predicates"]["completion"]:
        stop = "model_complete"
    else:
        require(len(rows) == len(commands) + 1, "premature_exhaustion")
        stop = "suffix_exhausted"
    require(trace["stop"] == stop, "terminal_status")
    return dict(
        stop=stop,
        states=len(rows),
        queried_frames=queried,
        point_state_classifications=classifications,
        checkpoints=checkpoints,
        final_frame=rows[-1]["frame"],
        final_progress=rows[-1]["route"]["rc"],
        max_background_count=max_count,
    )


def check(root, raw, commit):
    started = time.monotonic()
    plan = json.loads(read(root, BASE / "PLAN.json"))
    prefix_path = raw.relative_to(root).as_posix()
    names = (
        git(root, "ls-tree", "-r", "--name-only", commit, "--", prefix_path).decode().splitlines()
    )
    require(
        set(names) == {p.relative_to(root).as_posix() for p in raw.rglob("*") if p.is_file()},
        "raw_inventory",
    )
    total = 0
    for name in names:
        data = read(root, name)
        total += len(data)
        require(data == git(root, "show", commit + ":" + name), "raw_not_committed")
    require(total <= plan["max_output_bytes"], "output_budget")
    execution = json.loads(read(raw, "execution.json"))
    initialized = json.loads(read(raw, "initialized.json"))
    source = execution["source_commit"]
    source_check(root, plan, source)
    git(root, "merge-base", "--is-ancestor", source, commit)
    require(
        execution["plan_sha256"] == initialized["plan_sha256"] == sha(encode(plan))
        and initialized["source_commit"] == source,
        "initialization_identity",
    )
    require(
        execution["status"] == "completed"
        and execution["new_driving_episodes"] == 0
        and execution["provider_spend"] == 0,
        "execution_status",
    )
    require(0 < execution["elapsed_seconds"] <= plan["producer_seconds"], "producer_time")
    require(0 < execution["peak_rss_bytes"] <= plan["max_rss_bytes"], "producer_memory")
    inputs = json.loads(read(root, BASE / "INPUTS.json"))
    validate_inputs(root, inputs)
    old = json.loads(read(root, OLD))
    cases = {c["id"]: c for c in json.loads(read(root, PREVIOUS / "CASES.json"))}
    expected, records = {"initialized.json", "execution.json"}, []
    for i, pair in enumerate(inputs["pairs"]):
        for arm in ("discarded", "representative"):
            name = f"pair_{i}_{arm}"
            folder = raw / name
            trace = json.loads(read(folder, "trace.json"))
            result = verify(
                trace,
                pair,
                arm,
                cases[pair["case"]],
                old,
                lambda f: read(folder, f"mask_{f:03d}.bin", 40000),
                started + plan["checker_seconds"],
            )
            expected.add(name + "/trace.json")
            expected.update(f"{name}/mask_{f:03d}.bin" for f in result.pop("queried_frames"))
            if arm == "discarded":
                require(result["stop"] == "model_complete", "positive_control_failed")
            records.append(dict(name=name, pair=pair["id"], case=pair["case"], arm=arm, **result))
    require(
        {p.relative_to(raw).as_posix() for p in raw.rglob("*") if p.is_file()} == expected,
        "raw_file_set",
    )
    require(len(execution["records"]) == len(records), "record_population")
    for reported, admitted in zip(execution["records"], records):
        require(all(admitted[k] == v for k, v in reported.items()), "record_binding")
    require(
        rss() <= plan["max_rss_bytes"] and time.monotonic() - started <= plan["checker_seconds"],
        "checker_resources",
    )
    preserved = sum(r["stop"] == "model_complete" for r in records if r["arm"] == "representative")
    return dict(
        iteration=160,
        status="supported" if preserved == 5 else "contradicted",
        phase="closed",
        claim="Every retained representative completes under the same remaining witness commands.",
        source_commit=source,
        raw_commit=commit,
        pairs=5,
        historical_bindings=16,
        trajectories=10,
        positive_controls=5,
        preserved_pairs=preserved,
        changed_pairs=5 - preserved,
        records=records,
        verified_states=sum(r["states"] for r in records),
        point_state_classifications=sum(r["point_state_classifications"] for r in records),
        elapsed_seconds=time.monotonic() - started,
        peak_rss_bytes=rss(),
        new_driving_episodes=0,
        provider_spend=0,
        whole_search_causation=None,
        alternative_continuations=None,
        native_recovery=None,
        information_benefit=None,
        physical_safety=None,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True, type=Path)
    p.add_argument("--raw", required=True, type=Path)
    p.add_argument("--raw-commit", required=True)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    write(args.output, check(args.root.resolve(), args.raw.resolve(), args.raw_commit))
