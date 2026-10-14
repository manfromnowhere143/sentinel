"""One initialized execution; no retries, source-scene access or native runtime."""

import argparse
import json
from pathlib import Path
import time

from experiments.iter153_action_feasibility.geometry import route_outcome
from experiments.iter153_action_feasibility.planner import reference, transition
from experiments.iter158_constraint_aware_search.search import proposals as legacy, summary
from experiments.iter159_route_search_qualification.run import query_for, retain_trace
from .common import BASE, OLD, encode, read, write
from .connector import search
from .controls import proposals
from .records import failure, finish, initialize


def run(root, source):
    started = time.monotonic()
    output = root / BASE / "proof/search_raw"
    plan = initialize(root, output, source, "search")
    try:
        old = json.loads(read(root, OLD))
        cases = json.loads(read(root, BASE / "CASES.json"))
        path, arc = reference([[0, 0], [0, 20]], dict(offset=0, start=0, length=10), old)
        coverage = []
        for speed in plan["coverage_speeds"]:
            state = [0.0, 0.0, 0.0, speed, 0.0]
            coverage.append(
                dict(
                    speed=speed,
                    legacy=legacy(state, path, arc, old),
                    successor=[
                        dict(action=a, state=transition(state, a, old))
                        for a in proposals(state, path, arc, old)
                    ],
                )
            )
        write(output / "coverage.json", coverage)
        results = []
        for case in cases:
            query = query_for(case)
            state, rows = case["geometry"]["reset"], []
            for frame, action in enumerate([None, *case["witness_actions"]]):
                if action is not None:
                    state = transition(state, action, old)
                rows.append(
                    dict(
                        id=frame,
                        parent=frame - 1 if frame else None,
                        frame=frame,
                        action=action,
                        state=state,
                        route=route_outcome(state, case["geometry"]["route"]),
                        background=summary(query(state)),
                        reason="clear",
                    )
                )
            retain_trace(output / (case["id"] + "_witness"), rows, query)
            for depth in plan["lookaheads"]:
                name = case["id"] + "_depth" + str(depth)
                folder = output / name
                folder.mkdir()
                with (
                    (folder / "attempts.jsonl").open("xb") as a,
                    (folder / "calls.jsonl").open("xb") as c,
                ):

                    def emit(kind, row):
                        (a if kind == "attempt" else c).write(encode(row))

                    result = search(
                        case["geometry"],
                        case["task"],
                        old,
                        plan,
                        lambda s: summary(query(s)),
                        emit,
                        depth,
                    )
                rows = result.pop("trace")
                retain_trace(folder / "selected", rows, query)
                result.update(case=case["id"], depth=depth, materialization_queries=len(rows))
                write(folder / "result.json", result)
                results.append(result)
                print(json.dumps(result), flush=True)
        finish(output, source, plan, "search", started, records=results)
    except BaseException as exc:
        failure(output, started, exc)
        raise


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True, type=Path)
    p.add_argument("--source-commit", required=True)
    args = p.parse_args()
    run(args.root.resolve(), args.source_commit)
