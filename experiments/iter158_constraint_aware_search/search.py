"""Heuristic command search with hard constraints; no completeness guarantee."""

import argparse
from collections import Counter
import math
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
from experiments.iter153_action_feasibility.planner import command, limits, reference, transition
from experiments.iter155_background_witness.storage import read_json
from experiments.iter156_background_calibration.background import (
    BackgroundPopulation,
    box_for_state,
)
from .common import BASE, encode, git, inputs, require, rss, sha, source_check, write
from .guidance import Guidance


def proposals(state, path, arc, old):
    choices = [[a, r * math.pi / 12] for a in (-2.0, 0.0, 2.0) for r in (-1, -0.5, 0, 0.5, 1)]
    choices += [command(state, path, arc, {"speed": v}, old) for v in (2.0, 4.0, 6.0)]
    return [list(a) for a in dict.fromkeys(tuple(a) for a in choices)]


def score(node):
    return (
        node["guide_distance"],
        -node["route"]["nearest"],
        node["route"]["distance"],
        abs(node["state"][4]),
        node["effort"],
        node["id"],
    )


def cell(state):
    x, y, heading, velocity, steering = state
    return (
        math.floor(x / 2),
        math.floor(y / 0.5),
        round(heading / 0.1),
        round(velocity / 0.5),
        round(steering / 0.065),
    )


def choose(rows, width):
    seen, result, groups = set(), [], {}
    for row in sorted(rows, key=score):
        key = cell(row["state"])
        if key not in seen:
            seen.add(key)
            groups.setdefault(round(row["state"][3]), []).append(row)
    # Preserve slower opportunities: immediate distance gain otherwise eliminates
    # early steering at lower speed before its later clearance can be observed.
    depth = 0
    while len(result) < width:
        layer = sorted([rows[depth] for rows in groups.values() if len(rows) > depth], key=score)
        if not layer:
            break
        result.extend(layer[: width - len(result)])
        depth += 1
    return result


def prior_reason(before, after, action, frame, geometry, old, boxes):
    outcome = route_outcome(after, geometry["route"])
    if not limits(after, action, old):
        return "controls", outcome
    if any(separation(ego_box(after, geometry["ego_dimensions"]), b) <= 0 for b in boxes):
        return "foreground", outcome
    if not sweep_clear(before, after, geometry["ego_dimensions"], boxes, old):
        return "foreground_sweep", outcome
    if outcome["distance"] > old["route_distance_limit"]:
        return "route_distance", outcome
    for comparator in geometry["comparators"].values():
        if frame * old["dt"] == comparator["hazard_time"]:
            if outcome["rc"] < comparator["rc"] - old["progress_slack"]:
                return "progress", outcome
    return None, outcome


def summary(query):
    return dict(
        count=query.count,
        certain_inside=query.certain_inside,
        possible_inside=query.possible_inside,
        decision=query.decision,
        mask_sha256=sha(np.packbits(query.mask, bitorder="little").tobytes()),
    )


def search(geometry, old, plan, query, emit, started):
    boxes = obstacles(geometry)
    guide = Guidance(geometry)
    spec = dict(speed=6.0, offset=0.0, start=0.0, length=10.0)
    path, arc = reference(geometry["route"], spec, old)
    reset = dict(
        id=0,
        parent=None,
        frame=0,
        action=None,
        state=geometry["reset"],
        route=route_outcome(geometry["reset"], geometry["route"]),
        effort=0.0,
    )
    reset["background"] = query(reset["state"])
    reset["guide_distance"] = guide.distance(reset["state"])
    initial_contact = any(
        separation(ego_box(reset["state"], geometry["ego_dimensions"]), b) <= 0 for b in boxes
    )
    reset["reason"] = "initial_foreground" if initial_contact else reset["background"]["decision"]
    emit("attempt", reset)
    counts, nodes, beam, best = Counter(), {0: reset}, [reset], reset
    queries, attempts, selected = 1, 0, None
    stop = "initial_rejected" if reset["reason"] != "clear" else "horizon"
    if stop == "initial_rejected":
        return dict(
            stop=stop,
            attempts=0,
            search_queries=queries,
            counts={},
            selected=None,
            trace=[reset],
            completed_depth=0,
        )
    completed_depth = 0
    for frame in range(1, old["max_actions"] + 1):
        survivors, interrupted = [], None
        for parent in beam:
            for action in proposals(parent["state"], path, arc, old):
                if (
                    time.monotonic() - started
                    >= plan["producer_seconds"] - plan["finalization_reserve_seconds"]
                ):
                    interrupted = "time_budget"
                    break
                if queries >= plan["maximum_search_queries"]:
                    interrupted = "query_budget"
                    break
                require(rss() <= plan["max_rss_bytes"], "memory_budget")
                attempts += 1
                after = transition(parent["state"], action, old)
                reason, outcome = prior_reason(
                    parent["state"], after, action, frame, geometry, old, boxes
                )
                q = None
                if reason is None:
                    q = query(after)
                    queries += 1
                    reason = q["decision"]
                row = dict(
                    id=attempts,
                    parent=parent["id"],
                    frame=frame,
                    action=action,
                    state=after,
                    route=outcome,
                    effort=parent["effort"] + sum(v * v for v in action),
                    background=q,
                    reason=reason,
                    guide_distance=guide.distance(after),
                )
                emit("attempt", row)
                counts[reason] += 1
                if reason == "clear":
                    nodes[row["id"]] = row
                    survivors.append(row)
            if interrupted:
                break
        if interrupted:
            stop = interrupted
            emit("depth", dict(frame=frame, complete=False, survivors=len(survivors), beam=[]))
            break
        completed_depth = frame
        complete = [row for row in survivors if row["route"]["rc"] >= 1]
        beam = choose(survivors, plan["beam_width"])
        emit(
            "depth",
            dict(
                frame=frame,
                complete=True,
                survivors=len(survivors),
                pruned=len(survivors) - len(beam),
                beam=[r["id"] for r in beam],
            ),
        )
        for row in survivors:
            if (-row["route"]["nearest"], row["frame"], score(row)) < (
                -best["route"]["nearest"],
                best["frame"],
                score(best),
            ):
                best = row
        if complete:
            selected = min(complete, key=score)
            stop = "model_complete"
            break
        if not beam:
            stop = "beam_empty"
            break
    trace, node = [], selected or best
    while node is not None:
        trace.append(node)
        node = nodes[node["parent"]] if node["parent"] is not None else None
    return dict(
        stop=stop,
        attempts=attempts,
        search_queries=queries,
        counts=dict(counts),
        selected=selected["id"] if selected else None,
        trace=list(reversed(trace)),
        completed_depth=completed_depth,
    )


def execute(root, output, source):
    plan = read_json(root / BASE / "PLAN.json")
    require(git(root, "rev-parse", "HEAD").decode().strip() == source, "source_head")
    source_check(root, plan, source)
    geometry, old, arrays = inputs(root, plan)
    require(shutil.disk_usage(root).free >= plan["minimum_free_bytes"], "disk_budget")
    points = arrays["selected_xyz"]
    require(len(points) == plan["selected_points"], "population")
    population = BackgroundPopulation(points, sha(points.tobytes()))
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    write(
        output / "initialized.json",
        dict(
            source_commit=source,
            plan_sha256=sha((root / BASE / "PLAN.json").read_bytes()),
            python=sys.version,
            numpy=np.__version__,
            platform=platform.platform(),
        ),
    )

    def query(state):
        box, _, _ = box_for_state(state, arrays["ground_poses"])
        return summary(population.query(box))

    try:
        with (
            (output / "attempts.jsonl").open("xb") as attempts,
            (output / "depths.jsonl").open("xb") as depths,
        ):

            def emit(kind, row):
                stream = attempts if kind == "attempt" else depths
                stream.write(encode(row))
                if kind == "depth":
                    stream.flush()
                    attempts.flush()
                    print(row["frame"], row["survivors"], len(row["beam"]), flush=True)
                require(
                    attempts.tell() + depths.tell() < plan["max_output_bytes"] - 20 * 1024**2,
                    "output_budget",
                )

            result = search(geometry, old, plan, query, emit, started)
        for row in result["trace"]:
            box, _, _ = box_for_state(row["state"], arrays["ground_poses"])
            q = population.query(box)
            require(summary(q) == row["background"], "trace_query_changed")
            with (output / f"mask_{row['frame']:03d}.bin").open("xb") as stream:
                stream.write(np.packbits(q.mask, bitorder="little").tobytes())
        write(output / "trace.json", result.pop("trace"))
        result.update(
            status="completed",
            source_commit=source,
            plan_sha256=sha((root / BASE / "PLAN.json").read_bytes()),
            population_sha256=population.sha256,
            elapsed_seconds=time.monotonic() - started,
            peak_rss_bytes=rss(),
            new_driving_episodes=0,
        )
        require(result["elapsed_seconds"] <= plan["producer_seconds"], "producer_deadline")
        require(result["peak_rss_bytes"] <= plan["max_rss_bytes"], "memory_budget")
        write(output / "execution.json", result)
        return result
    except Exception as exc:
        write(
            output / "failure.json",
            dict(
                status="invalid",
                error=f"{type(exc).__name__}:{exc}",
                elapsed_seconds=time.monotonic() - started,
            ),
        )
        raise


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True, type=Path)
    p.add_argument("--source", required=True)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    print(execute(args.root.resolve(), args.output.resolve(), args.source))
