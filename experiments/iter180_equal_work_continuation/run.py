"""One preregistered paired continuation acquisition; no integrated planner run."""

import argparse
import copy
import json
from pathlib import Path
import time
from experiments.iter159_route_search_qualification.run import query_for
from experiments.iter158_constraint_aware_search.search import summary
from experiments.iter171_centered_shooting.runtime import identity
from experiments.iter179_frontier_continuation_audit.produce import Masks
from experiments.iter179_frontier_continuation_audit.probe import probe
from .common import BASE, OLD, read, require, write
from .contract import check_plan, schedule
from .records import initialize, finish, failure
from .retained import load
from .target import target_for
from .program import run_program


def run(root, source):
    started = time.monotonic()
    raw = root / BASE / "proof/study_raw"
    raw.parent.mkdir(exist_ok=True)
    plan = initialize(root, raw, source, "study")
    try:
        check_plan(plan)
        runtime = json.loads(read(root, BASE / "RUNTIME.json"))
        require(identity() == runtime, "runtime_identity")
        old = json.loads(read(root, OLD))
        case, _, paths = load(root, plan)
        vector = query_for(case)

        def query(state):
            return summary(vector(state))

        masks = Masks(raw / "masks", vector)
        for path in paths:
            require(path["masks"] == masks.path(path["trace"]), "retained_masks")
        write(raw / "paths.json", paths)
        records = []
        for index, (path, arm) in enumerate(schedule(paths)):
            last = path["trace"][-1]
            search_started = time.monotonic()
            target = target_for(
                last["state"], last["frame"], case["geometry"], plan["target_frame"]
            )
            deadline = search_started + plan["per_run_seconds"]
            if arm == "program":
                output = run_program(
                    last["state"],
                    last["frame"],
                    case["geometry"],
                    old,
                    plan,
                    query,
                    target,
                    deadline,
                )
                result, suffix, events = output["result"], output["trace"], output["events"]
                extra = {}
            else:
                result = probe(
                    last["state"], last["frame"], case["geometry"], old, plan, query, deadline
                )
                suffix, events = result.pop("trace"), result.pop("attempt_records")
                extra = dict(selected_attempt_ids=[r["id"] for r in suffix])
                require(result["attempts"] <= plan["maximum_beam_attempts"], "beam_work_bound")
            elapsed = time.monotonic() - search_started
            combined = copy.deepcopy(path["trace"] + suffix[1:])
            for i, row in enumerate(combined):
                row.update(id=i, parent=i - 1 if i else None)
            keys = masks.path(combined)
            rows = (
                [r for e in events if e["kind"] == "evaluation" for r in e["trace"]]
                if arm == "program"
                else events
            )
            for row in rows:
                if row["background"] is not None:
                    masks.add(row["state"], row["background"])
            folder = raw / f"run_{index:02}"
            folder.mkdir()
            write(folder / "events.json", events)
            write(folder / "trace.json", combined)
            records.append(
                dict(
                    index=index,
                    call=path["call"],
                    arm=arm,
                    target=target,
                    result=result,
                    masks=keys,
                    search_seconds=elapsed,
                    **extra,
                )
            )
            require(
                time.monotonic() - started < plan["study_producer_seconds"], "producer_deadline"
            )
        write(raw / "runs.json", records)
        masks.finish()
        require(identity() == runtime, "runtime_identity")
        attempts = sum(r["result"]["attempts"] for r in records)
        require(
            len(records) == 32 and attempts <= plan["maximum_total_attempts"], "comparison_scope"
        )
        finish(
            raw,
            source,
            plan,
            "study",
            started,
            new_motion_searches=32,
            new_integrated_schedules=0,
            diagnostic_attempts=attempts,
            distinct_masks=len(masks.rows),
        )
        print(
            json.dumps(dict(status="completed", attempts=attempts, distinct_masks=len(masks.rows))),
            flush=True,
        )
    except Exception as exc:
        failure(raw, started, exc)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source", required=True)
    args = parser.parse_args()
    run(args.root.resolve(), args.source)
