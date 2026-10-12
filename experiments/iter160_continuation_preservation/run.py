"""One fixed-suffix acquisition; every path starts at the actual reset."""

import argparse
import json
from pathlib import Path
import platform
import shutil
import sys
import time

import numpy as np

from experiments.iter153_action_feasibility.geometry import (
    ego_box,
    obstacles,
    route_outcome,
    separation,
    sweep_clear,
)
from experiments.iter153_action_feasibility.planner import limits, transition
from experiments.iter158_constraint_aware_search.search import summary
from experiments.iter159_route_search_qualification.run import query_for
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


def evaluate(before, state, action, frame, case, old, query):
    geometry = case["geometry"]
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
    route = route_outcome(state, geometry["route"])
    boxes = obstacles(geometry)
    checks = [
        ("controls", lambda: limits(state, action, old), bool(frame)),
        (
            "foreground",
            lambda: all(
                separation(ego_box(state, geometry["ego_dimensions"]), b) > 0 for b in boxes
            ),
            True,
        ),
        (
            "foreground_sweep",
            lambda: sweep_clear(before, state, geometry["ego_dimensions"], boxes, old),
            bool(frame),
        ),
        ("route_distance", lambda: route["distance"] <= old["route_distance_limit"], True),
    ]
    due = [c for c in geometry["comparators"].values() if frame * old["dt"] == c["hazard_time"]]
    checks.append(
        (
            "progress",
            lambda: all(route["rc"] >= c["rc"] - old["progress_slack"] for c in due),
            bool(due),
        )
    )
    for name, operation, applicable in checks:
        if applicable:
            predicates[name] = bool(operation())
            if not predicates[name]:
                return dict(route=route, predicates=predicates, background=None, reason=name), None
    result = query(state)
    background = summary(result)
    predicates["background"] = result.decision == "clear"
    reason = "clear" if predicates["background"] else "background_" + result.decision
    if reason == "clear":
        predicates["completion"] = route["rc"] >= 1
    packed = np.packbits(result.mask, bitorder="little").tobytes()
    return dict(route=route, predicates=predicates, background=background, reason=reason), packed


def replay(pair, arm, case, old, emit):
    history = pair[arm + "_prefix"]
    actions = [r["action"] for r in history[1:]] + pair["suffix"]
    state = case["geometry"]["reset"]
    query, rows = query_for(case), []
    for frame, action in enumerate([None, *actions]):
        before = state
        if frame:
            state = transition(before, action, old)
        if frame <= pair["frame"]:
            require(state == history[frame]["state"], "prefix_reproduction")
        assessed, mask = evaluate(before, state, action, frame, case, old, query)
        row = dict(frame=frame, action=action, state=state, **assessed)
        rows.append(row)
        emit(frame, mask)
        if assessed["reason"] != "clear":
            require(frame > pair["frame"], "invalid_prefix")
            break
        if assessed["predicates"]["completion"]:
            break
    stop = rows[-1]["reason"]
    if stop == "clear":
        stop = "model_complete" if rows[-1]["predicates"]["completion"] else "suffix_exhausted"
    return dict(pair=pair["id"], case=pair["case"], arm=arm, stop=stop, rows=rows)


def run(root, output, source):
    started = time.monotonic()
    plan = json.loads(read(root, BASE / "PLAN.json"))
    source_check(root, plan, source)
    require(git(root, "rev-parse", "HEAD").decode().strip() == source, "source_head")
    require(shutil.disk_usage(root).free >= plan["minimum_free_bytes"], "disk_budget")
    inputs = json.loads(read(root, BASE / "INPUTS.json"))
    validate_inputs(root, inputs)
    old = json.loads(read(root, OLD))
    cases = {c["id"]: c for c in json.loads(read(root, PREVIOUS / "CASES.json"))}
    output.mkdir(exist_ok=False)
    write(
        output / "initialized.json",
        dict(
            source_commit=source,
            plan_sha256=sha(encode(plan)),
            python=sys.version,
            numpy=np.__version__,
            platform=platform.platform(),
        ),
    )
    records = []
    try:
        for i, pair in enumerate(inputs["pairs"]):
            for arm in ("discarded", "representative"):
                folder = output / f"pair_{i}_{arm}"
                folder.mkdir()

                def emit(frame, mask):
                    require(
                        time.monotonic() - started < plan["producer_seconds"], "producer_deadline"
                    )
                    if mask is not None:
                        with (folder / f"mask_{frame:03d}.bin").open("xb") as stream:
                            stream.write(mask)

                trace = replay(pair, arm, cases[pair["case"]], old, emit)
                write(folder / "trace.json", trace)
                record = dict(
                    name=folder.name,
                    pair=pair["id"],
                    case=pair["case"],
                    arm=arm,
                    stop=trace["stop"],
                    states=len(trace["rows"]),
                )
                records.append(record)
                print(json.dumps(record), flush=True)
        total = sum(p.stat().st_size for p in output.rglob("*") if p.is_file())
        require(total < plan["max_output_bytes"] - 100000, "output_budget")
        require(rss() <= plan["max_rss_bytes"], "memory_budget")
        write(
            output / "execution.json",
            dict(
                status="completed",
                source_commit=source,
                plan_sha256=sha(encode(plan)),
                records=records,
                elapsed_seconds=time.monotonic() - started,
                peak_rss_bytes=rss(),
                raw_bytes_before_receipt=total,
                new_driving_episodes=0,
                provider_spend=0,
            ),
        )
    except Exception as exc:
        write(
            output / "failure.json",
            dict(status="invalid", error=str(exc), completed_records=len(records)),
        )
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--source", required=True)
    args = parser.parse_args()
    run(args.root.resolve(), args.output.resolve(), args.source)
