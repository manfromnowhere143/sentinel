"""One frozen twelve-task schedule; compare against retained Iter168 evidence."""

import argparse
import json
from pathlib import Path
import time

from experiments.iter153_action_feasibility.geometry import route_outcome
from experiments.iter153_action_feasibility.planner import transition
from experiments.iter158_constraint_aware_search.search import summary
from experiments.iter159_route_search_qualification.run import query_for, retain_trace
from .common import BASE, OLD, encode, read, write
from .records import initialize, finish, failure
from .runtime import verify
from .shooting import search


def run(root, source):
    started = time.monotonic()
    output = root / BASE / "proof/search_raw"
    plan = initialize(root, output, source, "search")
    try:
        runtime = verify(root)
        write(output / "runtime.json", runtime)
        old = json.loads(read(root, OLD))
        cases = json.loads(read(root, "experiments/iter168_control_connector/CASES.json"))
        records = []
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
            folder = output / case["id"]
            folder.mkdir()
            with (
                (folder / "requests.jsonl").open("xb") as req,
                (folder / "evaluations.jsonl").open("xb") as ev,
            ):

                def emit(kind, row):
                    (req if kind == "request" else ev).write(encode(row))

                result = search(
                    case["geometry"],
                    case["task"],
                    old,
                    plan,
                    lambda state: summary(query(state)),
                    emit,
                )
            rows = result.pop("trace")
            retain_trace(folder / "selected", rows, query)
            result.update(case=case["id"], materialization_queries=len(rows))
            write(folder / "result.json", result)
            records.append(result)
            print(json.dumps(result), flush=True)
        verify(root)
        finish(output, source, plan, "search", started, records=records)
    except BaseException as exc:
        failure(output, started, exc)
        raise


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--source-commit", required=True)
    a = p.parse_args()
    run(a.root.resolve(), a.source_commit)
